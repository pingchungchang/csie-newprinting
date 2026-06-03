import logging
from django.db import connection

logger = logging.getLogger(__name__)

def create_submission(username: str, printer: str, pages: int, money: int) -> int:
    """
    Create a pending submission skeleton in DB and return the generated uid.
    """
    query = """
        INSERT INTO np_submission (username, printer, pages, money, status, retry_count, created_at)
        VALUES (%s, %s, %s, %s, 'pending', 0, NOW())
        RETURNING uid;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, [username, printer, pages, money])
            row = cursor.fetchone()
            if row:
                return row[0]
            raise Exception("Failed to retrieve uid after insert.")
    except Exception as e:
        logger.error(f"[DB Error] Failed to create submission: {e}")
        raise

def mark_submission_refunded(uid: int, reason: str) -> bool:
    """
    Update submission status to 'refunded'.
    """
    query = "UPDATE np_submission SET status = 'refunded' WHERE uid = %s;"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, [uid])
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"[DB Error] Failed to update submission {uid} to refunded: {e}")
        return False
