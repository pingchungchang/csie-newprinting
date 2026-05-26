import logging
import threading

logger = logging.getLogger(__name__)

# --- Mock Database ---
# Using a lock to prevent race conditions between the gRPC server threads 
# writing data and the worker thread reading data.
db_lock = threading.Lock()
mock_table = {}
current_id = 1

def create_submission(uid, username, file_pages):
    global current_id
    with db_lock:
        job_id = current_id
        mock_table[job_id] = {
            "id": job_id,
            "uid": uid,
            "username": username,
            "pages": file_pages,
            "status": "pending",
            "retry_count": 0
        }
        current_id += 1
        logger.info(f"[DB Mock] Created job {job_id} for user {username}")
        return job_id

def get_pending_jobs():
    pending_jobs = []
    with db_lock:
        for job_id, job_data in mock_table.items():
            if job_data["status"] == "pending":
                # Simulate "SELECT FOR UPDATE" and immediate state change
                job_data["status"] = "processing"
                pending_jobs.append(job_data.copy())
    return pending_jobs

def update_job_status(job_id, status, wid=None, retry_increment=False):
    with db_lock:
        if job_id in mock_table:
            mock_table[job_id]["status"] = status
            if wid:
                mock_table[job_id]["wid"] = wid
            if retry_increment:
                mock_table[job_id]["retry_count"] += 1
            logger.info(f"[DB Mock] Updated job {job_id} status to {status}")
