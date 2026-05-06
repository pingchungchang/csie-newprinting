# python import example
from api.newprinting_grpc.bridge.printer_client import PrinterClient

# init client
client = PrinterClient(target_ip="172.16.127.106")  # windows IP

# ----- api list -----
# 1. send user info and to-print content (in bytes) to windows server
def send_print_job(user_id: str, raw_password: str, file_content: bytes, is_duplex: bool)

return format:
{
    "success": True,
    "message": "Windows job submitted",
    "job_id": "24"      # note: in string
}

# 2. query single job status
def get_job_status(job_id_str: str)

return format:
{
    "job_id": "24",     # note: in string
    "total_pages": 1,
    "submit_time": "2026-04-16 05:48:30",
    "state": "In Queue" # state options: In Queue, Printing, Finished, Error
}

# 3. get all printer jobs
def get_all_jobs()

return format:
[
    {"job_id": "24", "state": "Finished"},
    {"job_id": "25", "state": "In Queue"}
]
