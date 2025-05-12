import io
import tempfile
import os
import subprocess
from tkinter import messagebox
from ..utils import log_exception

def copy_figure_to_clipboard(fig):
    """Copy the current figure to clipboard"""
    try:
        # Create a temporary file
        # Save figure to a temporary buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
            temp_filename = temp.name
            temp.write(buf.getvalue())
            
        # Use xclip to copy to clipboard (Linux)
        try:
            subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', temp_filename])
            messagebox.showinfo("Success", "Chart copied to clipboard!")
        except FileNotFoundError:
            # If xclip is not available
            messagebox.showinfo("Copy to Clipboard", 
                               f"Chart saved to {temp_filename}\n"
                               "Could not copy directly to clipboard (xclip not found)")
        
        # Clean up temp file after a delay
        def clean_temp():
            try:
                os.unlink(temp_filename)
            except:
                pass
                
        # Schedule cleanup after 30 seconds
        from threading import Timer
        Timer(30.0, clean_temp).start()
            
    except Exception as e:
        log_exception("Failed to copy chart to clipboard", e)
        messagebox.showerror("Error", "Failed to copy chart to clipboard")
