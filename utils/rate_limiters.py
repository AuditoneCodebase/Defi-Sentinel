import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ['MONGO_URI'],
    default_limits=["200 per day", "50 per hour"]
)
