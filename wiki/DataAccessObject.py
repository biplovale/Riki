from pymongo import MongoClient
import certifi
from config import *
client = MongoClient(connection_string, tlsCAFile=certifi.where())
db = client.wikiDB
# name of our collection is pages and it is available in core.py -> Page class