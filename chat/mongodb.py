import os
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

client = MongoClient(settings.MONGODB_ADDRESS)

chat_db = client.get_database("mbtichat")
messages_collection = chat_db.get_collection("messages")

def save_message(message, sender_id, room_id):
    return str(messages_collection
    .insert_one({
        'message': message, 
        'sender_id': sender_id, 
        'room_id': room_id, 
        'created_at': datetime.utcnow()
    }).inserted_id)

def get_message(message_id):
    return messages_collection.find_one({'_id': ObjectId(message_id)})
