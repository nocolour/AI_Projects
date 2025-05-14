import os
import tkinter as tk
from tkinter import ttk, messagebox
from .utils import log_exception

class SettingsManager:
    def __init__(self, db_manager, ai_manager, settings_encryption, config_path):
        self.db_manager = db_manager
        self.ai_manager = ai_manager
        self.settings_encryption = settings_encryption
        self.config_path = config_path
    
    def load_config(self):
        """Load configuration from config file with decryption"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "rb") as f:
                    encrypted_data = f.read()
                
                # Decrypt the configuration
                config = self.settings_encryption.decrypt_data(encrypted_data)

                if "database" in config:
                    self.db_manager.update_config(config["database"])

                if "openai_api_key" in config and "ai_model" in config:
                    self.ai_manager.update_config(
                        api_key=config["openai_api_key"],
                        model=config["ai_model"]
                    )
                    
                return True
            except Exception as e:
                error_msg = log_exception("Failed to load configuration", e)
                messagebox.showerror("Configuration Error", error_msg)
                return False
        return False
    
    def save_config(self):
        """Save configuration to encrypted config file"""
        try:
            config = {
                "database": self.db_manager.db_config,
                "openai_api_key": self.ai_manager.api_key,
                "ai_model": self.ai_manager.model
            }

            # Encrypt the configuration
            encrypted_data = self.settings_encryption.encrypt_data(config)
            
            with open(self.config_path, "wb") as f:
                f.write(encrypted_data)

            return True, "Configuration saved securely."
        except Exception as e:
            error_msg = log_exception("Failed to save configuration", e)
            return False, error_msg
    
    def show_settings_dialog(self, parent):
        """Display settings dialog"""
        settings_window = tk.Toplevel(parent)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.transient(parent)
        settings_window.grab_set()

        # Create notebook for settings categories
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Database settings tab
        db_frame = ttk.Frame(notebook, padding=10)
        notebook.add(db_frame, text="Database")

        # Grid layout for database settings
        ttk.Label(db_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(db_frame, text="User:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(db_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(db_frame, text="Database:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(db_frame, text="Port:").grid(row=4, column=0, sticky=tk.W, pady=5)

        # Entry fields with current values
        host_var = tk.StringVar(value=self.db_manager.db_config.get("host", ""))
        user_var = tk.StringVar(value=self.db_manager.db_config.get("user", ""))
        password_var = tk.StringVar(value=self.db_manager.db_config.get("password", ""))
        database_var = tk.StringVar(value=self.db_manager.db_config.get("database", ""))
        port_var = tk.StringVar(value=str(self.db_manager.db_config.get("port", 3306)))

        host_entry = ttk.Entry(db_frame, textvariable=host_var, width=30)
        host_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        user_entry = ttk.Entry(db_frame, textvariable=user_var, width=30)
        user_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        password_entry = ttk.Entry(db_frame, textvariable=password_var, width=30, show="*")
        password_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        database_entry = ttk.Entry(db_frame, textvariable=database_var, width=30)
        database_entry.grid(row=3, column=1, sticky=tk.W, pady=5)

        port_entry = ttk.Entry(db_frame, textvariable=port_var, width=30)
        port_entry.grid(row=4, column=1, sticky=tk.W, pady=5)

        # Test connection button
        test_conn_btn = ttk.Button(
            db_frame, 
            text="Test Connection",
            command=lambda: self._test_connection_callback(
                host_var.get(), user_var.get(),
                password_var.get(), database_var.get(),
                port_var.get()
            )
        )
        test_conn_btn.grid(row=5, column=0, columnspan=2, pady=10)

        # API settings tab
        api_frame = ttk.Frame(notebook, padding=10)
        notebook.add(api_frame, text="API Settings")

        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(api_frame, text="AI Model:").grid(row=1, column=0, sticky=tk.W, pady=5)

        # API key entry
        api_key_var = tk.StringVar(value=self.ai_manager.api_key)
        api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, width=40, show="*")
        api_key_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Model selection
        model_var = tk.StringVar(value=self.ai_manager.model)
        model_combo = ttk.Combobox(api_frame, textvariable=model_var, width=30, 
                                  values=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"])
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        model_combo.state(["readonly"])

        # Buttons frame
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        # Save and Cancel buttons
        ttk.Button(
            btn_frame, 
            text="Save",
            command=lambda: self._save_settings_callback(
                host_var.get(), user_var.get(),
                password_var.get(), database_var.get(),
                port_var.get(), api_key_var.get(),
                model_var.get(), settings_window
            )
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            btn_frame, 
            text="Cancel",
            command=settings_window.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _test_connection_callback(self, host, user, password, database, port):
        """Test database connection callback"""
        try:
            success, message = self.db_manager.test_connection(host, user, password, database, port)
            if success:
                messagebox.showinfo("Connection Test", "Database connection successful!")
            else:
                messagebox.showerror("Connection Error", f"Failed to connect to database: {message}")
        except Exception as e:
            error_msg = log_exception("Connection test error", e)
            messagebox.showerror("Error", error_msg)
    
    def _save_settings_callback(self, host, user, password, database, port, api_key, model, window):
        """Save settings callback"""
        try:
            # Update database config
            db_config = {
                "host": host,
                "user": user,
                "password": password,
                "database": database,
                "port": int(port)
            }
            self.db_manager.update_config(db_config)
            
            # Update AI config
            self.ai_manager.update_config(api_key, model)

            # Save config to file
            success, message = self.save_config()
            if success:
                messagebox.showinfo("Settings", message)
                window.destroy()
            else:
                messagebox.showerror("Settings Error", message)
        except Exception as e:
            error_msg = log_exception("Settings save error", e)
            messagebox.showerror("Error", error_msg)
