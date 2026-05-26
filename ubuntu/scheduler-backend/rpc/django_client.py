import logging
import grpc

from .generated import django_scheduler_pb2 as pb2
from .generated import django_scheduler_pb2_grpc as pb2_grpc

logger = logging.getLogger(__name__)

class DjangoRefundClient:
    def __init__(self, target_ip="127.0.0.1", port="50053"):
        self.target = f"{target_ip}:{port}"

    def request_refund(self, uid: int, reason: str) -> bool:
        """
        Send refund request to Django
        """
        logger.info(f"[Refund] Requesting refund for UID: {uid}...")
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = pb2_grpc.DjangoServiceStub(channel)
                
                # Updated to match the new RefundRequest protobuf definition
                request = pb2.RefundRequest(
                    uid=uid,
                    reason=reason
                )
                
                response = stub.RefundJob(request, timeout=10)
                
                if response.success:
                    logger.info(f"[Refund] Successfully refunded UID {uid}. Msg: {response.message}")
                    return True
                else:
                    logger.error(f"[Refund] Django rejected refund for UID {uid}. Msg: {response.message}")
                    return False
                    
        except grpc.RpcError as e:
            logger.error(f"[Refund] gRPC Connection Error to Django: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"[Refund] Unexpected Error: {str(e)}")
            return False

django_client = DjangoRefundClient()
