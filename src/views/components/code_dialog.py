import tkinter as tk
from tkinter import ttk

class CodeInputDialog:
    def __init__(self, parent, phone, api_id):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Telegram Authentication")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        
        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Phone number and API ID info
        ttk.Label(
            self.dialog,
            text=f"Authentication for:\nPhone: {phone}\nAPI ID: {api_id}",
            wraplength=350,
            justify="center"
        ).pack(pady=10)
        
        # Code entry label
        ttk.Label(
            self.dialog, 
            text="Please enter the code you received:",
            wraplength=350
        ).pack(pady=10)
        
        # Code entry
        self.code_var = tk.StringVar()
        self.entry = ttk.Entry(
            self.dialog, 
            textvariable=self.code_var,
            width=20
        )
        self.entry.pack(pady=10)
        self.entry.focus()
        
        # Submit button
        ttk.Button(
            self.dialog, 
            text="Submit",
            command=self.submit
        ).pack(pady=10)
        
        self.result = None
        
    def submit(self):
        self.result = self.code_var.get()
        self.dialog.destroy()
        
    def get_code(self):
        self.dialog.wait_window()
        return self.result