import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import os
import json
import uuid
from dotenv import load_dotenv
import api
from logger_config import setup_logger
from datetime import datetime

# Setup logger
logger = setup_logger('telegram_ui')

class ConfigUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Client")
        
        # Configure window
        self.root.geometry("785x400")
        self.root.resizable(False, False)
        
        # Create main canvas with scrollbar
        self.canvas = tk.Canvas(root)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar components
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create main frame inside scrollable frame
        self.main_frame = tk.Frame(self.scrollable_frame, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill='both')
        
        # Add mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
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
        
        # Add Log Frame
        log_frame = tk.LabelFrame(self.main_frame, text="Logs", padx=5, pady=5)
        log_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Add Log Text Area
        self.log_area = scrolledtext.ScrolledText(log_frame, width=40, height=8)
        self.log_area.pack(fill='both', expand=True)
        
        # Load existing config
        self.load_config()
        
        # API thread
        self.api_thread = None
        self.api_running = False
        
        # Set callback for API logs
        api.set_ui_callback(self.log_message)
        
        self.log_message("Application started")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def log_message(self, message, level='info'):
        """Add message to log area and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_text = f"[{timestamp}] {message}\n"
        
        self.log_area.insert(tk.END, log_text)
        self.log_area.see(tk.END)  # Scroll to bottom
        
        # Log to file based on level
        if level == 'info':
            logger.info(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)

    def add_credential_set(self):
        """Add a new set of credential fields"""
        set_id = str(uuid.uuid4())
        frame = tk.Frame(self.credentials_frame)
        frame.pack(fill='x', pady=5)
        
        # Create fields with increased widths
        api_id = tk.Entry(frame, width=20)     # Increased from 15
        api_hash = tk.Entry(frame, width=40)    # Increased from 25
        phone = tk.Entry(frame, width=20)       # Increased from 15
        
        # Layout fields with more padding
        tk.Label(frame, text="API ID:").pack(side=tk.LEFT, padx=5)    # Increased padding
        api_id.pack(side=tk.LEFT, padx=5)
        tk.Label(frame, text="API Hash:").pack(side=tk.LEFT, padx=5)
        api_hash.pack(side=tk.LEFT, padx=5)
        tk.Label(frame, text="Phone:").pack(side=tk.LEFT, padx=5)
        phone.pack(side=tk.LEFT, padx=5)
        
        # Delete button with more padding
        delete_btn = tk.Button(frame, text="X", command=lambda: self.delete_credential_set(set_id))
        delete_btn.pack(side=tk.LEFT, padx=10)  # Increased padding
        
        # Store references
        self.credential_sets[set_id] = {
            'frame': frame,
            'api_id': api_id,
            'api_hash': api_hash,
            'phone': phone
        }

    def delete_credential_set(self, set_id):
        """Delete a credential set"""
        if len(self.credential_sets) > 1:  # Keep at least one set
            self.credential_sets[set_id]['frame'].destroy()
            del self.credential_sets[set_id]

    def save_config(self):
        """Save all credential sets"""
        credentials = []
        
        for cred_set in self.credential_sets.values():
            api_id = cred_set['api_id'].get().strip()
            api_hash = cred_set['api_hash'].get().strip()
            phone = cred_set['phone'].get().strip()
            
            if api_id and api_hash and phone:
                try:
                    int(api_id)  # Validate API ID is number
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
        
        try:
            # Create directory if it doesn't exist
            config_dir = 'config'
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                self.log_message("Created config directory")
            
            # Save to JSON file
            config_file = os.path.join(config_dir, 'telegram_credentials.json')
            with open(config_file, 'w') as f:
                json.dump(credentials, f, indent=4)
            
            self.log_message(f"Saved {len(credentials)} credential sets")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            error_msg = f"Error saving configuration: {str(e)}"
            self.log_message(error_msg, 'error')
            messagebox.showerror("Error", error_msg)

    def load_config(self):
        """Load saved credential sets"""
        config_file = os.path.join('config', 'telegram_credentials.json')
        
        if not os.path.exists('config'):
            os.makedirs('config')
            self.log_message("Created config directory")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    credentials = json.load(f)
                
                # If file is empty, create example data
                if not credentials:
                    self.create_example_config()
                    return
                
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
                error_msg = f"Error loading configuration: {str(e)}"
                self.log_message(error_msg, 'error')
                messagebox.showerror("Error", error_msg)
        else:
            # Create empty config file
            with open(config_file, 'w') as f:
                json.dump([], f)
            self.log_message("Created new empty configuration file", 'info')

    def create_example_config(self):
        """Create example credential sets"""
        example_credentials = [
            {
                "api_id": "12345678",
                "api_hash": "abcdef0123456789abcdef0123456789",
                "phone": "+84972292961"
            },
        ]
        
        config_dir = 'config'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            self.log_message("Created config directory")
        
        config_file = os.path.join(config_dir, 'telegram_credentials.json')
        
        try:
            with open(config_file, 'w') as f:
                json.dump(example_credentials, f, indent=4)
            self.log_message("Created example configuration file")
            
            # Reload the configuration
            self.load_config()
            
        except Exception as e:
            error_msg = f"Error creating example configuration: {str(e)}"
            self.log_message(error_msg, 'error')
            messagebox.showerror("Error", error_msg)

    def toggle_api(self):
        if not self.api_running:
            try:
                # Disable the button while starting
                self.toggle_btn.config(state='disabled')
                
                # Start API in a new thread
                self.api_thread = threading.Thread(target=api.start_api)
                self.api_thread.daemon = True
                self.api_thread.start()
                self.api_running = True
                self.status_label.config(text="API Status: Running", fg="green")
                self.toggle_btn.config(text="Stop API", state='normal')  # Re-enable button with new text
                self.log_message("API Server started successfully")
                
                # Ensure callback is set after restart
                api.set_ui_callback(self.log_message)
                
            except Exception as e:
                error_msg = f"Failed to start API: {str(e)}"
                self.log_message(error_msg, 'error')
                messagebox.showerror("Error", error_msg)
                self.api_running = False
                self.toggle_btn.config(state='normal')  # Re-enable button if start fails
        else:
            try:
                # Disable the button while stopping
                self.toggle_btn.config(state='disabled')
                
                # Stop API
                api.stop_api()
                self.api_running = False
                self.status_label.config(text="API Status: Stopped", fg="red")
                self.toggle_btn.config(text="Start API", state='normal')  # Re-enable button with new text
                self.log_message("API Server stopped")
            except Exception as e:
                error_msg = f"Failed to stop API: {str(e)}"
                self.log_message(error_msg, 'error')
                messagebox.showerror("Error", error_msg)
                self.toggle_btn.config(state='normal')  # Re-enable button if stop fails

def main():
    root = tk.Tk()
    app = ConfigUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()