import time
import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.newprinting_grpc.bridge.printer_client import PrinterClient

# --- Load Test Configuration ---
# Number of concurrent connections (adjust upward from 10 or 20 to test limits)
CONCURRENT_WORKERS = 20      
# Total number of print requests to dispatch
TOTAL_REQUESTS = 100         
# Path to the 5MB dummy file generated for testing
DUMMY_FILE = "dummy_5m.pdf"  
# Target file for benchmarking results
OUTPUT_CSV = "grpc_baseline_results.csv"

# Initialize the gRPC Client
client = PrinterClient(target_ip="172.16.127.106", port="50051")

# Pre-load the file into memory to prevent local Disk I/O from bottlenecking the network test
print(f"Loading {DUMMY_FILE} into memory...")
with open(DUMMY_FILE, "rb") as f:
    file_payload = f.read()

def single_grpc_request(req_id):
    """Executes a single gRPC transmission and records timing metrics."""
    start_time = time.time()
    try:
        # Call the gRPC API
        # The password parameter is handled via RSA public key encryption within the client
        response = client.send_print_job(
            user_id=f"test_user_{req_id}",
            raw_password="dummy_password",
            file_content=file_payload,
            is_duplex=True
        )
        end_time = time.time()
        latency = end_time - start_time
        
        # Return metric tuple: ID, Start, End, Latency, Success status, Message
        return (
            req_id, 
            start_time, 
            end_time, 
            latency, 
            response.get("success", False), 
            response.get("message", "")
        )
    except Exception as e:
        end_time = time.time()
        return (req_id, start_time, end_time, end_time - start_time, False, str(e))

def main():
    print(f"Starting gRPC Load Test: {TOTAL_REQUESTS} requests with {CONCURRENT_WORKERS} workers...")
    results = []
    
    test_start = time.time()
    
    # Use ThreadPool to generate concurrent requests
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        # Submit tasks to the thread pool
        futures = {executor.submit(single_grpc_request, i): i for i in range(TOTAL_REQUESTS)}
        
        # Collect results as they complete
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            status = "SUCCESS" if res[4] else "FAILED"
            print(f"[Req {res[0]:03d}] {status} - Latency: {res[3]:.2f}s - Msg: {res[5][:30]}")

    test_end = time.time()
    
    # Persist results to CSV
    with open(OUTPUT_CSV, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Req_ID", "Start_Time", "End_Time", "Latency_sec", "Success", "Message"])
        writer.writerows(results)

    # Basic statistics calculation
    success_count = sum(1 for r in results if r[4])
    total_time = test_end - test_start
    throughput = TOTAL_REQUESTS / total_time
    
    print("\n" + "="*40)
    print("Test Completed!")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Throughput: {throughput:.2f} requests/second")
    print(f"Success Rate: {success_count}/{TOTAL_REQUESTS} ({(success_count/TOTAL_REQUESTS)*100:.1f}%)")
    print("="*40)
    print(f"Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
