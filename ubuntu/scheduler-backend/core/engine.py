import threading
import logging
import time
import os
from db import crud
from rpc.printer_client import windows_client
from rpc.django_client import django_client

logger = logging.getLogger(__name__)

# Shared directory path for file transfer between Django and Scheduler
SHARED_DIR = os.environ.get("SHARED_PRINT_DIR", "/tmp/shared_printing")

class SchedulerEngine:
    def __init__(self):
        self.condition = threading.Condition()
        self.running = True
        self.next_wakeup_timeout = 300.0
        self.thread = threading.Thread(target=self._run, daemon=True)
        
        # In-memory dictionary to track when a failed job can be retried
        # Key: uid, Value: timestamp (time.time() + retry_delay)
        self.retry_backoff = {}

    def start(self):
        self.thread.start()
        logger.info("Scheduler Engine started. Waiting for jobs...")

    def notify_new_job(self):
        with self.condition:
            logger.info("Received gRPC notification. Waking up worker.")
            # Wake up immediately when Django sends a new job
            self.condition.notify()

    def _run(self):
        self._process_jobs()
        
        while self.running:
            with self.condition:
                self.condition.wait(timeout=self.next_wakeup_timeout)
                # Reset timeout to standard 300s after waking up
                self.next_wakeup_timeout = 30.0 # TIMEOUT_INTERVAL

            if not self.running:
                break
                
            logger.info("Worker awake. Checking DB for pending jobs...")
            self._process_jobs()

    def _process_jobs(self):
        try:
            jobs = crud.get_pending_jobs()
            if not jobs:
                return

            current_time = time.time()

            for job in jobs:
                uid = job['uid']
                username = job['username']
                
                # Check in-memory backoff to prevent spamming retries
                if uid in self.retry_backoff and current_time < self.retry_backoff[uid]:
                    # Job is not ready for retry yet, revert status back to pending
                    logger.debug(f"[UID {uid}] Skipping retry. Waiting for backoff period.")
                    crud.update_job_status(uid, status="pending")
                    continue

                logger.info(f"[UID {uid}] Processing print job for user {username}...")
                
                # Deduce file path using UID convention
                file_path = os.path.join(SHARED_DIR, f"{uid}.pdf")
                
                if not os.path.exists(file_path):
                    logger.error(f"[UID {uid}] File not found at {file_path}. Marking as failed.")
                    self._handle_total_failure(uid, "File not found on disk")
                    continue

                # Read file content to send via Windows RPC
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                except IOError as e:
                    logger.error(f"[UID {uid}] Failed to read file: {e}")
                    self._handle_retry(uid, job['retry_count'])
                    continue

                # Send to Windows Server
                """
                result = windows_client.send_print_job(
                    user_id=uid, 
                    file_content=file_content,
                    is_duplex=True
                )
                """                
                # testing success -> print mock response
                logger.info(f"[TEST MODE] Mocking Windows RPC for UID {uid}")
                result = {"success": True, "job_id": 9999}
                """

                # testing fail -> success: False
                logger.warning(f"[TEST MODE] Mocking Windows RPC FAILURE for UID {uid}")
                result = {"success": False, "message": "Windows Server Connection Timeout"}
                """
                if result["success"]:
                    wid = result["job_id"]
                    logger.info(f"[UID {uid}] Successfully sent to Windows. WID: {wid}")
                    crud.update_job_status(uid, status="success", wid=wid)
                    self._cleanup_job(uid, file_path)
                else:
                    logger.warning(f"[UID {uid}] Failed to send to Windows. Error: {result['message']}")
                    self._handle_retry(uid, job['retry_count'], file_path)
                    
        except Exception as e:
            logger.error(f"Error processing jobs: {e}")

    def _handle_retry(self, uid, current_retries, file_path=None):
        """Handles logic when a Windows RPC call fails and decides whether to retry or fail permanently."""
        if current_retries < 3:
            logger.info(f"[UID {uid}] Retrying later (Current retries: {current_retries})")
            crud.update_job_status(uid, status="pending", retry_increment=True)
            
            # Set backoff time to 5 seconds from now
            self.retry_backoff[uid] = time.time() + 5.0
            # Ensure the worker wakes up in 5 seconds if not woken up earlier
            self.next_wakeup_timeout = min(self.next_wakeup_timeout, 5.0)
        else:
            logger.error(f"[UID {uid}] Exceeded max retries. Marking as failed.")
            self._handle_total_failure(uid, "Windows Server Error / Max retries exceeded")
            if file_path:
                self._cleanup_job(uid, file_path)

    def _handle_total_failure(self, uid, reason):
        """Marks job as failed and attempts to refund via Django."""
        crud.update_job_status(uid, status="failed")
        
        # Call Django client for refund
        refund_success = django_client.request_refund(
            uid=uid,
            reason=reason
        )

        if not refund_success:
            logger.critical(f"[ALERT] Failed to process refund for UID {uid}!")
            # Note: The job status is 'failed', admin can query DB for failed jobs to manual refund
            
        # Clear backoff tracking if it exists
        self.retry_backoff.pop(uid, None)

    def _cleanup_job(self, uid, file_path):
        """Removes the file from disk and clears in-memory state."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[UID {uid}] Cleaned up file: {file_path}")
        except OSError as e:
            logger.error(f"[UID {uid}] Failed to delete file {file_path}: {e}")
            
        self.retry_backoff.pop(uid, None)
