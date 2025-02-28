import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
client = MongoClient(os.environ['MONGO_URI'] , tlsCAFile=certifi.where())