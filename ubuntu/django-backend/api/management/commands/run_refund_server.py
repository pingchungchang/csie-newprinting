import logging
from concurrent import futures
import grpc
from django.core.management.base import BaseCommand

from api.newprinting_grpc.generated import django_scheduler_pb2
from api.newprinting_grpc.generated import django_scheduler_pb2_grpc
from api.newprinting_db.submission.crud import mark_submission_refunded
from django.db import transaction, connection

logger = logging.getLogger(__name__)

class DjangoRefundServicer(django_scheduler_pb2_grpc.DjangoServiceServicer):
    def RefundJob(self, request, context):
        uid = request.uid
        reason = request.reason
        logger.info(f"Received refund request for UID {uid}. Reason: {reason}")
        
        try:
            # Use transaction to ensure data integrity
            with transaction.atomic():
                # 1. Look up the submission to get the user and money amount
                with connection.cursor() as cursor:
                    cursor.execute("SELECT username, money FROM np_submission WHERE uid = %s FOR UPDATE;", [uid])
                    row = cursor.fetchone()
                    
                    if not row:
                        return django_scheduler_pb2.RefundResponse(success=False, message="Submission not found")
                    
                    username, money, status = row[0], row[1], row[2]
                    if status == 'refunded':
                        return django_scheduler_pb2.RefundResponse(success=False, message="Submission already refunded")

                # 2. Add balance back
                # use SQL atomic update to avoid race condition
                cursor.execute("UPDATE np_balance SET balance = balance + %s WHERE username = %s;", [money, username])
                
                # 3. Update submission status
                mark_submission_refunded(uid, reason)

            return django_scheduler_pb2.RefundResponse(
                success=True, 
                message=f"Refunded {money} to {username}"
            )
            
        except Exception as e:
            logger.error(f"Refund failed for UID {uid}: {e}")
            return django_scheduler_pb2.RefundResponse(success=False, message=str(e))

class Command(BaseCommand):
    help = 'Starts the gRPC Refund Server'

    def handle(self, *args, **options):
        port = "50053"
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        django_scheduler_pb2_grpc.add_DjangoServiceServicer_to_server(
            DjangoRefundServicer(), server
        )
        server.add_insecure_port(f'[::]:{port}')
        server.start()
        self.stdout.write(self.style.SUCCESS(f"Django gRPC Refund Server listening on port {port}..."))
        server.wait_for_termination()
