from flask import Flask, request, jsonify
import threading
from queue import Queue
from threading import Lock
from telethon import TelegramClient, events
import asyncio
import json
import os
import re
from datetime import datetime
from src.views.components.code_dialog import CodeInputDialog

class APIController:
    def __init__(self, view):
        self.view = view
        self.api_running = False
        self.app = Flask(__name__)
        self.server_thread = None
        self.loop_thread = None # Thread for the asyncio event loop
        self.loop = None
        self.clients = {}  # Dictionary to store multiple clients
        self.responses = {}  # Dictionary to store responses for each client
        self.global_request_lock = Lock() # Global lock for handling send requests one by one
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
                
                # Start the asyncio event loop in a separate thread
                self.loop_thread = threading.Thread(target=self._run_loop)
                self.loop_thread.daemon = True
                self.loop_thread.start()
                
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
                # Stop the asyncio event loop first
                if self.loop and self.loop.is_running():
                    self.view.log_message("Stopping asyncio event loop...")
                    self.loop.call_soon_threadsafe(self.loop.stop) # Request loop stop
                if self.loop_thread:
                    self.loop_thread.join(timeout=5) # Wait for loop thread to finish
                    if self.loop_thread.is_alive():
                        self.view.log_message("Event loop thread did not stop gracefully.", 'warning')
                self.loop = None # Clear the loop reference

                # Shutdown all clients
                for phone, client in self.clients.items():
                    self.view.log_message(f"Disconnecting client for {phone}")
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

    def _run_loop(self):
        """Run the asyncio event loop."""
        asyncio.set_event_loop(self.loop)
        self.view.log_message("Asyncio event loop started.")

        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    def _handle_send_message(self):
        """Handle send message request"""
        # Acquire the global lock before processing the request
        # Wait indefinitely until the lock is available to ensure sequential processing
        self.view.log_message("Attempting to acquire global request lock...")
        self.global_request_lock.acquire()
        self.view.log_message("Global request lock acquired.")
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
            
            try:
                # Clear any previous response
                self.responses[phone] = None
                self.view.log_message(f"Sending message to {destination} using {phone}")
            
                # Send message and wait for response
                async def send_and_wait():
                    destination_id = None # Initialize destination_id
                    try:
                        # Resolve destination to entity/ID *before* sending
                        try:
                            # Use get_entity which works with usernames, phone numbers, or IDs
                            entity = await self.clients[phone].get_entity(destination)
                            destination_id = entity.id
                            self.view.log_message(f"Resolved destination '{destination}' to ID: {destination_id}")
                        except ValueError: # Handle case where destination is not found
                            self.view.log_message(f"Could not find entity for destination: {destination}", 'error')
                            return {
                                'success': False,
                                'error': 'Destination not found',
                                'message': f'Could not resolve Telegram entity for {destination}',
                                'phone': phone,
                                'timestamp': datetime.now().isoformat()
                            }
                        except Exception as e: # Catch other potential errors during entity resolution
                            self.view.log_message(f"Error resolving entity {destination}: {str(e)}", 'error')
                            raise # Re-raise to be caught by the outer handler which returns 500

                        # Clear previous response before sending
                        self.responses[phone] = None
                        
                        # Send message using the resolved entity ID
                        await self.clients[phone].send_message(destination_id, message)
                        sent_time = datetime.now()
                        self.view.log_message(f"Message sent to {destination} (ID: {destination_id}) at {sent_time}")
                        
                        # Wait for the full timeout period, allowing the handler to update the response
                        timeout_seconds = 10
                        elapsed_time = 0
                        while elapsed_time < timeout_seconds:
                            await asyncio.sleep(1) # Check every second
                            elapsed_time = (datetime.now() - sent_time).seconds
                            # Optional: Log waiting progress
                            # self.view.log_message(f"Waiting for response... {elapsed_time}/{timeout_seconds}s elapsed.")
                        
                        # After waiting, check the final response captured by the handler
                        final_response_data = self.responses.get(phone) # Use .get for safety
                        response_time = (datetime.now() - sent_time).total_seconds() # Use total_seconds for precision
                        final_response_text = None
                        # status = 'timeout' # Default status

                        # if final_response_data is not None:
                        #     response_sender_id, response_text = final_response_data
                        #     # Check if the response came from the intended destination
                        #     if response_sender_id == destination_id:
                        #         final_response_text = response_text
                        #         status = 'received'
                        #         self.view.log_message(
                        #             f"Matching response received from {destination} (ID: {destination_id}) within {timeout_seconds}s: {final_response_text}"
                        #         )
                        #     else:
                        #         # A response was received, but from someone else
                        #         status = 'received_other'
                        #         self.view.log_message(
                        #             f"Response received within {timeout_seconds}s, but from unexpected sender (ID: {response_sender_id}) instead of {destination_id}. Message: {response_text}",
                        #             'warning'
                        #         )
                        # else:
                        #     self.view.log_message(
                        #         f"No response received from {destination} (ID: {destination_id}) after {timeout_seconds} seconds",
                        #         'warning'
                        #     )

                        return {
                            'success': True, # Message sending itself was successful (unless get_entity failed)
                            'message': f'Message sent to {destination}',
                            'phone': phone,
                            'timestamp': datetime.now().isoformat(),
                            'response_time': response_time,
                            'response': final_response_data,
                        }
                    except Exception as e:
                        self.view.log_message(f"Error in send_and_wait: {str(e)}", 'error')
                        # Ensure response is cleared on error too
                        self.responses[phone] = None
                        raise
                
                future = asyncio.run_coroutine_threadsafe(send_and_wait(), self.loop)
                # Add a timeout to future.result() to prevent indefinite blocking
                try:
                    # Wait for max 40 seconds (slightly longer than internal timeout)
                    result = future.result(timeout=40) 
                    self.view.log_message(f"Request completed: {json.dumps(result)}")
                except TimeoutError:
                    self.view.log_message("Coroutine execution timed out.", 'error')
                    return jsonify({'error': 'Request timed out', 'message': 'The Telegram operation took too long.'}), 504 # Gateway Timeout
                # Return 200 OK even if destination lookup failed, as the error is in the result JSON
                return jsonify(result), 200 if result.get('success') is not False else 404                
            except Exception as e:
                raise e;
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.view.log_message(error_msg, 'error')
            return jsonify({
                'error': str(e),
                'type': type(e).__name__
            }), 500
        finally:
            # Always release the global lock when done processing or if an error occurred
            self.global_request_lock.release()

    def is_running(self):
        """Return current API status"""
        return self.api_running