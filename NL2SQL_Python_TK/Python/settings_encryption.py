import os
import json
from cryptography.fernet import Fernet
import base64
import logging

class SettingsEncryption:
    """Utility class for encrypting and decrypting application settings"""
    
    def __init__(self, key_file='.nl2sql_key.key'):
        """Initialize with a key file path"""
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        
    def _load_or_generate_key(self):
        """Load existing key or generate a new one if it doesn't exist"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as key_file:
                    return key_file.read()
            else:
                key = Fernet.generate_key()
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(self.key_file)), exist_ok=True)
                with open(self.key_file, 'wb') as key_file:
                    key_file.write(key)
                return key
        except Exception as e:
            logging.error(f"Error handling encryption key: {str(e)}")
            # Fallback to a generated key that won't persist
            return Fernet.generate_key()
    
    def encrypt_data(self, data):
        """Encrypt dictionary data"""
        try:
            json_data = json.dumps(data).encode('utf-8')
            return self.cipher.encrypt(json_data)
        except Exception as e:
            logging.error(f"Encryption error: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data to dictionary"""
        try:
            decrypted_json = self.cipher.decrypt(encrypted_data).decode('utf-8')
            return json.loads(decrypted_json)
        except Exception as e:
            logging.error(f"Decryption error: {str(e)}")
            # Return empty dict on decryption failure
            return {}
