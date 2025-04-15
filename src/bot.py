from telethon import TelegramClient, events, utils
import os
from dotenv import load_dotenv

# Set time offset (in seconds)
utils.time_offset = 0

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')

# Create the Telegram client
client = TelegramClient('user_session', api_id, api_hash)

# Event handler for new messages
@client.on(events.NewMessage)
async def handle_new_message(event):
    sender = await event.get_sender()
    sender_name = sender.username or sender.first_name or "Unknown"
    print(f"Message from {sender_name}: {event.text}")

    # Reply to the sender
    # await event.reply("Hello! I received your message.")

async def main():
    # Send a message to a specific phone number
    phone_number = '+84972292961'
    await client.send_message(phone_number, 'Hello from Telethon!')

    bot_username = '@GamethuVN_bot'
    await client.send_message(bot_username, 'tl dieu01')

# Start the client
with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()