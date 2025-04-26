import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

def get_secret(secret_name):
    return os.getenv(secret_name)  # Fetch from local environment