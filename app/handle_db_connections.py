import pymysql
import decimal

from handle_credentials import get_secret

def create_conn():

    connection_host = get_secret("connection_host")
    connection_user = get_secret("connection_user")
    connection_password = get_secret("connection_password")
    connection_database = get_secret("connection_database")

    connection = pymysql.connect(host = connection_host, user = connection_user, password = connection_password, database = connection_database, connect_timeout = 1800)
    
    return connection

def execute_insert(connection, query, statement):
    cursor = connection.cursor()
    try:
        cursor.executemany(query, statement)
        connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()
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
