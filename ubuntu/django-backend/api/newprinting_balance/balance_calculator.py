import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

INIT_BALANCE = 500

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

def insert_if_no_exist(username: str):
    conn, cursor = get_conn_cursor()
    cursor.execute(
        """
INSERT INTO np_balance (username, balance)
VALUES (%s, %s)
ON CONFLICT(username) DO NOTHING;
    """,
        (username, INIT_BALANCE),
    )
    conn.commit()


# withdraws money, returns (success or not, msg)
def safe_withdraw(username: str, amount: int) -> (bool, str):
    conn, cursor = get_conn_cursor()
    insert_if_no_exist(username)
    if amount < 0:
        return (False, "invalid, amount < 0")
    try:
        sql = """
        UPDATE np_balance
        SET balance = balance - %s
        WHERE username = %s AND balance >= %s;
        """
        cursor.execute(sql, (amount, username, amount))
        if cursor.rowcount > 0:
            conn.commit()
            return (True, f"{username} has withdrawn {amount}")
        else:
            return (False, f"{username} may not have enough money")
    except sqlite3.Error as e:
        return (False, f"DB error: {e}")


def set_balance(username: str, amount: int):
    conn, cursor = get_conn_cursor()
    insert_if_no_exist(username)
    try:
        sql = """
        UPDATE np_balance
        SET balance = %s
        WHERE username = %s;
        """
        cursor.execute(sql, (amount, username))
        conn.commit()
        return (True, f"{username}'s balance has been set to {amount}")
    except sqlite3.Error as e:
        return (False, f"DB error: {e}")


# returns -1 if failed, returns correct value if success
def query_balance(username: str) -> int:
    conn, cursor = get_conn_cursor()
    insert_if_no_exist(username)
    try:
        sql = "SELECT balance FROM np_balance WHERE username = %s"
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return -1
    except sqlite3.Error as e:
        print(f"DB query_balance error: {e}")
        return -1

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
    print(query_balance("a"))
    print(safe_withdraw("b", 49))
    print(query_balance("b"))
    print(safe_withdraw("c", 500))
    print(query_balance("c"))
    print(safe_withdraw("c", 504))
    print(query_balance("c"))

if __name__ == "__main__":
    run_tests()
