import os
from bson.errors import InvalidId
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient, DESCENDING

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")

client = MongoClient(settings.MONGODB_ADDRESS)

chat_db = client.get_database("mbtichat")
messages_collection = chat_db.get_collection("messages")
room_members_collection = chat_db.get_collection("room_members")


def save_message(message, nickname, sender_id, room_id):
    return str(messages_collection
    .insert_one({
        'message': message, 
        'sender_nickname': nickname,
        'sender_id': sender_id, 
        'room_id': room_id, 
        'created_at': datetime.utcnow()
    }).inserted_id)

def get_message(message_id):
    try:
        message_data = messages_collection.find_one({'_id': ObjectId(message_id)})
    except InvalidId:
        return False
    return message_data

def add_room_member(room_id, user_id):
    room_members_collection.insert_one(
        {
            '_id': {'room_id': room_id, 'user_id': user_id},
            'created_at': datetime.utcnow()
        })

def remove_room_member(room_id, user_id):
    room_members_collection.delete_one({
        '_id': {'room_id': room_id, 'user_id': user_id},
    })

def get_messages(room_id, page_size=10, page=0):
    offset = page * page_size
    messages = list(
        messages_collection.find({'room_id': room_id}).sort('_id', DESCENDING).limit(page_size).skip(offset))
    for message in messages:
        message['created_at'] = message['created_at'].strftime("%d %b, %H:%M")
    return messages[::-1]
