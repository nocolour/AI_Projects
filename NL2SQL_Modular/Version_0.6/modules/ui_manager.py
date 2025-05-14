import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
from typing import Optional, Callable, Any
from .utils import log_exception
from .constants import EXAMPLE_QUERIES, WINDOW_SIZE, MIN_WINDOW_SIZE
from .task_manager import TaskManager

class UIManager:
    def __init__(self, root, db_manager, ai_manager, vis_manager, settings_manager):
        self.root = root
        self.db_manager = db_manager
        self.ai_manager = ai_manager
        self.vis_manager = vis_manager
        self.settings_manager = settings_manager
        
        # Replace hardcoded example queries with constant
        self.example_queries = EXAMPLE_QUERIES
        
        # Initialize task manager
        self.task_manager = TaskManager()
        
        # Add progress indicators
        self.progress_var = None
        self.progress_bar = None
        
        # UI components that need to be accessed from methods
        self.query_text = None
        self.sql_text = None
        self.result_tree = None
        self.chart_frame = None
        self.summary_text = None
        self.status_var = None
        self.example_var = None
        self.results_notebook = None
        
        # Store current results for chart generation
        self.current_results = None
    
    def create_ui(self):
        """Create the main user interface"""
        self.root.title("Natural Language to SQL Query System")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])
        
        # Create menu
        self._create_menu()
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create top frame for query input
        self._create_query_frame(main_frame)

        # Create paned window for SQL/results
        paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # SQL frame
        self._create_sql_frame(paned)

        # Results frame with notebook for table/chart views
        self._create_results_frame(paned)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=5)
        
        # Add progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            orient=tk.HORIZONTAL, 
            mode='indeterminate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=2, before=status_bar)
        self.progress_bar.pack_forget()  # Hide initially
    
    def _create_menu(self):
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
    
    def _create_query_frame(self, parent):
        """Create the query input frame"""
        query_frame = ttk.LabelFrame(parent, text="Natural Language Query", padding=10)
        query_frame.pack(fill=tk.X, pady=5)

        # Query text input
        self.query_text = scrolledtext.ScrolledText(query_frame, height=4, wrap=tk.WORD)
        self.query_text.pack(fill=tk.X, expand=True, pady=5)

        # Example queries dropdown
        example_frame = ttk.Frame(query_frame)
        example_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Label(example_frame, text="Example queries:").pack(side=tk.LEFT, padx=5)
        self.example_var = tk.StringVar()
        example_combo = ttk.Combobox(example_frame, textvariable=self.example_var, width=50, 
                                     values=self.example_queries)
        example_combo.pack(side=tk.LEFT, padx=5)
        example_combo.bind("<<ComboboxSelected>>", self.use_example)

        # Buttons frame
        button_frame = ttk.Frame(query_frame)
        button_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Button(button_frame, text="Execute Query", command=self.execute_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Schema", command=self.view_schema).pack(side=tk.LEFT, padx=5)
    
    def _create_sql_frame(self, parent):
        """Create the SQL frame"""
        sql_frame = ttk.LabelFrame(parent, text="Generated SQL", padding=10)
        parent.add(sql_frame, weight=1)

        self.sql_text = scrolledtext.ScrolledText(sql_frame, height=4, wrap=tk.WORD)
        self.sql_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_results_frame(self, parent):
        """Create the results frame with notebook"""
        results_frame = ttk.LabelFrame(parent, text="Query Results", padding=10)
        parent.add(results_frame, weight=3)

        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # Table view tab
        self._create_table_view_tab()

        # Chart view tab
        chart_tab = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(chart_tab, text="Chart View")
        
        # Frame for the chart
        self.chart_frame = ttk.Frame(chart_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame for chart actions
        chart_btn_frame = ttk.Frame(chart_tab)
        chart_btn_frame.pack(fill=tk.X, pady=5, before=self.chart_frame)
        
        # Add button to open chart in new window
        self.pop_out_chart_btn = ttk.Button(
            chart_btn_frame, 
            text="Pop Out Chart in New Window",
            command=self.open_chart_in_new_window
        )
        self.pop_out_chart_btn.pack(side=tk.LEFT, padx=5)
        
        # Summary view tab
        self._create_summary_view_tab()
    
    def _create_table_view_tab(self):
        """Create the table view tab"""
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
    
    def _create_summary_view_tab(self):
        """Create the summary view tab"""
        summary_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(summary_frame, text="Summary")

        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
    
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
            
            return True
        except Exception as e:
            error_msg = log_exception("Failed to display results", e)
            messagebox.showerror("Display Error", error_msg)
            return False
    
    def use_example(self, event):
        """Fill the query text box with the selected example"""
        try:
            example = self.example_var.get()
            self.query_text.delete("1.0", tk.END)
            self.query_text.insert(tk.END, example)
        except Exception as e:
            log_exception("Failed to use example", e)
    
    def clear_query(self):
        """Clear the query text box"""
        try:
            self.query_text.delete("1.0", tk.END)
        except Exception as e:
            log_exception("Failed to clear query", e)
    
    def show_settings(self):
        """Show settings dialog"""
        self.settings_manager.show_settings_dialog(self.root)
    
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
            log_exception("Failed to show about dialog", e)
    
    def view_schema(self):
        """View the database schema"""
        try:
            schema_info = self.db_manager.get_db_schema()

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
            error_msg = log_exception("Failed to get schema", e)
            messagebox.showerror("Error", error_msg)
    
    def _start_progress(self):
        """Start progress indicator for background tasks"""
        self.progress_bar.pack(fill=tk.X, pady=2)
        self.progress_bar.start(10)
    
    def _stop_progress(self):
        """Stop progress indicator"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
    
    def execute_query(self):
        """Process the natural language query and execute SQL asynchronously"""
        try:
            # Get the query text
            query = self.query_text.get("1.0", tk.END).strip()

            if not query:
                messagebox.showwarning("Input Error", "Please enter a query.")
                return

            if not self.ai_manager.api_key:
                messagebox.showwarning("API Key Required", "Please set your OpenAI API key in settings.")
                return

            # Update status with more detailed information
            self.status_var.set("Analyzing query and generating SQL...")
            self._start_progress()
            self.root.update_idletasks()

            # Run the query processing in background
            self.task_manager.add_task(
                func=self._process_query,
                args=[query],
                callback=self._query_completed
            )

        except Exception as e:
            self._stop_progress()
            error_msg = log_exception("Query execution error", e)
            messagebox.showerror("Error", f"{error_msg}")
            self.status_var.set("Error occurred")
    
    def _process_query(self, query):
        """Process the query in background"""
        # Get database schema for context
        schema_info = self.db_manager.get_db_schema()
        
        # Update progress status if possible
        if hasattr(self, 'status_var') and self.status_var:
            self.root.after(0, lambda: self.status_var.set("Generating SQL with AI..."))

        # Generate SQL using the selected model
        sql_query = self.ai_manager.generate_sql(query, schema_info)
        
        # Update progress status
        if hasattr(self, 'status_var') and self.status_var:
            self.root.after(0, lambda: self.status_var.set("Validating and executing SQL..."))

        # Fix ambiguous column references in the query
        sql_query = self.db_manager.fix_ambiguous_columns(sql_query)
        
        # Validate SQL
        is_valid, error_message = self.db_manager.validate_sql(sql_query)
        if not is_valid:
            raise Exception(error_message)

        # Execute the query
        df = self.db_manager.execute_sql(sql_query)
        
        # Update progress status
        if hasattr(self, 'status_var') and self.status_var:
            self.root.after(0, lambda: self.status_var.set("Generating summary and visualizations..."))
        
        # Generate summary
        summary = self.ai_manager.generate_summary(query, sql_query, df)
        
        # Return all results for UI update
        return {
            "query": query,
            "sql_query": sql_query,
            "dataframe": df,
            "summary": summary
        }
    
    def _query_completed(self, task):
        """Callback when query is completed"""
        # Stop the progress indicator
        self.root.after(0, self._stop_progress)
        
        if task.status.value == "completed":
            # Update UI with results
            result = task.result
            
            # Store current results for chart pop-out functionality
            self.current_results = result["dataframe"]
            
            # Update SQL text
            self.root.after(0, lambda: self.sql_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.sql_text.insert(tk.END, result["sql_query"]))
            
            # Display dataframe
            self.root.after(0, lambda: self.display_results(result["dataframe"]))
            
            # Generate chart - pass the original query for context
            self.root.after(0, lambda: self.vis_manager.generate_chart(
                result["dataframe"], 
                self.chart_frame,
                query=result["query"]
            ))
            
            # Update summary
            self.root.after(0, lambda: self.summary_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.summary_text.insert(tk.END, result["summary"]))
            
            # Update status
            self.root.after(0, lambda: self.status_var.set(
                f"Query completed: {len(result['dataframe'])} rows returned"
            ))
        else:
            # Show error
            self.root.after(0, lambda: self.status_var.set("Error occurred"))
            if task.error:
                self.root.after(0, lambda: messagebox.showerror("Query Error", task.error))
    
    def open_chart_in_new_window(self):
        """Open the current chart in a separate window"""
        try:
            # Get current dataframe from results
            if not hasattr(self, 'current_results') or self.current_results is None or self.current_results.empty:
                from tkinter import messagebox
                messagebox.showinfo("No Data", "No chart data available. Run a query first.")
                return
                
            # Get the current query
            query = self.query_text.get("1.0", tk.END).strip()
            
            # Open the chart in a new window
            self.vis_manager.open_chart_in_new_window(
                self.current_results, 
                query=query,
                parent=self.root
            )
        except Exception as e:
            error_msg = log_exception("Failed to open chart in new window", e)
            from tkinter import messagebox
            messagebox.showerror("Error", error_msg)
