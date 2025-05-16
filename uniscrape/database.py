"""
This module is responsible for connection to database.
"""
from .config_manager import ConfigManager

from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError


class Database():
    def __init__(self, config_manager: ConfigManager, database_name: str = "Scraped_data", collection_name: str = "Documents"):
        self.config_manager = config_manager
        self.logger_tool = config_manager.logger_tool
        self.logger_print = config_manager.logger_print
        # Database settings
        self.uri = config_manager.database_api_key
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None

    def connect_to_database(self):
        """
        Connects to database and creates Collection object.
        """
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            db = self.client[self.database_name]
            self.collection = db[self.collection_name]
            self.logger_tool.info("Successfully connected to MongoDB!")

        except ConnectionFailure as e:
            self.logger_tool.error(f"Failed to connect to MongoDB: {e}")
            self.logger_print.error(f"Failed to connect to MongoDB: {e}")
            raise

    def append_to_database(self, data: dict) -> None:
        if self.collection is None:
            raise RuntimeError(
                "Database connection not established. Call connect_to_database() first.")

        try:
            result = self.collection.insert_one(data)
            self.logger_print.info(
                f"Added document with ID: {result.inserted_id}")
        except PyMongoError as e:
            self.logger_print.error(f"Failed to add document: {e}")
            self.logger_tool.error(f"Failed to add document: {e}")
            raise

    def close_connection(self):
        if self.client:
            self.client.close()
            self.logger_tool.info("Connection ended.")
