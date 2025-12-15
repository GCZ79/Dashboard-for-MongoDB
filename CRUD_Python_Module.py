# CS340 Project One | CRUD Module
# Author: GCZ79
# Date: 11/24/2025
# Description: CRUD operations module for the AAC (Austin Animal Center) MongoDB database.

from pymongo import MongoClient
from bson.objectid import ObjectId

class AnimalShelter:
    """ CRUD operations for the Animal collection in MongoDB """
    """ This class provides CRUD functionalities (Create, Read, Update, Delete) """

    def __init__(self, username='aacuser', password='NoSQLNoParty'):
        """ Initializes the connection to MongoDB """        
        
        USER = username    # MongoDB username
        PASS = password    # MongoDB password
        HOST = 'localhost' # hostname of the MongoDB server
        PORT = 27017       # port number of the MongoDB server
        DB   = 'aac'       # database name
        COL  = 'animals'   # collection name
        
        try:
            self.client     = MongoClient(f'mongodb://{USER}:{PASS}@{HOST}:{PORT}')
            self.database   = self.client[DB]
            self.collection = self.database[COL]
            print("Connection to MongoDB established successfully")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")

    def create(self, data):
        """ Inserts a document into the MongoDB collection """
        """ Input: data - dictionary with key/value pairs to insert """
        """ Returns: True if successful, False otherwise """

        try: # Validate input data
            if data is not None and isinstance(data, dict):
                # Insert the document into the animals collection
                result = self.collection.insert_one(data)
                # Check if insertion was successful by verifying inserted_id exists
                if result.inserted_id:
                    print(f"Document inserted successfully with ID: {result.inserted_id}")
                    return True
                else:
                    print("Failed to insert document")
                    return False
            else:
                raise Exception("Data parameter is empty or not a dictionary")
        except Exception as e:
            print(f"Error occurred during create operation: {e}")
            return False

    def read(self, query):
        """ Query documents from the MongoDB collection """
        """ Input: query - dictionary with key/value pairs for filtering """
        """ Returns: list of documents if successful, empty list otherwise """

        try: # Validate input query
            if query is not None and isinstance(query, dict):
                # Query the database using find() method
                cursor = self.collection.find(query)
                # Convert cursor to list and return
                result = list(cursor)
                return result
            else:
                raise Exception("Query parameter is empty or not a dictionary")
        except Exception as e:
            print(f"Error occurred during read operation: {e}")
            return []

    def update(self, query, new_values):
        """ Updates document(s) in the MongoDB collection """
        """ Input: query -> key/value lookup pair to filter documents """
        """   new_values -> dictionary of fields to update: {'$set': { ... }} """ 
        """ Return: Number of documents modified """

        try: # Validate that both query and new_values parameters are dictionaries
            if isinstance(query, dict) and isinstance(new_values, dict):
                # Execute update_many to update all documents matching the query
                result = self.collection.update_many(query, new_values)
                # Return the number of documents that were successfully modified
                return result.modified_count
            else: # Raise exception if input validation fails
                raise Exception("Both query and new_values must be dictionaries")
        except Exception as e: # Handle any other exceptions
            print(f"Error occurred during update operation: {e}")
            return 0

    def delete(self, query):
        """ Deletes document(s) from the MongoDB collection """        
        """ Input: query -> key/value lookup pair for find() / delete_many() """
        """ Return: Number of documents deleted """

        try: # Validate that the query parameter is a dictionary
            if isinstance(query, dict):
                # Execute delete_many to remove all documents matching the query
                result = self.collection.delete_many(query)
                # Return the number of documents that were successfully deleted
                return result.deleted_count
            else: # Raise exception if input validation fails
                raise Exception("Query must be a dictionary")
        except Exception as e: # Handle any other exceptions
            print(f"Error occurred during delete operation: {e}")
            return 0