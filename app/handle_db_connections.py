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

def execute_insert(connection, query, statement):
    cursor = connection.cursor()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  # Directly return dictionaries
            cursor.execute(sql_query)
            return cursor.fetchall()  # Returns list of dicts (no manual conversion needed)
    finally:
        cursor.close()
        connection.close()

def execute_select(connection, query, params=None):
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        row_headers = [x[0] for x in cursor.description]
        json_data = [dict(zip(row_headers, row)) for row in results]
        return json_data
    finally:
        cursor.close()
        connection.close()
