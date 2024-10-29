
import os

from dotenv import load_dotenv
from google.cloud import secretmanager

def get_secret(secret_name):

    app_env = 'prod'
    
    if app_env == 'local':
        load_dotenv() 
        return os.getenv(secret_name)
    
    elif app_env == 'prod':
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/durable-path-439213-p0/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    
    else:
        raise ValueError(f"Unsupported APP_ENV value: {app_env}")