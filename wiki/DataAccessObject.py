import certifi
from pymongo import MongoClient

from config import *


class DatabaseSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseSingleton, cls).__new__(cls)
            cls._instance.client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
            cls._instance.db = cls._instance.client.wikiDB
        return cls._instance


# Now, you can create a single instance of your database like this:
db = DatabaseSingleton().db
