import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": os.environ.get("DB_PORT", "5000"),  # switch to postgres-ha db
    "dbname": os.environ.get("DB_NAME", "newprinting_db"),
    "user": os.environ.get("DB_USER", "printu"),
    "password": os.environ.get("DB_PASSWORD", "nasa3!Nasa3!"),
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_pending_jobs():
    """get pending jobs using row-level locking (SKIP LOCKED), atomic update status to 'processing'"""
    query = """
        SELECT uid, username, printer, pages, money, retry_count 
        FROM np_submission 
        WHERE status = 'pending' 
        FOR UPDATE SKIP LOCKED;
    """
    jobs = []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                jobs = cur.fetchall()
                
                if jobs:
                    uids = tuple([job['uid'] for job in jobs])
                    update_query = "UPDATE np_submission SET status = 'processing' WHERE uid IN %s"
                    cur.execute(update_query, (uids,))
                conn.commit()
    except Exception as e:
        logger.error(f"[DB Error] Failed to get pending jobs: {e}")
    return jobs

def update_job_status(uid, status, wid=None, retry_increment=False):
    """update job status, bind wid if success"""
    updates = ["status = %s"]
    params = [status]
    
    if wid is not None:
        updates.append("wid = %s")
        params.append(wid)
        
    if retry_increment:
        updates.append("retry_count = retry_count + 1")
        
    query = f"UPDATE np_submission SET {', '.join(updates)} WHERE uid = %s;"
    params.append(uid)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                conn.commit()
                logger.info(f"[DB] Updated UID {uid} status to {status}")
    except Exception as e:
        logger.error(f"[DB Error] Failed to update UID {uid}: {e}")
