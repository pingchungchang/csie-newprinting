import threading
import logging
import time
from db import crud
from rpc.printer_client import windows_client
from rpc.django_client import django_client

logger = logging.getLogger(__name__)

class SchedulerEngine:
    def __init__(self):
        self.condition = threading.Condition()
        self.running = True
        # maintain variable for timeout avoid race condition
        self.next_wakeup_timeout = 300.0
        # single worker thread
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        logger.info("Scheduler Engine started. Waiting for jobs...")

    def notify_new_job(self):
        """interface for gRPC server to call"""
        with self.condition:
            logger.info("Received notification. Waking up worker.")
            self.condition.notify()

    def _run(self):
        # scan DB when scheduler init, handle any orphan pending submission
        self._process_jobs()
        
        while self.running:
            with self.condition:
                # worker wakes up to poll db with timeout=300s
                # avoid pending orphan submissions
                self.condition.wait(timeout=self.next_wakeup_timeout)
                self.next_wakeup_timeout = 300.0

            if not self.running:
                break
                
            logger.info("Worker awake. Checking DB for pending jobs...")
            self._process_jobs()

    def _process_jobs(self):
        """handle pending jobs from DB"""
        try:
            jobs = crud.get_pending_jobs()
            if not jobs:
                return

            for job in jobs:
                uid = job['uid']
                username = job['username']
                
                logger.info(f"[UID {uid}] Processing print job for user {username}...")

                # TODO: dummy file content for testing
                dummy_file_content = b"%PDF-1.4 dummy content"

                # calls windows_client.send_print_job() to windows server
                result = windows_client.send_print_job(
                    user_id=job['uid'], 
                    file_content=dummy_file_content,
                    is_duplex=True
                )

                if result["success"]:
                    wid = result["job_id"]
                    logger.info(f"[Job {job_id}] Successfully sent to Windows. WID: {result['job_id']}")
                    crud.update_job_status(job_id, status="success", wid=result["job_id"])
                else:
                    logger.warning(f"[Job {job_id}] Failed to send to Windows. Error: {result['message']}")

                    # retry method
                    if job['retry_count'] < 3:
                        logger.info(f"[Job {job_id}] Retrying later (Current retries: {job['retry_count']})")
                        crud.update_job_status(job_id, status="pending", retry_increment=True)

                        # retry in 5s
                        self.next_wakeup_timeout = min(self.next_wakeup_timeout, 5.0)
                    else:
                        logger.error(f"[Job {job_id}] Exceeded max retries. Marking as failed.")
                        crud.update_job_status(job_id, status="failed")
                        
                        # calls django_client's refund
                        refund_success = django_client.request_refund(
                            uid=job['uid'],
                            job_id=job_id,
                            reason="Windows Server Error / Max retries exceeded"
                        )

                        if not refund_success:
                            # add Dead Letter Queue or DB Table to let admin manually refund?
                            logger.critical(f"[ALERT] Failed to process refund for Job {job_id}!")
                
        except Exception as e:
            logger.error(f"Error processing jobs: {e}")
