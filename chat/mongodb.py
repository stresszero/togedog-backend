import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

# import django
# django.setup()

from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient, DESCENDING

from django.conf import settings


client = MongoClient(settings.MONGODB_ADDRESS)

chat_db = client.get_database("mbtichat")
messages_collection = chat_db.get_collection("messages")
# users_collection = chat_db.get_collection("users")
# rooms_collection = chat_db.get_collection("rooms")
# room_members_collection = chat_db.get_collection("room_members")

def save_message(message, sender_id, room_id):
    return str(messages_collection
    .insert_one({
        'room_id': room_id, 
        'message': message, 
        'sender_id': sender_id, 
        'created_at': datetime.utcnow()
    }).inserted_id)
