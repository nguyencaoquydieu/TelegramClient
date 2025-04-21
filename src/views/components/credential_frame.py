import tkinter as tk
from tkinter import messagebox

class CredentialFrame:
    def __init__(self, parent, set_id, delete_callback):
        self.frame = tk.Frame(parent)
        self.frame.pack(fill='x', pady=5)
        
        # Create fields with increased widths
        self.api_id = tk.Entry(self.frame, width=20)
        self.api_hash = tk.Entry(self.frame, width=40)
        self.phone = tk.Entry(self.frame, width=20)
        
        # Layout fields with more padding
        tk.Label(self.frame, text="API ID:").pack(side=tk.LEFT, padx=5)
        self.api_id.pack(side=tk.LEFT, padx=5)
        tk.Label(self.frame, text="API Hash:").pack(side=tk.LEFT, padx=5)
        self.api_hash.pack(side=tk.LEFT, padx=5)
        tk.Label(self.frame, text="Phone:").pack(side=tk.LEFT, padx=5)
        self.phone.pack(side=tk.LEFT, padx=5)
        
        # Delete button
        delete_btn = tk.Button(self.frame, text="X", 
                             command=lambda: delete_callback(set_id))
        delete_btn.pack(side=tk.LEFT, padx=10)