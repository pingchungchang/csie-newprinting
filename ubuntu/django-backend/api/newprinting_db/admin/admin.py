import logging

from django.db import connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def add_admin(username: str) -> bool:
    insert_query = '''
        INSERT INTO np_admin (username)
        VALUES (%s)
        ON CONFLICT (username) DO NOTHING
    '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (username,))
        logging.info(f'add user {username}')
        return True
    except Exception as e:
        logging.info(f'add admin error: {e}')
        return False


def remove_admin(username: str) -> bool:
    remove_query = '''
        DELETE FROM np_admin WHERE username = %s
    '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(remove_query, (username,))
        logging.info(f'remove user {username}')
        return True
    except Exception as e:
        logging.info(f'remove admin error: {e}')
        return False


def is_admin(username: str) -> bool:
    query = '''
        SELECT EXISTS ( SELECT 1 FROM np_admin WHERE username = %s)
    '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            exists = bool(row[0]) if row else False
        logging.info(f'query user {username}: {exists}')
        return exists
    except Exception as e:
        logging.info(f'is_admin error: {e}')
        return False


def init():
    # Kept for backwards compatibility with the standalone test runner.
    # The Django runtime uses django.db.connection directly.
    pass


def run_tests():
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
