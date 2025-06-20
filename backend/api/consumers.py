from channels.generic.websocket import AsyncWebsocketConsumer
import json

class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        # Просто отправляет обратно то же сообщение
        await self.send(text_data=text_data)

class NotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Добро пожаловать в NotifyConsumer!"}))

    async def receive(self, text_data=None, bytes_data=None):
        # Отправляет уведомление о получении сообщения
        await self.send(text_data=json.dumps({"notification": "Сообщение получено!", "data": text_data})) 