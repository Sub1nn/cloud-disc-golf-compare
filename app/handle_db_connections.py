import pymysql
from handle_credentials import get_secret

def create_conn():
    connection = pymysql.connect(
        host=get_secret("connection_host"),
        user=get_secret("connection_user"),
        password=get_secret("connection_password"),
        database=get_secret("connection_database"),
        connect_timeout=1800
    )
    return connection

def read_query(connection, sql_query):
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # Directly return dictionaries
            cursor.execute(sql_query)
            return cursor.fetchall()  # Returns list of dicts (no manual conversion needed)
    finally:
        connection.close()