from pymongo import MongoClient
import certifi
from config import *

client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
db = client.wikiDB
# name of our collection is pages and it is available in core.py -> Page class