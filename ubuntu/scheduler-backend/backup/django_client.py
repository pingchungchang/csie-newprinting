import logging
import grpc

from .generated import django_scheduler_pb2 as pb2
from .generated import django_scheduler_pb2_grpc as pb2_grpc

logger = logging.getLogger(__name__)

class DjangoRefundClient:
    def __init__(self, target_ip="127.0.0.1", port="50053"):
        # django's gRPC refund service at 50053 port
        self.target = f"{target_ip}:{port}"

    def request_refund(self, uid: str, job_id: int, reason: str) -> bool:
        """
        send refund request to django
        """
        logger.info(f"[Refund] Requesting refund for user {uid}, Job ID: {job_id}...")
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = pb2_grpc.DjangoServiceStub(channel)
                
                request = pb2.RefundRequest(
                    uid=uid,
                    job_id=job_id,
                    reason=reason
                )
                
                # timeout avoid dies at django
                response = stub.RefundJob(request, timeout=10)
                
                if response.success:
                    logger.info(f"[Refund] Successfully refunded Job {job_id}. Msg: {response.message}")
                    return True
                else:
                    logger.error(f"[Refund] Django rejected refund for Job {job_id}. Msg: {response.message}")
                    return False
                    
        except grpc.RpcError as e:
            logger.error(f"[Refund] gRPC Connection Error to Django: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"[Refund] Unexpected Error: {str(e)}")
            return False

django_client = DjangoRefundClient()
