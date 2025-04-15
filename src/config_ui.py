import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import os
from dotenv import load_dotenv
import api
from logger_config import setup_logger
from datetime import datetime

# Setup logger
logger = setup_logger('telegram_ui')

class ConfigUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram API Configuration")
        
        # Configure window
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Create frames
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill='both')
        
        # API ID
        tk.Label(self.main_frame, text="API ID:").grid(row=0, column=0, sticky='w', pady=5)
        self.api_id = tk.Entry(self.main_frame, width=40)
        self.api_id.grid(row=0, column=1, pady=5)
        
        # API Hash
        tk.Label(self.main_frame, text="API Hash:").grid(row=1, column=0, sticky='w', pady=5)
        self.api_hash = tk.Entry(self.main_frame, width=40)
        self.api_hash.grid(row=1, column=1, pady=5)
        
        # Status Label
        self.status_label = tk.Label(self.main_frame, text="API Status: Stopped", fg="red")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Buttons Frame
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Save Button
        tk.Button(btn_frame, text="Save", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
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

    def save_config(self):
        api_id = self.api_id.get().strip()
        api_hash = self.api_hash.get().strip()
        
        if not api_id or not api_hash:
            self.log_message("Error: Missing API credentials", 'error')
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            # Validate API ID is a number
            int(api_id)
            
            # Save to .env file
            with open('.env', 'w') as f:
                f.write(f"TELEGRAM_API_ID={api_id}\n")
                f.write(f"TELEGRAM_API_HASH={api_hash}\n")
            
            self.log_message(f"Configuration saved successfully (API ID: {api_id})")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except ValueError:
            self.log_message("Error: Invalid API ID format", 'error')
            messagebox.showerror("Error", "API ID must be a number")

    def load_config(self):
        if os.path.exists('.env'):
            load_dotenv()
            api_id = os.getenv('TELEGRAM_API_ID', '')
            api_hash = os.getenv('TELEGRAM_API_HASH', '')
            
            self.api_id.delete(0, tk.END)
            self.api_id.insert(0, api_id)
            
            self.api_hash.delete(0, tk.END)
            self.api_hash.insert(0, api_hash)
            
            self.log_message("Configuration loaded from .env file")
        else:
            self.log_message("No configuration file found", 'warning')

    def toggle_api(self):
        if not self.api_running:
            try:
                # Start API in a new thread
                self.api_thread = threading.Thread(target=api.start_api)
                self.api_thread.daemon = True
                self.api_thread.start()
                self.api_running = True
                self.status_label.config(text="API Status: Running", fg="green")
                self.toggle_btn.config(text="Stop API")
                self.log_message("API Server started successfully")
                
                # Ensure callback is set after restart
                api.set_ui_callback(self.log_message)
                
            except Exception as e:
                error_msg = f"Failed to start API: {str(e)}"
                self.log_message(error_msg, 'error')
                messagebox.showerror("Error", error_msg)
                self.api_running = False
        else:
            try:
                # Stop API
                api.stop_api()
                self.api_running = False
                self.status_label.config(text="API Status: Stopped", fg="red")
                self.toggle_btn.config(text="Start API")
                self.log_message("API Server stopped")
            except Exception as e:
                error_msg = f"Failed to stop API: {str(e)}"
                self.log_message(error_msg, 'error')
                messagebox.showerror("Error", error_msg)

def main():
    root = tk.Tk()
    app = ConfigUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()