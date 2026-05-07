import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging

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


def add_admin(username: str) -> bool:
    insert_query = '''
        INSERT INTO np_admin (username)
        VALUES (%s)
        ON CONFLICT (username) DO NOTHING
    '''
    payload = (username,)
    conn, curr = get_conn_cursor()
    try:
        curr.execute(insert_query, payload)
        conn.commit()
        logging.info(f'add user {username}')
        return True
    except Exception as e:
        print(f'add error: {e}')
        conn.rollback()
        return False
    finally:
        curr.close()
        conn.close()

def remove_admin(username: str) -> bool:
    remove_query = '''
        DELETE FROM np_admin WHERE username = %s
    '''
    payload = (username,)
    conn, curr = get_conn_cursor()
    try:
        curr.execute(remove_query, payload)
        conn.commit()
        logging.info(f'remove user {username}')
        return True
    except Exception as e:
        print(f'remove error: {e}')
        conn.rollback()
        return False
    finally:
        curr.close()
        conn.close()

def is_admin(username: str) -> bool:
    query = '''
        SELECT EXISTS ( SELECT 1 FROM np_admin WHERE username = %s)
    '''
    payload = (username,)
    conn, curr = get_conn_cursor()
    try:
        curr.execute(query, payload)
        exists = curr.fetchone()[0]
        logging.info(f'query user {username}: {exists}')
        return exists
    except Exception as e:
        print(f'remove error: {e}')
        conn.rollback()
        return False
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
    add_admin('pcc')
    remove_admin('pcc')
    add_admin('acc')
    add_admin('bcc')
    add_admin('ccc')
    remove_admin('acc')
    remove_admin('dcc')
    is_admin('acc')
    is_admin('bcc')
    is_admin('dcc')

if __name__ == "__main__":
    run_tests()
