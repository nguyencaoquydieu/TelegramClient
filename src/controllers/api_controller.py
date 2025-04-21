from flask import Flask, request, jsonify
import threading
from telethon import TelegramClient, events
import asyncio
import json
import os
from datetime import datetime
from threading import Lock
from queue import Queue
from ..views.components.code_dialog import CodeInputDialog

class APIController:
    def __init__(self, view):
        self.view = view
        self.api_running = False
        self.app = Flask(__name__)
        self.server_thread = None
        self.loop = None
        self.clients = {}  # Dictionary to store multiple clients
        self.responses = {}  # Dictionary to store responses for each client
        self.request_locks = {}  # Locks for each phone number
        self.request_queue = Queue()  # Queue for handling multiple requests
        
        # Register Flask routes
        @self.app.route('/send-message', methods=['POST'])
        def send_message():
            return self._handle_send_message()

    def start_api(self):
        """Start the Flask API server"""
        try:
            if not self.api_running:
                # Load all credentials
                config_file = os.path.join('config', 'telegram_credentials.json')
                with open(config_file, 'r') as f:
                    all_credentials = json.load(f)
                
                # Initialize event loop
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                
                # Define event handler factory
                def create_message_handler(phone_number):
                    async def handle_new_message(event):
                        if event.is_private:  # Only handle private messages
                            self.responses[phone_number] = event.message.text
                            self.view.log_message(
                                f"Received response for {phone_number}: {event.message.text}"
                            )
                    return handle_new_message
                
                # Initialize locks for each phone number
                for cred in all_credentials:
                    phone = cred['phone']
                    self.request_locks[phone] = Lock()
                
                # Initialize and start each client
                for cred in all_credentials:
                    phone = cred['phone']
                    self.view.log_message(f"Starting client for {phone}")
                    
                    client = TelegramClient(
                        f'telegram_session_{phone}',
                        int(cred['api_id']),
                        cred['api_hash'],
                        loop=self.loop
                    )
                    
                    # Define code callback for this client
                    def code_callback():
                        dialog = CodeInputDialog(
                            self.view.root,
                            phone=phone,
                            api_id=cred['api_id']
                        )
                        return dialog.get_code()
                    
                    # Start client with code callback
                    client.start(
                        phone=phone,
                        code_callback=code_callback
                    )
                    
                    # Add message handler for this client
                    handler = create_message_handler(phone)
                    client.add_event_handler(handler, events.NewMessage)
                    
                    # Store client in dictionary
                    self.clients[phone] = client
                    self.view.log_message(f"Client authenticated for {phone}")
                
                # Start Flask in a separate thread
                self.server_thread = threading.Thread(target=self._run_server)
                self.server_thread.daemon = True
                self.server_thread.start()
                
                self.api_running = True
                self.view.update_api_status("Running", "green")  # Update status here
                self.view.log_message(f"API Server started with {len(self.clients)} clients")
            
        except Exception as e:
            self.view.update_api_status("Error", "red")  # Update status on error
            self.view.log_message(f"Error starting API: {str(e)}", 'error')
            raise

    def stop_api(self):
        """Stop the Flask API server"""
        try:
            if self.api_running:
                # Clear all locks
                for lock in self.request_locks.values():
                    if lock.locked():
                        lock.release()
                self.request_locks.clear()
                
                # Shutdown all clients
                for phone, client in self.clients.items():
                    self.view.log_message(f"Disconnecting client for {phone}")
                    client.disconnect()
                self.clients.clear()
                
                # Stop Flask server
                self.api_running = False
                self.view.update_api_status("Stopped", "red")  # Update status here
                self.view.log_message("API Server stopped")
        except Exception as e:
            self.view.update_api_status("Error", "red")  # Update status on error
            self.view.log_message(f"Error stopping API: {str(e)}", 'error')
            raise

    def _run_server(self):
        """Run Flask server in thread"""
        self.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    def _handle_send_message(self):
        """Handle send message request"""
        try:
            data = request.json
            self.view.log_message(f"Received send-message request: {json.dumps(data)}")
            
            destination = data.get('destination')
            message = data.get('message')
            phone = data.get('phone')
            
            # Validate required parameters
            if not all([destination, message, phone]):
                error_msg = f"Missing parameters in request. Required: destination, message, phone. Received: {data}"
                self.view.log_message(error_msg, 'error')
                return jsonify({
                    'error': 'Missing parameters',
                    'required': ['destination', 'message', 'phone']
                }), 400
            
            # Validate phone number format
            if not phone.startswith('+'):
                error_msg = f"Invalid phone format: {phone}"
                self.view.log_message(error_msg, 'error')
                return jsonify({
                    'error': 'Invalid phone number format',
                    'expected': 'Phone number must start with "+" (e.g. +84123456789)'
                }), 400
            
            # Check if phone number exists
            if phone not in self.clients:
                available_phones = list(self.clients.keys())
                error_msg = f"Phone {phone} not found. Available phones: {available_phones}"
                self.view.log_message(error_msg, 'warning')
                return jsonify({
                    'error': 'Phone number not found',
                    'message': f'Phone number {phone} is not registered',
                    'available_phones': available_phones
                }), 404
            
            # Check if phone is currently processing a request
            if not self.request_locks[phone].acquire(blocking=False):
                self.view.log_message(
                    f"Phone {phone} is busy processing another request", 
                    'warning'
                )
                return jsonify({
                    'error': 'Phone is busy',
                    'message': f'Phone {phone} is currently processing another request',
                    'retry_after': 5  # Suggest retry after 5 seconds
                }), 429  # Too Many Requests
            
            try:
                # Clear any previous response
                self.responses[phone] = None
                self.view.log_message(f"Sending message to {destination} using {phone}")
                
                # Send message and wait for response
                async def send_and_wait():
                    # Send message
                    await self.clients[phone].send_message(destination, message)
                    sent_time = datetime.now()
                    self.view.log_message(f"Message sent to {destination}")
                    
                    # Wait for response
                    while (datetime.now() - sent_time).seconds < 30:
                        if self.responses[phone]:
                            response_time = (datetime.now() - sent_time).seconds
                            # Use Python's built-in string literal evaluation
                            decoded_response = bytes(self.responses[phone], 'utf-8').decode('unicode_escape')
                            
                            self.view.log_message(
                                f"Received response from {destination} in {response_time}s: {decoded_response}"
                            )
                            return {
                                'success': True,
                                'message': f'Message sent to {destination}',
                                'response': decoded_response,  # Use decoded response
                                'phone': phone,
                                'timestamp': datetime.now().isoformat(),
                                'response_time': response_time
                            }
                        await asyncio.sleep(1)
                    
                    # Timeout case
                    self.view.log_message(
                        f"No response received from {destination} after 30 seconds", 
                        'warning'
                    )
                    return {
                        'success': True,
                        'message': f'Message sent to {destination}',
                        'response': None,
                        'phone': phone,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'timeout',
                        'timeout': 30
                    }
                
                result = self.loop.run_until_complete(send_and_wait())
                self.view.log_message(f"Request completed: {json.dumps(result)}")
                return jsonify(result), 200
                
            finally:
                # Always release the lock
                self.request_locks[phone].release()
                
        except Exception as e:
            # Release lock if error occurs
            if phone in self.request_locks:
                self.request_locks[phone].release()
            
            error_msg = f"Error processing request: {str(e)}"
            self.view.log_message(error_msg, 'error')
            return jsonify({
                'error': str(e),
                'type': type(e).__name__
            }), 500

    def is_running(self):
        """Return current API status"""
        return self.api_running