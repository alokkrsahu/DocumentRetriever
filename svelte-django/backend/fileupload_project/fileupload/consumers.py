# fileupload_project/fileupload/consumers.py

# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Project

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_name = self.scope['url_route']['kwargs']['project_name']
        self.room_group_name = f'chat_{self.project_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send message to room group about new user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.scope['user'].username
            }
        )

        # Update user status
        await self.update_user_status(self.scope['user'].username, is_online=True)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Send message to room group about user leaving
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'username': self.scope['user'].username
            }
        )

        # Update user status
        await self.update_user_status(self.scope['user'].username, is_online=False)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'chat_message':
            message = text_data_json['message']
            username = self.scope['user'].username

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username
                }
            )
        elif message_type == 'user_status':
            is_busy = text_data_json.get('isBusy', False)
            await self.update_user_status(self.scope['user'].username, is_busy=is_busy)

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'username': username
        }))

    async def user_join(self, event):
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'username': username
        }))

    async def user_leave(self, event):
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'username': username
        }))

    async def user_status(self, event):
        # Send user status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'username': event['username'],
            'isOnline': event['isOnline'],
            'isBusy': event['isBusy']
        }))

    @database_sync_to_async
    def update_user_status(self, username, is_online=None, is_busy=None):
        user = User.objects.get(username=username)
        if is_online is not None:
            user.is_online = is_online
        if is_busy is not None:
            user.is_busy = is_busy
        user.save()

        # Notify all clients in the room about the status change
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': username,
                'isOnline': user.is_online,
                'isBusy': user.is_busy
            }
        )
