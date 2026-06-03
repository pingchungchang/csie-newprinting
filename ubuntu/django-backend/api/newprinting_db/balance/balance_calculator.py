import os
from django.db import connection

INIT_BALANCE = 500

def insert_if_no_exist(username: str):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO np_balance (username, balance)
            VALUES (%s, %s)
            ON CONFLICT(username) DO NOTHING;
            """,
            (username, INIT_BALANCE),
        )

# withdraws money, returns (success or not, msg)
def safe_withdraw(username: str, amount: int) -> tuple[bool, str]:
    insert_if_no_exist(username)
    if amount < 0:
        return (False, "invalid, amount < 0")
    
    try:
        with connection.cursor() as cursor:
            sql = """
            UPDATE np_balance
            SET balance = balance - %s
            WHERE username = %s AND balance >= %s;
            """
            cursor.execute(sql, (amount, username, amount))
            if cursor.rowcount > 0:
                return (True, f"{username} has withdrawn {amount}")
            else:
                return (False, f"{username} may not have enough money")
    except Exception as e:
        return (False, f"DB error: {e}")

def set_balance(username: str, amount: int):
    insert_if_no_exist(username)
    try:
        with connection.cursor() as cursor:
            sql = """
            UPDATE np_balance
            SET balance = %s
            WHERE username = %s;
            """
            cursor.execute(sql, (amount, username))
            return (True, f"{username}'s balance has been set to {amount}")
    except Exception as e:
        return (False, f"DB error: {e}")

# returns -1 if failed, returns correct value if success
def query_balance(username: str) -> int:
    insert_if_no_exist(username)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT balance FROM np_balance WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return -1
    except Exception as e:
        print(f"DB query_balance error: {e}")
        return -1
