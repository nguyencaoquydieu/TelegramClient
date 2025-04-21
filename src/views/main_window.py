from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import os
import json
import uuid
from src.controllers.api_controller import APIController
from src.utils.logger_config import setup_logger

# Setup logger
logger = setup_logger('telegram_ui')

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Client")
        self.root.geometry("785x400")  # Initial size
        self.root.resizable(False, True)  # Allow only vertical resizing
        
        # Initialize controllers
        self.api_controller = APIController(self)
        
        # Create main frame
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill='both')
        
        # Function to update window size
        self.update_window_size()
        
        # Container for credential sets
        self.credentials_frame = tk.LabelFrame(self.main_frame, text="Telegram Credentials", padx=5, pady=5)
        self.credentials_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=5)
        
        # Dictionary to store credential widgets
        self.credential_sets = {}
        
        # Add first credential set
        self.add_credential_set()
        
        # Add Credential Button
        tk.Button(self.main_frame, text="+ Add New Credentials", 
                 command=self.add_credential_set).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Status Label
        self.status_label = tk.Label(self.main_frame, text="API Status: Stopped", fg="red")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Buttons Frame
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Save Button
        tk.Button(btn_frame, text="Save All", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # Start/Stop API Button
        self.toggle_btn = tk.Button(btn_frame, text="Start API", command=self.toggle_api)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        # Log Frame
        log_frame = tk.LabelFrame(self.main_frame, text="Logs", padx=5, pady=5)
        log_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Add Log Text Area
        self.log_area = scrolledtext.ScrolledText(log_frame, width=80, height=10)
        self.log_area.pack(fill='both', expand=True)
        
        # Load existing config
        self.load_config()

    def update_window_size(self, event=None):
        """Update window size based on content"""
        # Wait for all pending events to complete
        self.root.update_idletasks()
        
        # Calculate required height with padding
        required_height = self.main_frame.winfo_reqheight()
        current_height = self.root.winfo_height()
        
        # Update window height if needed
        if required_height != current_height:
            self.root.geometry(f"785x{required_height}")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.main_frame.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_credential_set(self):
        """Add a new set of credential fields"""
        set_id = str(uuid.uuid4())
        frame = tk.Frame(self.credentials_frame)
        frame.pack(fill='x', pady=5)
        
        # Create fields
        api_id = tk.Entry(frame, width=20)
        api_hash = tk.Entry(frame, width=40)
        phone = tk.Entry(frame, width=20)
        
        # Layout fields
        tk.Label(frame, text="API ID:").pack(side=tk.LEFT, padx=5)
        api_id.pack(side=tk.LEFT, padx=5)
        tk.Label(frame, text="API Hash:").pack(side=tk.LEFT, padx=5)
        api_hash.pack(side=tk.LEFT, padx=5)
        tk.Label(frame, text="Phone:").pack(side=tk.LEFT, padx=5)
        phone.pack(side=tk.LEFT, padx=5)
        
        # Delete button
        delete_btn = tk.Button(frame, text="X", command=lambda: self.delete_credential_set(set_id))
        delete_btn.pack(side=tk.LEFT, padx=10)
        
        # Store references
        self.credential_sets[set_id] = {
            'frame': frame,
            'api_id': api_id,
            'api_hash': api_hash,
            'phone': phone
        }
        
        # After adding new credentials, update window size
        self.update_window_size()

    def delete_credential_set(self, set_id):
        """Delete a credential set"""
        if len(self.credential_sets) > 1:
            self.credential_sets[set_id]['frame'].destroy()
            del self.credential_sets[set_id]
            # After deleting credentials, update window size
            self.update_window_size()
        
    def save_config(self):
        """Save all credential sets"""
        credentials = []
        for cred_set in self.credential_sets.values():
            api_id = cred_set['api_id'].get().strip()
            api_hash = cred_set['api_hash'].get().strip()
            phone = cred_set['phone'].get().strip()
            
            if api_id and api_hash and phone:
                try:
                    int(api_id)
                    if not phone.startswith('+'):
                        raise ValueError(f"Phone number must start with '+': {phone}")
                    
                    credentials.append({
                        'api_id': api_id,
                        'api_hash': api_hash,
                        'phone': phone
                    })
                except ValueError as e:
                    self.log_message(f"Error in credentials: {str(e)}", 'error')
                    messagebox.showerror("Error", str(e))
                    return
        
        config_dir = 'config'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        config_file = os.path.join(config_dir, 'telegram_credentials.json')
        with open(config_file, 'w') as f:
            json.dump(credentials, f, indent=4)
            
        self.log_message(f"Saved {len(credentials)} credential sets")
        messagebox.showinfo("Success", "Configuration saved successfully!")

    def load_config(self):
        """Load saved credential sets"""
        config_file = os.path.join('config', 'telegram_credentials.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    credentials = json.load(f)
                
                # Remove default credential set
                if self.credential_sets:
                    set_id = list(self.credential_sets.keys())[0]
                    self.credential_sets[set_id]['frame'].destroy()
                    self.credential_sets.clear()
                
                # Add saved credentials
                for cred in credentials:
                    self.add_credential_set()
                    set_id = list(self.credential_sets.keys())[-1]
                    self.credential_sets[set_id]['api_id'].insert(0, cred['api_id'])
                    self.credential_sets[set_id]['api_hash'].insert(0, cred['api_hash'])
                    self.credential_sets[set_id]['phone'].insert(0, cred['phone'])
                
                self.log_message(f"Loaded {len(credentials)} credential sets")
            except Exception as e:
                self.log_message(f"Error loading configuration: {str(e)}", 'error')
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
        else:
            self.create_example_config()
        
        # After loading config, update window size
        self.update_window_size()

    def create_example_config(self):
        """Create example credential sets"""
        example_credentials = [
            {
                "api_id": "12345678",
                "api_hash": "abcdef0123456789abcdef0123456789",
                "phone": "+84987654321"
            }
        ]
        
        config_dir = 'config'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        config_file = os.path.join(config_dir, 'telegram_credentials.json')
        
        try:
            with open(config_file, 'w') as f:
                json.dump(example_credentials, f, indent=4)
            self.log_message("Created example configuration file")
            self.load_config()
        except Exception as e:
            self.log_message(f"Error creating example configuration: {str(e)}", 'error')
            messagebox.showerror("Error", f"Failed to create example configuration: {str(e)}")

    def toggle_api(self):
        """Toggle API start/stop"""
        try:
            if not self.api_controller.is_running():
                # Disable button while starting
                self.toggle_btn.config(state='disabled')
                self.status_label.config(text="API Status: Starting...", fg="orange")  # Add starting state
                self.api_controller.start_api()
                self.toggle_btn.config(text="Stop API", state='normal')
            else:
                # Disable button while stopping
                self.toggle_btn.config(state='disabled')
                self.status_label.config(text="API Status: Stopping...", fg="orange")  # Add stopping state
                self.api_controller.stop_api()
                self.toggle_btn.config(text="Start API", state='normal')
        except Exception as e:
            error_msg = f"Failed to {'start' if not self.api_controller.is_running() else 'stop'} API: {str(e)}"
            self.log_message(error_msg, 'error')
            messagebox.showerror("Error", error_msg)
            self.toggle_btn.config(state='normal')
            self.status_label.config(text="API Status: Error", fg="red")  # Add error state

    def update_api_status(self, status, color):
        """Update the API status label with the given status and color"""
        self.status_label.config(text=f"API Status: {status}", fg=color)
        self.log_message(f"API Status changed to: {status}")

    def log_message(self, message, level='info'):
        """Log a message to UI and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_text = f"[{timestamp}] {message}\n"
        
        self.log_area.insert(tk.END, log_text)
        self.log_area.see(tk.END)
        
        if level == 'info':
            logger.info(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)