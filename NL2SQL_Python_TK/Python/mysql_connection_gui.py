import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import traceback

try:
    import pymysql
    from sqlalchemy import create_engine, text
    import pandas as pd
    import matplotlib.pyplot as plt
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql", "sqlalchemy", "pandas", "matplotlib"])
    import pymysql
    from sqlalchemy import create_engine, text
    import pandas as pd
    import matplotlib.pyplot as plt

import socket
import time
from urllib.parse import quote_plus

def test_network_connectivity(host, port, log):
    log(f"\n== Testing network connectivity to {host}:{port} ==")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        if result == 0:
            log(f"✅ Successfully connected to {host} on port {port}")
            return True
        else:
            log(f"❌ Failed to connect to {host} on port {port} (Error code: {result})")
            return False
    except Exception as e:
        log(f"❌ Network connectivity test failed: {str(e)}")
        return False

def test_mysql_connection_direct(host, port, user, password, database, log):
    log(f"\n== Testing direct MySQL connection using PyMySQL ==")
    start_time = time.time()
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database if database else None,
            connect_timeout=10
        )
        duration = time.time() - start_time
        log(f"✅ Successfully connected using PyMySQL in {duration:.2f} seconds")
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        log(f"   MySQL server version: {version}")
        if database:
            try:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                log(f"   Found {len(tables)} tables in database '{database}'")
            except Exception as e:
                log(f"   Could not list tables: {str(e)}")
                log(traceback.format_exc())
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        duration = time.time() - start_time
        log(f"❌ Connection failed in {duration:.2f} seconds: {str(e)}")
        log(traceback.format_exc())
        return False

def test_sqlalchemy_connection(host, port, user, password, database, log):
    log(f"\n== Testing SQLAlchemy connection ==")
    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    if database:
        connection_string = f"mysql+pymysql://{safe_user}:{safe_password}@{host}:{port}/{database}"
    else:
        connection_string = f"mysql+pymysql://{safe_user}:{safe_password}@{host}:{port}"
    log(f"Connection string: {connection_string.replace(safe_password, '********')}")
    start_time = time.time()
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            duration = time.time() - start_time
            log(f"✅ Successfully connected using SQLAlchemy in {duration:.2f} seconds")
            result = conn.execute(text("SELECT 1"))
            log("   Simple query executed successfully")
        return True
    except Exception as e:
        duration = time.time() - start_time
        log(f"❌ SQLAlchemy connection failed in {duration:.2f} seconds: {str(e)}")
        log(traceback.format_exc())
        return False

def run_tests(host, port, user, password, database, log, done_callback):
    log("===== MySQL CONNECTION TEST UTILITY =====")
    log(f"Host: {host}")
    log(f"Port: {port}")
    log(f"User: {user}")
    log(f"Database: {database or 'Not specified'}")
    network_ok = test_network_connectivity(host, port, log)
    direct_ok = test_mysql_connection_direct(host, port, user, password, database, log)
    sqlalchemy_ok = test_sqlalchemy_connection(host, port, user, password, database, log)
    log("\n===== TEST SUMMARY =====")
    log(f"Network connectivity: {'✅ PASS' if network_ok else '❌ FAIL'}")
    log(f"Direct MySQL connection: {'✅ PASS' if direct_ok else '❌ FAIL'}")
    log(f"SQLAlchemy connection: {'✅ PASS' if sqlalchemy_ok else '❌ FAIL'}")
    done_callback()

class MySQLConnectionGUI:
    def __init__(self, root):
        self.root = root
        root.title("MySQL Connection Test Utility")
        frm = ttk.Frame(root, padding=10)
        frm.grid()
        ttk.Label(frm, text="Host:").grid(column=0, row=0, sticky="e")
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(frm, textvariable=self.host_var, width=20).grid(column=1, row=0)
        ttk.Label(frm, text="Port:").grid(column=0, row=1, sticky="e")
        self.port_var = tk.StringVar(value="3306")
        ttk.Entry(frm, textvariable=self.port_var, width=20).grid(column=1, row=1)
        ttk.Label(frm, text="User:").grid(column=0, row=2, sticky="e")
        self.user_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.user_var, width=20).grid(column=1, row=2)
        ttk.Label(frm, text="Password:").grid(column=0, row=3, sticky="e")
        self.password_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.password_var, width=20, show="*").grid(column=1, row=3)
        ttk.Label(frm, text="Database:").grid(column=0, row=4, sticky="e")
        self.database_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.database_var, width=20).grid(column=1, row=4)
        self.test_btn = ttk.Button(frm, text="Test Connection", command=self.start_test)
        self.test_btn.grid(column=0, row=5, columnspan=2, pady=5)

        # Add Load Data and Visualize buttons
        self.load_btn = ttk.Button(frm, text="Load Data", command=self.load_data, state="disabled")
        self.load_btn.grid(column=0, row=6, pady=5)
        self.visual_btn = ttk.Button(frm, text="Visualize", command=self.visualize_data, state="disabled")
        self.visual_btn.grid(column=1, row=6, pady=5)

        self.output = scrolledtext.ScrolledText(frm, width=70, height=20, state="disabled")
        self.output.grid(column=0, row=7, columnspan=2, pady=5)

        # Table and column selection for visualization
        self.table_var = tk.StringVar()
        self.column_var = tk.StringVar()
        ttk.Label(frm, text="Table:").grid(column=0, row=8, sticky="e")
        self.table_combo = ttk.Combobox(frm, textvariable=self.table_var, state="readonly")
        self.table_combo.grid(column=1, row=8, sticky="we")
        ttk.Label(frm, text="Column:").grid(column=0, row=9, sticky="e")
        self.column_combo = ttk.Combobox(frm, textvariable=self.column_var, state="readonly")
        self.column_combo.grid(column=1, row=9, sticky="we")

        for i in range(10):
            frm.rowconfigure(i, pad=2)
        frm.columnconfigure(1, weight=1)

        self.df = None
        self.engine = None

    def log(self, msg):
        self.output.configure(state="normal")
        self.output.insert(tk.END, msg + "\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")
        self.root.update_idletasks()

    def start_test(self):
        self.output.configure(state="normal")
        self.output.delete(1.0, tk.END)
        self.output.configure(state="disabled")
        self.test_btn.config(state="disabled")
        self.load_btn.config(state="disabled")
        self.visual_btn.config(state="disabled")
        self.table_combo['values'] = []
        self.column_combo['values'] = []
        args = (
            self.host_var.get(),
            self.port_var.get(),
            self.user_var.get(),
            self.password_var.get(),
            self.database_var.get(),
            self.log,
            self.on_test_done
        )
        threading.Thread(target=run_tests, args=args, daemon=True).start()

    def on_test_done(self):
        self.test_btn.config(state="normal")
        # Enable Load Data if test passed and database is specified
        if self.database_var.get():
            self.load_btn.config(state="normal")

    def load_data(self):
        self.output.configure(state="normal")
        self.output.insert(tk.END, "\n== Loading tables from database ==\n")
        self.output.configure(state="disabled")
        self.root.update_idletasks()
        try:
            safe_user = quote_plus(self.user_var.get())
            safe_password = quote_plus(self.password_var.get())
            db = self.database_var.get()
            conn_str = f"mysql+pymysql://{safe_user}:{safe_password}@{self.host_var.get()}:{self.port_var.get()}/{db}"
            self.engine = create_engine(conn_str)
            with self.engine.connect() as conn:
                tables = conn.execute(text("SHOW TABLES")).fetchall()
                table_names = [t[0] for t in tables]
                self.table_combo['values'] = table_names
                if table_names:
                    self.table_var.set(table_names[0])
                    self.load_table_preview(table_names[0])
                else:
                    self.output.configure(state="normal")
                    self.output.insert(tk.END, "No tables found in database.\n")
                    self.output.configure(state="disabled")
                    self.visual_btn.config(state="disabled")
        except Exception as e:
            self.output.configure(state="normal")
            self.output.insert(tk.END, f"Error loading tables: {e}\n")
            self.output.configure(state="disabled")
            self.visual_btn.config(state="disabled")
            return
        self.table_combo.bind("<<ComboboxSelected>>", self.on_table_selected)
        self.visual_btn.config(state="normal")

    def on_table_selected(self, event=None):
        table = self.table_var.get()
        if table:
            self.load_table_preview(table)

    def load_table_preview(self, table):
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM `{table}` LIMIT 10", conn)
                self.df = df
                self.output.configure(state="normal")
                self.output.insert(tk.END, f"\nPreview of '{table}':\n")
                self.output.insert(tk.END, df.head().to_string() + "\n")
                self.output.configure(state="disabled")
                # Update columns for visualization
                self.column_combo['values'] = list(df.columns)
                if len(df.columns) > 0:
                    self.column_var.set(df.columns[0])
        except Exception as e:
            self.output.configure(state="normal")
            self.output.insert(tk.END, f"Error loading table '{table}': {e}\n")
            self.output.configure(state="disabled")

    def visualize_data(self):
        table = self.table_var.get()
        column = self.column_var.get()
        if not table or not column:
            messagebox.showwarning("Select Table/Column", "Please select a table and column to visualize.")
            return
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(f"SELECT `{column}` FROM `{table}`", conn)
            plt.figure(figsize=(8, 4))
            if pd.api.types.is_numeric_dtype(df[column]):
                df[column].plot(kind='hist', bins=20, title=f"Histogram of {column} in {table}")
                plt.xlabel(column)
                plt.ylabel("Frequency")
            else:
                df[column].value_counts().plot(kind='bar', title=f"Value counts of {column} in {table}")
                plt.xlabel(column)
                plt.ylabel("Count")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Visualization Error", f"Could not visualize data: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MySQLConnectionGUI(root)
    root.mainloop()
