import grpc
import logging
from concurrent import futures
from .generated import django_scheduler_pb2
from .generated import django_scheduler_pb2_grpc
from db import crud

logger = logging.getLogger(__name__)

class SchedulerServicer(django_scheduler_pb2_grpc.SchedulerServiceServicer):
    def __init__(self, engine):
        self.engine = engine

    def SubmitPrintJob(self, request, context):
        """SubmitPrintJob"""
        logger.info(f"Received SubmitPrintJob for {request.username} (uid: {request.uid})")
        try:
            # 1. update DB (default status: pending)
            job_id = crud.create_submission(
                uid=request.uid,
                username=request.username,
                file_pages=request.total_pages
            )

            # 2. wake up sleeping worker thread
            self.engine.notify_new_job()

            return django_scheduler_pb2.SubmitJobResponse(
                success=True,
                message="Job submitted to Scheduler successfully.",
                job_id=job_id
            )
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            return django_scheduler_pb2.SubmitJobResponse(
                success=False,
                message=str(e),
                job_id=-1
            )

def serve(engine, port="50052"):
    """run gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    django_scheduler_pb2_grpc.add_SchedulerServiceServicer_to_server(
        SchedulerServicer(engine), server
    )
    # listening on port 50052
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Scheduler gRPC Server listening on port {port}")
    server.wait_for_termination()
