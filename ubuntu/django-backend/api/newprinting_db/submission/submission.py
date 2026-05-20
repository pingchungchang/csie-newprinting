import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging
import datetime
from dataclasses import dataclass

@dataclass
class JobData:
    uid: int
    wid: int
    username: str
    printer: str
    created_at: datetime.datetime
    pages: int
    money: int
    retry_count: int
    status: str
    @classmethod
    def empty(cls):
        return cls(
            uid=-1,
            wid=0,
            printer="Unknown",
            created_at=datetime.datetime.now(),
            pages=0,
            money=0,
            retry_count=0,
            status="Invalid",
            username="Guest"
        )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

conn_params = {
    "host": "127.0.0.1",
    "database": "newprinting_db",
    "user": "printu",
    "password": "IDK",
    "port": "5432"
}

def get_conn_cursor():
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    return (conn, cursor)

def create_new_job(job: JobData) -> int:
    sql = '''
        INSERT INTO np_submission (
            wid, username, printer, pages, money, status, retry_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING uid;
    '''
    data = (
        job.wid,
        job.username,
        job.printer,
        job.pages,
        job.money,
        job.status,
        job.retry_count,
        job.created_at
    )
    conn, curr = get_conn_cursor()
    try:
        curr.execute(sql, data)
        uid = curr.fetchone()[0]
        conn.commit()
        return uid
    except Exception as e:
        logging.info(f'insert failed, error: {e}!')
        return -1
    finally:
        curr.close()
        conn.close()

def get_job_by_uid(uid: int) -> JobData:
    sql = '''
        SELECT uid, wid, username, printer, created_at, pages, retry_count, status, money
        FROM np_submission
        WHERE uid = %s;
    '''
    conn, curr = get_conn_cursor()
    try:
        curr.execute(sql, (uid,))
        row = curr.fetchone()
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
                    )
        return JobData.empty()
    except Exception as e:
        logging.info(f'get job error: {e}')
        return JobData.empty()
    finally:
        curr.close()
        conn.close()

def modify_by_uid(uid: int, entry_name: str, new_value) -> bool:
    query = sql.SQL("UPDATE np_submission SET {field} = %s WHERE uid = %s").format(
            field=sql.Identifier(entry_name)
            )
    conn, curr = get_conn_cursor()
    try:
        curr.execute(query, (new_value, uid))
        if curr.rowcount == 0:
            logging.info(f'unable to find uid={uid}, no modify done')
            return False
        else:
            conn.commit()
            logging.info(f'modifieduid={uid}, entry {entry_name} to {new_value}')
    except Exception as e:
        logging.info(f'modify by uid error: {e}')
        return JobData.empty()
    finally:
        curr.close()
        conn.close()

def init():
    global conn_params
    load_dotenv()
    conn_params['database'] = os.getenv("POSTGRES_DB")
    conn_params['user'] = os.getenv("POSTGRES_USER")
    conn_params['password'] = os.getenv("POSTGRES_PASSWORD")
    conn_params['port'] = os.getenv("POSTGRES_PORT")
    print(f'conn_params:\n{conn_params}')

def run_tests():
    init()
    a = JobData.empty()
    a.uid = create_new_job(a)
    logging.info(f'get uid of a = {a.uid}')
    print(get_job_by_uid(a.uid))
    print(get_job_by_uid(-1))
    print(modify_by_uid(a.uid, 'printer', 'nptest'))
    print(get_job_by_uid(a.uid))

if __name__ == "__main__":
    run_tests()
