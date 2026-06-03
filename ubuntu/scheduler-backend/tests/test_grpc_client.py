import sys
import os
import grpc

# Add the parent directory to sys.path so we can import the rpc module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rpc.generated import django_scheduler_pb2
from rpc.generated import django_scheduler_pb2_grpc

def test_submit_job():
    target = "localhost:50052"
    print(f"Connecting to Scheduler at {target}...")
    
    # Open an insecure channel to the gRPC server
    with grpc.insecure_channel(target) as channel:
        stub = django_scheduler_pb2_grpc.SchedulerServiceStub(channel)
        
        # Create the request payload based on the .proto definition
        request = django_scheduler_pb2.SubmitJobRequest(
            uid="testuid",
            username="ta1",
            total_pages=15,
            file_path="/tmp/dummy.pdf"
        )
        
        print("Sending SubmitPrintJob request...")
        try:
            response = stub.SubmitPrintJob(request, timeout=5)
            print("--- Response Received ---")
            print(f"Success: {response.success}")
            print(f"Message: {response.message}")
            print(f"Job ID : {response.job_id}")
        except grpc.RpcError as e:
            print(f"gRPC call failed: {e.code()} - {e.details()}")

if __name__ == "__main__":
    test_submit_job()
