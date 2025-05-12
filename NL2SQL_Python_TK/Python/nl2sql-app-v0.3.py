import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openai
import json
import os
import logging
from datetime import datetime
import traceback
import re  # Added for regex pattern matching in SQL fixes

class NL2SQLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Natural Language to SQL Query System")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Setup logging with daily log files
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"error_{log_date}.log"
        logging.basicConfig(
            filename=log_filename,
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Initialize configuration
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "",
            "port": 3306  # Default MySQL port
        }

        self.openai_api_key = ""
        self.ai_model = "gpt-4o-mini"  # Default AI model
        self.load_config()

        # SQL commands blacklist for security
        self.sql_blacklist = [
            "DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
            "CREATE", "RENAME", "REPLACE", "GRANT", "REVOKE"
        ]

        # Example queries
        self.example_queries = [
            "Show all customers from the USA",
            "What are the top 5 products by sales?",
            "List all employees hired in 2022",
            "Show me the total revenue by month",
            "Which customers have placed more than 10 orders?",
            "Show all tables in the database",
            "Display the schema for the customers table"
        ]

        # Create the UI
        self.create_menu()
        self.create_ui()

    def load_config(self):
        """Load configuration from config file"""
        config_file = "nl2sql_config.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                if "database" in config:
                    self.db_config = config["database"]

                if "openai_api_key" in config:
                    self.openai_api_key = config["openai_api_key"]
                    
                if "ai_model" in config:
                    self.ai_model = config["ai_model"]
            except Exception as e:
                error_msg = f"Failed to load configuration: {str(e)}"
                logging.error(f"{error_msg}\n{traceback.format_exc()}")
                messagebox.showerror("Configuration Error", error_msg)

    def save_config(self):
        """Save configuration to config file"""
        config_file = "nl2sql_config.json"

        try:
            config = {
                "database": self.db_config,
                "openai_api_key": self.openai_api_key,
                "ai_model": self.ai_model
            }

            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)

            messagebox.showinfo("Configuration", "Configuration saved successfully.")
        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Configuration Error", error_msg)

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_ui(self):
        """Create the main user interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create top frame for query input
        query_frame = ttk.LabelFrame(main_frame, text="Natural Language Query", padding=10)
        query_frame.pack(fill=tk.X, pady=5)

        # Query text input
        self.query_text = scrolledtext.ScrolledText(query_frame, height=4, wrap=tk.WORD)
        self.query_text.pack(fill=tk.X, expand=True, pady=5)

        # Example queries dropdown
        example_frame = ttk.Frame(query_frame)
        example_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Label(example_frame, text="Example queries:").pack(side=tk.LEFT, padx=5)
        self.example_var = tk.StringVar()
        example_combo = ttk.Combobox(example_frame, textvariable=self.example_var, width=50, values=self.example_queries)
        example_combo.pack(side=tk.LEFT, padx=5)
        example_combo.bind("<<ComboboxSelected>>", self.use_example)

        # Buttons frame
        button_frame = ttk.Frame(query_frame)
        button_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Button(button_frame, text="Execute Query", command=self.execute_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Schema", command=self.view_schema).pack(side=tk.LEFT, padx=5)

        # Create paned window for SQL/results
        paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # SQL frame
        sql_frame = ttk.LabelFrame(paned, text="Generated SQL", padding=10)
        paned.add(sql_frame, weight=1)

        self.sql_text = scrolledtext.ScrolledText(sql_frame, height=4, wrap=tk.WORD)
        self.sql_text.pack(fill=tk.BOTH, expand=True)

        # Results frame with notebook for table/chart views
        results_frame = ttk.LabelFrame(paned, text="Query Results", padding=10)
        paned.add(results_frame, weight=3)

        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # Table view tab
        table_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(table_frame, text="Table View")

        # Create treeview for results with scrollbars
        tree_frame = ttk.Frame(table_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.result_tree = ttk.Treeview(tree_frame, show="headings",
                                      yscrollcommand=tree_scroll_y.set,
                                      xscrollcommand=tree_scroll_x.set)
        self.result_tree.pack(fill=tk.BOTH, expand=True)

        tree_scroll_y.config(command=self.result_tree.yview)
        tree_scroll_x.config(command=self.result_tree.xview)

        # Chart view tab
        self.chart_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.chart_frame, text="Chart View")

        # Summary view tab
        self.summary_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.summary_frame, text="Summary")

        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=5)

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
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
        host_var = tk.StringVar(value=self.db_config.get("host", ""))
        user_var = tk.StringVar(value=self.db_config.get("user", ""))
        password_var = tk.StringVar(value=self.db_config.get("password", ""))
        database_var = tk.StringVar(value=self.db_config.get("database", ""))
        port_var = tk.StringVar(value=str(self.db_config.get("port", 3306)))

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
        test_conn_btn = ttk.Button(db_frame, text="Test Connection",
                                 command=lambda: self.test_db_connection(host_var.get(), user_var.get(),
                                                                        password_var.get(), database_var.get(),
                                                                        port_var.get()))
        test_conn_btn.grid(row=5, column=0, columnspan=2, pady=10)

        # API settings tab
        api_frame = ttk.Frame(notebook, padding=10)
        notebook.add(api_frame, text="API Settings")

        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(api_frame, text="AI Model:").grid(row=1, column=0, sticky=tk.W, pady=5)

        api_key_var = tk.StringVar(value=self.openai_api_key)
        model_var = tk.StringVar(value=self.ai_model)

        api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, width=40)
        api_key_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Add model selection dropdown
        model_combo = ttk.Combobox(api_frame, textvariable=model_var, width=30, 
                                  values=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"])
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        model_combo.state(["readonly"])  # Make it read-only

        # Buttons frame
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        # Save and Cancel buttons
        ttk.Button(btn_frame, text="Save",
                 command=lambda: self.save_settings(host_var.get(), user_var.get(),
                                                  password_var.get(), database_var.get(),
                                                  port_var.get(), api_key_var.get(),
                                                  model_var.get(), settings_window)).pack(side=tk.RIGHT, padx=5)

        ttk.Button(btn_frame, text="Cancel",
                 command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)

    def test_db_connection(self, host, user, password, database, port):
        """Test the database connection with provided credentials"""
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=int(port)
            )
            connection.close()
            messagebox.showinfo("Connection Test", "Database connection successful!")
        except Exception as e:
            error_msg = f"Failed to connect to database: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Connection Error", error_msg)

    def save_settings(self, host, user, password, database, port, api_key, model, window):
        """Save the settings and close the settings window"""
        try:
            self.db_config = {
                "host": host,
                "user": user,
                "password": password,
                "database": database,
                "port": int(port)
            }

            self.openai_api_key = api_key
            self.ai_model = model

            # Save to config file
            self.save_config()

            # Close the window
            window.destroy()
        except Exception as e:
            error_msg = f"Failed to save settings: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Settings Error", error_msg)

    def execute_query(self):
        """Process the natural language query and execute SQL"""
        try:
            # Get the query text
            query = self.query_text.get("1.0", tk.END).strip()

            if not query:
                messagebox.showwarning("Input Error", "Please enter a query.")
                return

            if not self.openai_api_key:
                messagebox.showwarning("API Key Required", "Please set your OpenAI API key in settings.")
                return

            # Update status
            self.status_var.set("Generating SQL query...")
            self.root.update_idletasks()

            # Generate SQL using the selected model
            sql_query = self.generate_sql(query)

            # Fix ambiguous column references in the query
            sql_query = self.fix_ambiguous_columns(sql_query)
            
            # Display the SQL
            self.sql_text.delete("1.0", tk.END)
            self.sql_text.insert(tk.END, sql_query)

            # Validate SQL
            if not self.validate_sql(sql_query):
                return

            # Update status
            self.status_var.set("Executing query...")
            self.root.update_idletasks()

            # Execute the query
            df = self.execute_sql(sql_query)

            # Display results
            self.display_results(df)

            # Generate chart
            self.generate_chart(df)

            # Generate summary
            self.summary_text.delete("1.0", tk.END)
            summary = self.generate_summary(query, sql_query, df)
            self.summary_text.insert(tk.END, summary)

            # Update status
            self.status_var.set(f"Query completed: {len(df)} rows returned")

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = f"error_{today}.log"
            logging.error(f"Query execution error: {error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Error", f"{error_msg}\nError details exported to {log_file}")
            self.status_var.set("Error occurred")

    def generate_sql(self, query):
        """Generate SQL from natural language using selected AI model"""
        try:
            # First get database schema for context
            schema_info = self.get_db_schema()

            # Set up the prompt for AI model with improved instructions for column disambiguation
            prompt = f"""
            You are a natural language to SQL converter. Convert the following question into a SQL query for MySQL.
            
            Database schema:
            {schema_info}
            
            Question: {query}
            
            Important guidelines:
            1. Only return the SQL query without any explanation or markdown formatting
            2. Do not use backticks or any other formatting
            3. Only use SELECT statements or SHOW statements for security
            4. Your response should be a valid SQL query that can be executed directly
            5. Keep it simple and focused on answering the question
            6. ALWAYS use fully qualified column names (table_name.column_name) in SELECT, JOIN, WHERE, GROUP BY, 
               and ORDER BY clauses when the query involves multiple tables
            7. Be particularly careful with JOIN operations to avoid ambiguous column references
            
            SQL Query:
            """

            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=self.ai_model,  # Use selected AI model
                messages=[
                    {"role": "system", "content": "You are a natural language to SQL converter. You output only valid SQL queries with fully qualified column names."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200
            )

            # Extract SQL query from response
            sql_query = response.choices[0].message.content.strip()

            # Add semicolon if missing
            if not sql_query.endswith(';'):
                sql_query += ';'

            return sql_query

        except Exception as e:
            error_msg = f"Failed to generate SQL query: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg)
            
    def fix_ambiguous_columns(self, sql_query):
        """Fix ambiguous column references in the SQL query"""
        try:
            # Check if the query has JOINs (indicating potential for ambiguity)
            if " JOIN " not in sql_query.upper():
                return sql_query
                
            # Get database connection
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Extract table names from the query
            # This is a simplified approach - a full SQL parser would be better but more complex
            table_pattern = r'\bFROM\s+(\w+)|JOIN\s+(\w+)'
            tables = []
            for match in re.finditer(table_pattern, sql_query, re.IGNORECASE):
                table = match.group(1) if match.group(1) else match.group(2)
                if table:
                    tables.append(table)
            
            # Collect all columns for each table
            table_columns = {}
            for table in tables:
                try:
                    cursor.execute(f"DESCRIBE {table};")
                    columns = [row[0] for row in cursor.fetchall()]
                    table_columns[table] = columns
                except Exception as e:
                    logging.warning(f"Could not get columns for table {table}: {str(e)}")
                    continue
            
            # Find columns that appear in multiple tables
            all_columns = {}
            for table, columns in table_columns.items():
                for column in columns:
                    if column not in all_columns:
                        all_columns[column] = [table]
                    else:
                        all_columns[column].append(table)
            
            # Identify ambiguous columns (those that appear in multiple tables)
            ambiguous_columns = {col: tables for col, tables in all_columns.items() if len(tables) > 1}
            
            # Fix SQL query by qualifying ambiguous columns
            for col, tables in ambiguous_columns.items():
                # Choose the primary table for the column (for simplicity, use the first table)
                primary_table = tables[0]
                
                # Regular expression to find standalone column references (not already qualified)
                pattern = r'(?<!\w\.)(\b' + col + r'\b)(?!\.\w)'
                
                # Replace standalone column references with qualified references
                sql_query = re.sub(pattern, f"{primary_table}.{col}", sql_query)
            
            cursor.close()
            conn.close()
            
            return sql_query
        except Exception as e:
            # Log the error but return the original query to avoid blocking execution
            error_msg = f"Error fixing ambiguous columns: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return sql_query

    def view_schema(self):
        """View the database schema"""
        try:
            schema_info = self.get_db_schema()

            # Show in a new window
            schema_window = tk.Toplevel(self.root)
            schema_window.title("Database Schema")
            schema_window.geometry("600x400")
            schema_window.transient(self.root)

            schema_text = scrolledtext.ScrolledText(schema_window, wrap=tk.WORD)
            schema_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            schema_text.insert(tk.END, schema_info)
            schema_text.config(state=tk.DISABLED)

        except Exception as e:
            error_msg = f"Failed to get schema: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)

    def get_db_schema(self):
        """Get the database schema"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # Get list of tables
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            schema_info = []

            # Get columns for each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name};")
                columns = cursor.fetchall()

                column_info = []
                for column in columns:
                    col_name = column[0]
                    col_type = column[1]
                    column_info.append(f"{col_name} ({col_type})")

                schema_info.append(f"Table: {table_name}\nColumns: {', '.join(column_info)}\n")

            cursor.close()
            conn.close()

            return "\n".join(schema_info)

        except Exception as e:
            error_msg = f"Failed to get database schema: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg)

    def validate_sql(self, sql_query):
        """Validate SQL for safety"""
        try:
            sql_upper = sql_query.upper()

            # Check for blacklisted commands
            for cmd in self.sql_blacklist:
                if cmd in sql_upper and not f"'{cmd}" in sql_upper and not f'"{cmd}' in sql_upper:
                    messagebox.showerror("Security Error",
                                        f"For security reasons, {cmd} commands are not allowed.")
                    return False

            # Ensure the query is a SELECT or SHOW statement
            if not (sql_upper.strip().startswith("SELECT") or sql_upper.strip().startswith("SHOW")):
                messagebox.showerror("Security Error",
                                    "Only SELECT and SHOW queries are allowed for security reasons.")
                return False

            # Ensure no multiple statements (no semicolons except at the end)
            if ";" in sql_query[:-1]:
                messagebox.showerror("Security Error",
                                    "Multiple SQL statements are not allowed.")
                return False

            return True
        except Exception as e:
            error_msg = f"Failed to validate SQL: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg)

    def execute_sql(self, sql_query):
        """Execute SQL query on MySQL database"""
        try:
            conn = mysql.connector.connect(**self.db_config)

            # Execute query and convert to pandas DataFrame
            df = pd.read_sql_query(sql_query, conn)
            conn.close()

            return df

        except Exception as e:
            error_msg = f"Failed to execute SQL query: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg)

    def display_results(self, df):
        """Display results in the treeview"""
        try:
            # Clear existing data
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            # Configure columns
            columns = list(df.columns)
            self.result_tree["columns"] = columns

            # Configure headings
            self.result_tree["show"] = "headings"
            for col in columns:
                self.result_tree.heading(col, text=col)
                self.result_tree.column(col, width=100)

            # Add data rows
            for _, row in df.iterrows():
                values = list(row)
                self.result_tree.insert("", tk.END, values=values)
        except Exception as e:
            error_msg = f"Failed to display results: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg)

    def generate_chart(self, df):
        """Generate appropriate chart for the data"""
        try:
            # Clear current chart
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            # Check if we have data and it's suitable for visualization
            if df.empty or len(df.columns) < 2:
                ttk.Label(self.chart_frame, text="No data available for visualization").pack(expand=True)
                return

            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))

            # Create a default chart based on the data
            if len(df) <= 10:  # Small number of rows - bar chart
                if df.shape[1] == 2:  # Two columns (category and value)
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    df.plot(kind='bar', x=x_col, y=y_col, ax=ax, legend=False)
                    ax.set_ylabel(y_col)
                else:  # More than two columns - select numeric columns for multi-bar
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
                        if non_numeric_cols:
                            x_col = non_numeric_cols[0]
                            df.plot(kind='bar', x=x_col, y=numeric_cols[:3], ax=ax)
                        else:
                            df.plot(kind='bar', ax=ax)
            else:  # More rows - line chart if there seems to be a trend
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if df.shape[1] >= 2 and numeric_cols:
                    # Check if first column might be a date or category for x-axis
                    x_col = df.columns[0]
                    y_cols = numeric_cols
                    df.plot(kind='line', x=x_col, y=y_cols[:3], ax=ax, marker='o')

            ax.set_title("Query Results Visualization")
            plt.tight_layout()

            # Embed the plot in the chart frame
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            error_msg = f"Failed to generate chart: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            ttk.Label(self.chart_frame, text=error_msg).pack(expand=True)

    def generate_summary(self, query, sql_query, df):
        """Generate summary of the query results using selected AI model"""
        try:
            # If we don't have any data, return a simple message
            if df.empty:
                return "No data found for your query."

            # Get data statistics
            row_count = len(df)
            col_count = len(df.columns)

            # Create a summary of the data
            data_sample = df.head(5).to_string()
            data_stats = df.describe().to_string() if not df.empty else "No data"

            # Set up the prompt for AI model
            prompt = f"""
            Analyze the following database query and results:
            
            Natural Language Query: {query}
            SQL Query: {sql_query}
            
            Data sample (first 5 rows):
            {data_sample}
            
            Data statistics:
            {data_stats}
            
            Total rows returned: {row_count}
            
            Please provide a concise, meaningful summary of these results in 3-4 sentences. 
            Focus on key insights, patterns, or notable findings in the data.
            """

            # Call AI model for summary
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=self.ai_model,  # Use selected AI model
                messages=[
                    {"role": "system", "content": "You provide concise, insightful summaries of database query results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )

            # Extract summary from response
            summary = response.choices[0].message.content.strip()

            return summary

        except Exception as e:
            error_msg = f"Failed to generate summary: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return error_msg

    def use_example(self, event):
        """Fill the query text box with the selected example"""
        try:
            example = self.example_var.get()
            self.query_text.delete("1.0", tk.END)
            self.query_text.insert(tk.END, example)
        except Exception as e:
            error_msg = f"Failed to use example: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)

    def clear_query(self):
        """Clear the query text box"""
        try:
            self.query_text.delete("1.0", tk.END)
        except Exception as e:
            error_msg = f"Failed to clear query: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)

    def show_about(self):
        """Show about dialog"""
        try:
            messagebox.showinfo("About NL2SQL Query System",
                              "Natural Language to SQL Query System\n\n"
                              "This application allows you to query MySQL databases "
                              "using natural language. It converts your questions into "
                              "SQL queries using OpenAI's models.\n\n"
                              "Configure your database connection, API key, and AI model in the "
                              "settings to get started.")
        except Exception as e:
            error_msg = f"Failed to show about dialog: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NL2SQLApp(root)
    root.mainloop()