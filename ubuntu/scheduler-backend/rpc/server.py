import grpc
import logging
from concurrent import futures
from .generated import django_scheduler_pb2
from .generated import django_scheduler_pb2_grpc
# Removed crud import because Django already creates the DB submission skeleton

logger = logging.getLogger(__name__)

class SchedulerServicer(django_scheduler_pb2_grpc.SchedulerServiceServicer):
    def __init__(self, engine):
        self.engine = engine

    def SubmitPrintJob(self, request, context):
        """SubmitPrintJob"""
        logger.info(f"Received SubmitPrintJob for {request.username} (uid: {request.uid})")
        try:
            # Django has already written to the DB and renamed the file to {uid}.pdf.
            # We only need to wake up the engine's worker thread.
            self.engine.notify_new_job()

            return django_scheduler_pb2.SubmitJobResponse(
                success=True,
                message="Job notification received by Scheduler.",
                uid=request.uid
            )
        except Exception as e:
            logger.error(f"Error waking up engine: {e}")
            return django_scheduler_pb2.SubmitJobResponse(
                success=False,
                message=str(e),
                uid=request.uid
            )

def serve(engine, port="50052"):
    """run gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    django_scheduler_pb2_grpc.add_SchedulerServiceServicer_to_server(
        SchedulerServicer(engine), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Scheduler gRPC Server listening on port {port}")
    server.wait_for_termination()
