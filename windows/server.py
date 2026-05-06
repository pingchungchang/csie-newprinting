import grpc
from concurrent import futures
import time
import print_pb2
import print_pb2_grpc
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# import windows printer utils
from printer_scripts import PrinterUtils

MAX_MESSAGE_LENGTH = 1024 * 1024 * 512 # 512 MB

# 1. load RSA private key
with open("private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(key_file.read(), password=None)

class PrinterServicer(print_pb2_grpc.PrinterBridgeServicer):
    
    def ExecutePrintJob(self, request, context):
        print(f"[RECV] Print request for {request.user_id}")
        try:
            # decoding
            decrypted_password = private_key.decrypt(
                request.encrypted_password,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode('utf-8')

            # call printer util api
            # (success: bool, job_id: int)
            print('[server.py] sending print job to PrinterUtils')
            success, job_id = PrinterUtils.submit_print_job_bytes(
                request.user_id, 
                decrypted_password, 
                request.file_content, 
                request.is_duplex
            )

            # return to ubuntu (job_id cast to string)
            return print_pb2.PrintResponse(
                success=success,
                message="Windows job submitted",
                job_id=str(job_id) 
            )
        except Exception as e:
            print(f"ExecutePrintJob Error: {e}")
            return print_pb2.PrintResponse(success=False, message=str(e), job_id="0")

    def GetJobStatus(self, request, context):
        print(f"[QUERY] Job ID: {request.job_id}")
        try:
            # cast to int and calls get_printer_job_by_id()
            target_id = int(request.job_id)
            job_info = PrinterUtils.get_printer_job_by_id(job_id=target_id)
            
            # print(f"[DEBUG] Raw Job Data: {job_info}")  # for debug

            # syntax alignment
            return print_pb2.StatusResponse(
                job_id=str(job_info.job_id),
                total_pages=int(job_info.total_pages),
                submit_time=str(job_info.submit_time),
                state=str(job_info.status)
            )
        except Exception as e:
            print(f"GetJobStatus Error: {e}")
            return print_pb2.StatusResponse(state=f"Error: {str(e)}")

    def GetAllJobs(self, request, context):
        print("[LIST] Fetching all jobs")
        try:
            # call get_printer_jobs()
            all_jobs = PrinterUtils.get_printer_jobs()
            response = print_pb2.JobListResponse()
            for job in all_jobs:
                id_str = str(job.job_id) if hasattr(job, 'job_id') else str(job.get('JobId', 'unknown'))
                status_str = str(job.status) if hasattr(job, 'status') else str(job.get('Status', 'unknown'))
                
                response.jobs.append(print_pb2.StatusResponse(
                    job_id=id_str,
                    state=status_str
                ))
            return response
        except Exception as e:
            print(f"GetAllJobs Error: {e}")
            return print_pb2.JobListResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options = [
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
        ])
    print_pb2_grpc.add_PrinterBridgeServicer_to_server(PrinterServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Windows gRPC Server is running on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
