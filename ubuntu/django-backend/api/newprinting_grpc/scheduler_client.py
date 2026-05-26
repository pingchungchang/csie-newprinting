import logging
import grpc
from .generated import django_scheduler_pb2 as pb2
from .generated import django_scheduler_pb2_grpc as pb2_grpc

logger = logging.getLogger(__name__)

class SchedulerClient:
    def __init__(self, target_ip="127.0.0.1", port="50052"):
        self.target = f"{target_ip}:{port}"

    def submit_job(self, uid: int, username: str, total_pages: int) -> bool:
        """
        Notify Scheduler that a new print job is ready on disk.
        """
        logger.info(f"Notifying Scheduler for UID: {uid}")
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = pb2_grpc.SchedulerServiceStub(channel)
                request = pb2.SubmitJobRequest(
                    uid=uid,
                    username=username,
                    total_pages=total_pages,
                    file_path="" # We rely on {uid}.pdf convention now
                )
                response = stub.SubmitPrintJob(request, timeout=5)
                if response.success:
                    return True
                else:
                    logger.error(f"Scheduler rejected job {uid}: {response.message}")
                    return False
        except grpc.RpcError as e:
            logger.error(f"gRPC Error connecting to Scheduler: {e.code()} - {e.details()}")
            return False
