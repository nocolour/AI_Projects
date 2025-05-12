import tkinter as tk
import os
import atexit
from modules.utils import setup_logging, setup_tmp_dir
from modules.database_manager import DatabaseManager
from modules.ai_manager import AIManager
from modules.visualization_manager import VisualizationManager
from modules.settings_manager import SettingsManager
from modules.ui_manager import UIManager
from modules.settings_encryption import SettingsEncryption
from modules.task_manager import TaskManager

class Application:
    def __init__(self):
        # Setup logging and directories
        self.log_dir = setup_logging()
        self.tmp_dir = setup_tmp_dir()
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        self.ai_manager = AIManager()
        
        # Store task manager as instance variable for better resource management
        self.task_manager = TaskManager()
        
        # Create visualization manager with reference to AI manager
        self.vis_manager = VisualizationManager(ai_manager=self.ai_manager)
        
        # Initialize encryption utility
        self.settings_encryption = SettingsEncryption(
            key_file=os.path.join(self.tmp_dir, ".nl2sql_key.key")
        )
        
        # Create the config path
        self.config_path = os.path.join(self.tmp_dir, "nl2sql_config.enc")
        
        # Initialize settings manager
        self.settings_manager = SettingsManager(
            db_manager=self.db_manager,
            ai_manager=self.ai_manager,
            settings_encryption=self.settings_encryption,
            config_path=self.config_path
        )
        
        # Register cleanup handler
        atexit.register(self.cleanup)
    
    def run(self):
        # Load configuration
        self.settings_manager.load_config()
        
        # Create Tkinter root
        root = tk.Tk()
        
        # Set protocol for window close
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize and create UI
        self.ui_manager = UIManager(
            root=root,
            db_manager=self.db_manager,
            ai_manager=self.ai_manager,
            vis_manager=self.vis_manager,
            settings_manager=self.settings_manager
        )
        self.ui_manager.create_ui()
        
        # Start main loop
        root.mainloop()
    
    def on_close(self):
        """Handle window close event"""
        self.cleanup()
        self.ui_manager.root.destroy()
    
    def cleanup(self):
        """Clean up resources before exit"""
        # Shutdown task manager
        try:
            self.task_manager.shutdown()  # Use instance variable for better resource management
        except Exception as e:
            print(f"Error shutting down task manager: {e}")
        
        # Close database connections if any
        if hasattr(self, 'db_manager') and self.db_manager.engine is not None:
            try:
                self.db_manager.engine.dispose()
            except Exception as e:
                print(f"Error disposing database engine: {e}")

def main():
    app = Application()
    app.run()

if __name__ == "__main__":
    main()