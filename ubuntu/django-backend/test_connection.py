import os
import sys

# 1. get working dir `api/` (django structure)
sys.path.append(os.getcwd())

from api.newprinting_grpc.bridge.printer_client import PrinterClient

def run_test():
    WINDOWS_IP = "172.16.127.106" 
    
    print(f"--- Starting Connection Test to {WINDOWS_IP} ---")
    
    # client init
    try:
        client = PrinterClient(target_ip=WINDOWS_IP)
        print("[Step 1] PrinterClient Initialized.")
    except Exception as e:
        print(f"[Step 1] Initialization Failed: {e}")
        return

    # single print job
    print("\n[Step 2] Testing: ExecutePrintJob...")
    test_file_content = b"This is a test PDF content from Ubuntu."
    
    # info
    result = client.send_print_job(
        user_id="ta1", 
        raw_password="ta1", 
        file_content=test_file_content,
        is_duplex=True
    )

    if result["success"]:
        print(f"[Step 2] Success! Received Job ID: {result['job_id']} (Type: {type(result['job_id'])})")
        
        # query status
        print("\n[Step 3] Testing: GetJobStatus...")
        status = client.get_job_status(result["job_id"])
        print(f"[Step 3] Status Result: {status}")
    else:
        print(f"[Step 2] Failed: {result['message']}")

    # get all job list
    print("\n[Step 4] Testing: GetAllJobs...")
    all_jobs = client.get_all_jobs()
    print(f"[Step 4] Found {len(all_jobs)} jobs in list.")

if __name__ == "__main__":
    run_test()
