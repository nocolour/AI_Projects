"""
Configuration management module
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from .settings_encryption import SettingsEncryption
from .utils import log_exception

class ConfigManager:
    """
    Manages application configuration loading, saving and access
    """
    
    def __init__(self, encryption_util: SettingsEncryption, config_path: str):
        """
        Initialize the config manager
        
        Args:
            encryption_util: Encryption utility for securing configuration
            config_path: Path to the configuration file
        """
        self.encryption = encryption_util
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
    
    def load(self) -> bool:
        """
        Load configuration from encrypted file
        
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        if not os.path.exists(self.config_path):
            return False
            
        try:
            with open(self.config_path, "rb") as f:
                encrypted_data = f.read()
            
            self.config = self.encryption.decrypt_data(encrypted_data)
            return True
        except Exception as e:
            log_exception("Failed to load configuration", e)
            return False
    
    def save(self) -> Tuple[bool, str]:
        """
        Save configuration to encrypted file
        
        Returns:
            Tuple of (success, message)
        """
        try:
            encrypted_data = self.encryption.encrypt_data(self.config)
            
            with open(self.config_path, "wb") as f:
                f.write(encrypted_data)
            
            return True, "Configuration saved securely."
        except Exception as e:
            error_msg = log_exception("Failed to save configuration", e)
            return False, error_msg
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            The configuration value or default
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
