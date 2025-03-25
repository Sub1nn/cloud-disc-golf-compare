import os
from dotenv import load_dotenv

def get_secret(secret_name):
    load_dotenv()  # Load variables from .env file
    return os.getenv(secret_name)  # Fetch from local environment