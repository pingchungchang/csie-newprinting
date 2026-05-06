import grpc
from concurrent import futures
import time
import uuid
import print_pb2
import print_pb2_grpc
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# Notice: We DO NOT import PrinterUtils here. 
# This guarantees 100% safety from accidental physical printing.

MAX_MESSAGE_LENGTH = 1024 * 1024 * 512 # 512 MB

# 1. load RSA private key
try:
    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
except FileNotFoundError:
    print("[WARNING] private_key.pem not found. Please ensure it exists for RSA decryption testing.")
    private_key = None

class MockPrinterServicer(print_pb2_grpc.PrinterBridgeServicer):

    def ExecutePrintJob(self, request, context):
        print(f"[TEST RECV] Print request for {request.user_id} ({len(request.file_content)} bytes)")
        try:
            # decoding (kept to simulate realistic CPU load during tests)
            if private_key:
                decrypted_password = private_key.decrypt(
                    request.encrypted_password,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode('utf-8')

            # simulate a tiny bit of disk/processing delay
            time.sleep(0.05) 
            
            # generate a fake job_id
            fake_job_id = str(uuid.uuid4().int)[:6]
            
            return print_pb2.PrintResponse(
                success=True,
                message="[TEST] Windows mock job submitted successfully",
                job_id=fake_job_id
            )
        except Exception as e:
            print(f"[TEST] ExecutePrintJob Error: {e}")
            return print_pb2.PrintResponse(success=False, message=str(e), job_id="0")

    def GetJobStatus(self, request, context):
        print(f"[TEST QUERY] Job ID: {request.job_id}")
        return print_pb2.StatusResponse(
            job_id=str(request.job_id),
            total_pages=1,
            submit_time="2026-05-04 12:00:00",
            state="Finished (Test Mode)"
        )

    def GetAllJobs(self, request, context):
        print("[TEST LIST] Fetching all jobs")
        response = print_pb2.JobListResponse()
        response.jobs.append(print_pb2.StatusResponse(
            job_id="999",
            state="Finished (Test Mode)"
        ))
        return response

def serve_test():
    # increased max_workers to 30 to prevent Windows thread bottleneck during concurrent testing
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=30), options = [
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
        ])
    
    print_pb2_grpc.add_PrinterBridgeServicer_to_server(MockPrinterServicer(), server)
    server.add_insecure_port('[::]:50051')
    
    print("="*50)
    print("WARNING: STARTING IN TEST MODE")
    print("Physical printer is disabled. Safe for load testing.")
    print("Windows gRPC Test Server is running on port 50051...")
    print("="*50)
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve_test()
