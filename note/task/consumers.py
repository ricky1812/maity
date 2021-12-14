import json
from urllib.parse import parse_qs

import channels.layers
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ValidationError

from user.models import User
from cryptography.fernet import Fernet
from decouple import config
from datetime import datetime
import datetime as dt

channel_layer = channels.layers.get_channel_layer()

# token authenticate
from rest_framework_simplejwt.backends import TokenBackend


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):


        try:
            token = parse_qs(self.scope["query_string"].decode("utf8"))["token"][0]

            token = bytes(token, 'utf-8')


            key = config('KEY')

            fernet = Fernet(key)


            decMessage = fernet.decrypt(token).decode()

            decMessage_list = decMessage.split('_')
            user_id = decMessage_list[1]
            token_time = decMessage_list[0]
            token_time = float(token_time)
            token_time = dt.datetime.utcfromtimestamp(token_time / 1000)
            current = datetime.now()
            diff = current - token_time
            diff_hr = diff.total_seconds() / 3600
            if diff_hr > 20:
                print("Token expired")

            else:
                self.room_name = user_id
                self.room_group_name = 'chat_%s' % self.room_name
                await self.channel_layer.group_add(
                    self.room_name,
                    self.channel_name
                )

                await self.accept()



        except ValidationError as e:
            print(e)

    # ...
    async def receive(self, text_data=None, bytes_data=None):

        if self.scope['user'].id:
            pass
        else:
            try:
                # It means user is not authenticated yet.
                data = json.loads(text_data)
                if 'token' in data.keys():
                    token = data['token']
                    user = fetch_user_from_token(token)
                    self.scope['user'] = user

            except Exception as e:
                # Data is not valid, so close it.
                print(e)
                pass

        if not self.scope['user'].id:
            self.close()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'tweet_send',
                'data': message
            }
        )

    async def tweet_send(self, event):
        data = event['data']
        model = event['model']


        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'data': data,
            'model': model
        }))
