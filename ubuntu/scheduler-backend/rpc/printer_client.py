import os
from typing import TypedDict
import grpc

class JobResponse(TypedDict):
    success: bool
    message: str
    job_id: str

from .generated import scheduler_windows_pb2 as pb2
from .generated import scheduler_windows_pb2_grpc as pb2_grpc

MAX_MESSAGE_SIZE = 1024 * 1024 * 512  # 512 MB

class PrinterClient:
    def __init__(self, target_ip="172.16.127.106", port="50051"):
        self.target = f"{target_ip}:{port}"
        self.send_print_job_options = [
            ("grpc.max_send_message_length", MAX_MESSAGE_SIZE),
            ("grpc.max_receive_message_length", MAX_MESSAGE_SIZE),
        ]

    def send_print_job(
        self,
        user_id: str,
        file_content: bytes,
        is_duplex: bool = True,
    ) -> JobResponse:
        """
        [API] Called to execute a print job
        """
        try:
            with grpc.insecure_channel(
                self.target, self.send_print_job_options
            ) as channel:
                stub = pb2_grpc.PrinterBridgeStub(channel)

                request = pb2.PrintRequest(
                    file_content=file_content,
                    user_id=user_id,
                    is_duplex=is_duplex, 
                )

                response = stub.ExecutePrintJob(request, timeout=420)

                return {
                    "success": response.success,
                    "message": response.message,
                    "job_id": response.job_id,
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Bridge Error: {str(e)}",
                "job_id": "",
            }

    def get_job_status(self, job_id_str: str):
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = pb2_grpc.PrinterBridgeStub(channel)
                request = pb2.StatusRequest(job_id=job_id_str)
                response = stub.GetJobStatus(request, timeout=10)

                return {
                    "job_id": str(response.job_id),
                    "total_pages": str(response.total_pages),
                    "submit_time": str(response.submit_time),
                    "state": str(response.state),
                    "error_message": "",
                }
        except Exception as e:
            return {
                "job_id": job_id_str,
                "total_pages": "0",
                "submit_time": "",
                "state": "error",
                "error_message": str(e),
            }

    def get_all_jobs(self):
        try:
            with grpc.insecure_channel(self.target) as channel:
                stub = pb2_grpc.PrinterBridgeStub(channel)
                response = stub.GetAllJobs(pb2.Empty())

                jobs_list = []
                for job in response.jobs:
                    jobs_list.append(
                        {
                            "job_id": job.job_id,
                            "state": job.state,
                            "submit_time": job.submit_time,
                        }
                    )
                return jobs_list
        except Exception as e:
            return []

# use local IP for testing
windows_client = PrinterClient(target_ip="127.0.0.1", port="50051")
