import datetime
import logging
from dataclasses import dataclass

from django.db import connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@dataclass
class JobData:
    uid: int
    wid: int
    username: str
    printer: str
    created_at: datetime.datetime
    pages: int
    retry_count: int
    status: str
    money: int


    @classmethod
    def empty(cls):
        return cls(
            uid=-1,
            wid=0,
            printer="Unknown",
            created_at=datetime.datetime.now(),
            pages=0,
            retry_count=0,
            status="Invalid",
            username="nptest",
            money=0,
            is_duplex=True,
        )


def _rows_to_jobs(cursor) -> list[JobData]:
    columns = [col[0] for col in cursor.description]
    out: list[JobData] = []
    for row in cursor.fetchall():
        data = dict(zip(columns, row))
        out.append(
            JobData(
                uid=data.get("uid", -1),
                wid=data.get("wid", 0),
                username=data.get("username", ""),
                printer=data.get("printer", ""),
                created_at=data.get("created_at", datetime.datetime.now()),
                pages=data.get("pages", 0),
                retry_count=data.get("retry_count", 0),
                status=data.get("status", "Invalid"),
                money=data.get("money", 0),
                is_duplex=data.get("is_duplex", True),
            )
        )
    return out


def create_new_job(job: JobData) -> int:
    query = '''
        INSERT INTO np_submission (
            wid, username, printer, pages, status, retry_count, created_at, money, is_duplex)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING uid;
    '''
    data = (
        job.wid,
        job.username,
        job.printer,
        job.pages,
        job.status,
        job.retry_count,
        job.created_at,
        job.money,
        job.is_duplex,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, data)
            row = cursor.fetchone()
            return row[0] if row else -1
    except Exception as e:
        logging.info(f'insert failed, error: {e}!')
        return -1


def get_job_by_uid(uid: int) -> JobData:
    query = '''
        SELECT uid, wid, username, printer, created_at, pages, retry_count, status, money, is_duplex
        FROM np_submission
        WHERE uid = %s;
    '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (uid,))
            row = cursor.fetchone()
            if row:
                return JobData(
                    uid=row[0],
                    wid=row[1],
                    username=row[2],
                    printer=row[3],
                    created_at=row[4],
                    pages=row[5],
                    retry_count=row[6],
                    status=row[7],
                    money=row[8],
                    is_duplex=row[9],
                )
            return JobData.empty()
    except Exception as e:
        logging.info(f'get job error: {e}')
        return JobData.empty()


def get_jobs_by_username(username: str) -> list[JobData]:
    query = "SELECT * FROM np_submission WHERE username = %s;"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (username,))
            return _rows_to_jobs(cursor)
    except Exception as e:
        logging.info(f'get user job error: {e}')
        return []


def get_jobs_by_uid_between(start: int, end: int) -> list[JobData]:
    query = "SELECT * FROM np_submission WHERE uid BETWEEN %s AND %s;"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (start, end))
            return _rows_to_jobs(cursor)
    except Exception as e:
        logging.info(f'get jobs by uid range error: {e}')
        return []


_MODIFIABLE_FIELDS = {
    "wid", "username", "printer", "pages",
    "status", "retry_count", "created_at", "money",
    "is_duplex",
}


def modify_by_uid(uid: int, entry_name: str, new_value) -> bool:
    if entry_name not in _MODIFIABLE_FIELDS:
        logging.info(f'modify by uid rejected unknown field: {entry_name}')
        return False
    try:
        with connection.cursor() as cursor:
            quoted = connection.ops.quote_name(entry_name)
            cursor.execute(
                f"UPDATE np_submission SET {quoted} = %s WHERE uid = %s",
                (new_value, uid),
            )
            if cursor.rowcount == 0:
                logging.info(f'unable to find uid={uid}, no modify done')
                return False
            logging.info(f'modified uid={uid}, entry {entry_name} to {new_value}')
            return True
    except Exception as e:
        logging.info(f'modify by uid error: {e}')
        return False


def init():
    # Kept for backwards compatibility with the standalone test runner.
    # The Django runtime uses django.db.connection directly.
    pass
