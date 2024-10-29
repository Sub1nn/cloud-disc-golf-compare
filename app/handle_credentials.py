
import os
from dotenv import load_dotenv

def get_secret(secret_name):

    app_env = 'local'
    
    if app_env == 'local':
        load_dotenv() 
        return os.getenv(secret_name)
    
    else:
        raise ValueError(f"Unsupported APP_ENV value: {app_env}")