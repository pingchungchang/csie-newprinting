import grpc
from concurrent import futures
import time
import print_pb2
import print_pb2_grpc
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from printer_scripts import PrinterUtils

# 1. Load RSA Private Key
try:
    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
    print("[SUCCESS] RSA Private Key loaded successfully.")
except Exception as e:
    print(f"[ERROR] Failed to load private key: {e}")

class PrinterServicer(print_pb2_grpc.PrinterBridgeServicer):
    def ExecutePrintJob(self, request, context):
        print(f"\n[RECEIVED] Request from User: {request.user_id}")
        
        try:
            # 2. RSA Decryption (OAEP + SHA256)
            # Encoding as latin1 to handle binary data within the string
            # encrypted_data = request.encrypted_password.encode('latin1')
            encrypted_data = request.encrypted_password
            
            decrypted_password = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode('utf-8')

            print(f"[SUCCESS] Password decrypted: {decrypted_password}")
            print(f"[INFO] Settings: {'Duplex' if request.is_duplex else 'Simplex'}")
            print(f"[INFO] File size: {len(request.file_content)} bytes")

            succ, job_id = PrinterUtils.submit_print_job_bytes(request.user_id, decrypted_password, request.file_content, request.is_duplex)
            # succ, job_id = PrinterUtils.submit_print_job()

            # Logic for Printer Driver integration goes here
            return print_pb2.PrintResponse(
                success=succ, 
                message=f"succeeded, job ID = {job_id}",
		job_id=str(job_id)
            )

        except Exception as e:
            print(f"[ERROR] Decryption failed: {e}")
            return print_pb2.PrintResponse(
                success=False, 
                message=f"Windows Server Error: {str(e)}"
		job_id="ERROR"
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    print_pb2_grpc.add_PrinterBridgeServicer_to_server(PrinterServicer(), server)
    
    # Listen on all interfaces at Port 50051
    server.add_insecure_port('[::]:50051')
    print("gRPC Server is running... Listening on [::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
