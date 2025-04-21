import json
import os
from ..models.credentials import CredentialSet

class ConfigController:
    def __init__(self, view):
        self.view = view
        self.credentials = []
    
    def save_config(self, credentials):
        # Move save configuration logic here
        pass
    
    def load_config(self):
        # Move load configuration logic here
        pass