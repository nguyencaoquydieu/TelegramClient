# filepath: d:\AutoGame\Python\TelegramClient\telegram-client-project\src\api.py
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
import asyncio
import threading
from logger_config import setup_logger
from threading import Lock
import functools

# Setup logger
logger = setup_logger('telegram_api')

# Callback for UI updates
ui_callback = None

def set_ui_callback(callback):
    global ui_callback
    ui_callback = callback

def log_to_ui(message, level='info'):
    if ui_callback:
        ui_callback(message, level)
    logger.info(message)

# Load environment variables
load_dotenv()

# Get API credentials from environment variables
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')

# Flask app
app = Flask(__name__)

# Store the response globally
response_message = None
client = None
loop = None
loop_lock = Lock()
message_lock = Lock()

def initialize_client():
    global client, loop
    log_to_ui("Initializing Telegram client...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient('user_session', api_id, api_hash, loop=loop)
    
    @client.on(events.NewMessage)
    async def handle_new_message(event):
        global response_message
        response_message = event.text
        log_to_ui(f"Received message: {event.text}")

    # Start the client in the loop
    log_to_ui("Connecting to Telegram...")
    loop.run_until_complete(client.connect())
    if not client.is_user_authorized():
        log_to_ui("Client not authorized. Starting authorization...")
        loop.run_until_complete(client.start())
        log_to_ui("Authorization completed")

def start_api():
    global client, loop
    
    try:
        # Initialize client in the new thread
        if client is None:
            initialize_client()
        
        log_to_ui("Starting Flask API server...")
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        log_to_ui(f"Failed to start API: {str(e)}", 'error')
        raise

def stop_api():
    global client, loop
    
    # Disconnect client
    if client:
        loop.run_until_complete(client.disconnect())
        client = None
        loop = None
    
    # Shutdown Flask
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/send-message', methods=['POST'])
def send_message():
    global response_message, client

    with message_lock:
        response_message = None

        data = request.json
        destination = data.get('destination')
        message = data.get('message')

        log_to_ui(f"Sending message to {destination}")

        if not destination or not message:
            log_to_ui("Missing destination or message", 'error')
            return jsonify({'error': 'Missing destination or message'}), 400

        async def send_and_wait():
            try:
                # Try to resolve the entity first
                try:
                    entity = await client.get_entity(destination)
                    log_to_ui(f"Found entity for {destination}")
                except ValueError:
                    log_to_ui(f"Entity not found for {destination}. Make sure the contact exists in your Telegram.", 'error')
                    return {'error': 'Contact not found. Please add the contact to your Telegram first.'}, 404

                # Send the message
                await client.send_message(entity, message)
                log_to_ui(f"Message sent to {destination}")
                
                # Wait for response
                for _ in range(30):
                    if response_message:
                        log_to_ui(f"Received response: {response_message}")
                        return {'response': response_message}, 200
                    await asyncio.sleep(1)
                
                log_to_ui("No response received within timeout", 'warning')
                return {'error': 'No response received within 30 seconds'}, 408
            
            except Exception as e:
                error_msg = f"Error sending message: {str(e)}"
                log_to_ui(error_msg, 'error')
                return {'error': error_msg}, 500

        # Run the coroutine in the event loop with lock
        with loop_lock:
            result, status_code = loop.run_until_complete(send_and_wait())
        
        return jsonify(result), status_code

if __name__ == '__main__':
    # Start the UI
    from config_ui import main as config_ui
    config_ui()