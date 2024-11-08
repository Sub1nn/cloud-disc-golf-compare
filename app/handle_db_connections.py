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

def read_query(connection, sql_query):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            row_headers = [x[0] for x in cursor.description]
            result = cursor.fetchall()
            json_data = []
            for row in result:
                row_dict = dict(zip(row_headers, row))
                for key, value in row_dict.items():
                    if isinstance(value, decimal.Decimal):
                        row_dict[key] = f"{float(value):.2f}" 
                    elif isinstance(value, float):
                        row_dict[key] = f"{value:.2f}" 
                json_data.append(row_dict)
            return json_data
    finally:
        connection.close()