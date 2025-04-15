import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.debug(f"WebSocket scope: {self.scope}")

        try:
            # Import models inside the method to avoid AppRegistryNotReady error
            from _api._users.models import Customer

            # Get the authenticated user's email
            user_email = self.scope["user"].email  # Authenticated user's email

            # Get the Customer object associated with the user's email
            self.sender = await sync_to_async(Customer.objects.filter(email=user_email).first, thread_sensitive=False)()
            if not self.sender:
                logger.error(f"No Customer found for user email {user_email}.")
                await self.close()
                return

            # Use the Customer ID as the sender_id
            self.sender_id = self.sender.id

            # Extract receiver_id from the WebSocket URL
            self.receiver_id = int(self.scope["url_route"]["kwargs"]["receiver_id"])  # Ensure receiver_id is an integer

            # Validate that the receiver exists
            self.receiver = await sync_to_async(Customer.objects.filter(id=self.receiver_id).first, thread_sensitive=False)()
            if not self.receiver:
                logger.error(f"Receiver with ID {self.receiver_id} does not exist.")
                await self.close()
                return

            # Create a unique room name for the conversation
            self.room_name = f"dm_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}"
            self.room_group_name = f"chat_{self.room_name}"

            logger.debug(f"WebSocket connect: sender_id={self.sender_id}, receiver_id={self.receiver_id}, room_group_name={self.room_group_name}")

            # Join the room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        except KeyError as e:
            logger.error(f"KeyError: {e}")
            await self.close()
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        logger.debug(f"WebSocket disconnect: room_group_name={self.room_group_name}, close_code={close_code}")

        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        logger.debug(f"WebSocket receive: text_data={text_data}")

        try:
            # Import models inside the method to avoid AppRegistryNotReady error
            from _api._users.models import DM

            text_data_json = json.loads(text_data)
            message = text_data_json["message"]

            # Save the message to the database
            dm = await sync_to_async(DM.objects.create, thread_sensitive=False)(
                sender_id=self.sender_id,
                receiver_id=self.receiver_id,
                message=message.encode("utf-8"),  # Save as binary
            )

            logger.debug(f"Message saved to database: id={dm.id}, sender_id={dm.sender_id}, receiver_id={dm.receiver_id}, sent_at={dm.sent_at}")
            sent_at = await sync_to_async(lambda: dm.sent_at.isoformat())()

            # Broadcast the message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_id": self.sender_id,
                    "receiver_id": self.receiver_id,
                    "sent_at": sent_at,
                }
            )
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "An error occurred while processing your message."
            }))

    async def chat_message(self, event):
        logger.debug(f"chat_message event received: {event}")

        # Ensure all required keys are present
        try:
            message = event["message"]
            sender_id = event["sender_id"]
            receiver_id = event["receiver_id"]
            sent_at = event["sent_at"]
        except KeyError as e:
            logger.error(f"Missing key in event: {e}")
            return

        # Broadcast the message to the WebSocket
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "sent_at": sent_at,
        }))