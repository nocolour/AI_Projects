import os
import json
import logging
import traceback
import re
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import pandas as pd
from openai import OpenAI
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg for server-side plotting
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from functools import wraps
from logging.handlers import RotatingFileHandler

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging with rotating file handlers
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)  # Create logs directory if it doesn't exist
log_filename = f"{log_dir}/error.log"
request_log_filename = f"{log_dir}/requests.log"

# Configure main logger with rotating file handler
main_handler = RotatingFileHandler(
    log_filename, 
    maxBytes=10485760,  # 10MB
    backupCount=10
)
main_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(main_handler)

# Create a separate logger for requests with rotating file handler
request_logger = logging.getLogger('request_logger')
request_logger.setLevel(logging.INFO)
request_handler = RotatingFileHandler(
    request_log_filename,
    maxBytes=10485760,  # 10MB
    backupCount=10
)
request_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
request_logger.addHandler(request_handler)

# SQL commands blacklist for security
SQL_BLACKLIST = [
    "DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "CREATE", "RENAME", "REPLACE", "GRANT", "REVOKE"
]

# Global database connection pool
db_pool = None

# Create a simple in-memory cache
cache = {}

# Request logging middleware
@app.before_request
def log_request_info():
    request_logger.info(f"Request: {request.method} {request.path} - Client: {request.remote_addr}")
    if request.is_json:
        sanitized_data = request.json.copy() if request.json else {}
        if 'password' in sanitized_data:
            sanitized_data['password'] = '******'
        if 'openai_api_key' in sanitized_data:
            sanitized_data['openai_api_key'] = '******'
        request_logger.debug(f"Request JSON: {sanitized_data}")

@app.after_request
def log_response_info(response):
    request_logger.info(f"Response: {response.status_code} - {response.content_length} bytes")
    return response

# Cache decorator
def cache_result(expiry=300):  # Default cache expiry of 300 seconds (5 minutes)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < expiry:
                    return result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator

# Error handling decorator
# NOTE: Do NOT pass 'proxies' to OpenAI(). Proxy support is handled via environment variables (HTTP_PROXY/HTTPS_PROXY) only.
def handle_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except mysql.connector.Error as e:
            error_msg = f"Database error: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": error_msg, "error_type": "database"}), 500
        except openai.RateLimitError as e:
            error_msg = "OpenAI API rate limit exceeded. Please try again later."
            logging.error(f"{error_msg}: {str(e)}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": error_msg, "error_type": "rate_limit"}), 429
        except openai.APIConnectionError as e:
            error_msg = "Connection to OpenAI API failed. Please check your internet connection."
            logging.error(f"{error_msg}: {str(e)}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": error_msg, "error_type": "connection"}), 503
        except openai.APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": error_msg, "error_type": "api"}), 500
        except openai.AuthenticationError as e:
            error_msg = "OpenAI API authentication failed. Please check your API key."
            logging.error(f"{error_msg}: {str(e)}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": error_msg, "error_type": "authentication"}), 401
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": error_msg, "error_type": "general"}), 500
    return decorated_function

# Initialize database connection pool
def initialize_db_pool(db_config, pool_size=5):
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="nl2sql_pool",
            pool_size=pool_size,
            **db_config
        )
        logging.info(f"Database connection pool initialized with size {pool_size}")
        return True
    except mysql.connector.Error as e:
        error_msg = f"Failed to initialize connection pool: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return False

# Get connection from pool
def get_db_connection(db_config=None, max_retries=3, retry_delay=1):
    global db_pool
    if db_config:
        retries = 0
        last_error = None
        while retries < max_retries:
            try:
                connection = mysql.connector.connect(**db_config)
                return connection
            except mysql.connector.Error as e:
                last_error = e
                retries += 1
                logging.warning(f"Database connection attempt {retries} failed: {str(e)}")
                if retries < max_retries:
                    time.sleep(retry_delay)
        error_msg = f"Failed to connect to database after {max_retries} attempts: {str(last_error)}"
        logging.error(error_msg)
        raise mysql.connector.Error(error_msg)
    else:
        if db_pool is None:
            if not initialize_db_pool(config["database"]):
                raise mysql.connector.Error("Database pool is not initialized")
        retries = 0
        last_error = None
        while retries < max_retries:
            try:
                connection = db_pool.get_connection()
                return connection
            except mysql.connector.Error as e:
                last_error = e
                retries += 1
                logging.warning(f"Database pool connection attempt {retries} failed: {str(e)}")
                if retries < max_retries:
                    time.sleep(retry_delay)
        error_msg = f"Failed to get connection from pool after {max_retries} attempts: {str(last_error)}"
        logging.error(error_msg)
        raise mysql.connector.Error(error_msg)

# Load configuration from file and environment variables
def load_config():
    try:
        config_file = "../nl2sql_config.json"
        config_data = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        if os.getenv("DB_HOST"):
            if "database" not in config_data:
                config_data["database"] = {}
            config_data["database"]["host"] = os.getenv("DB_HOST")
        if os.getenv("DB_USER"):
            if "database" not in config_data:
                config_data["database"] = {}
            config_data["database"]["user"] = os.getenv("DB_USER")
        if os.getenv("DB_PASSWORD"):
            if "database" not in config_data:
                config_data["database"] = {}
            config_data["database"]["password"] = os.getenv("DB_PASSWORD")
        if os.getenv("DB_NAME"):
            if "database" not in config_data:
                config_data["database"] = {}
            config_data["database"]["database"] = os.getenv("DB_NAME")
        if os.getenv("DB_PORT"):
            if "database" not in config_data:
                config_data["database"] = {}
            config_data["database"]["port"] = int(os.getenv("DB_PORT", "3306"))
        if os.getenv("OPENAI_API_KEY"):
            config_data["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("AI_MODEL"):
            config_data["ai_model"] = os.getenv("AI_MODEL")
        defaults = {
            "database": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "",
                "port": 3306
            },
            "openai_api_key": "",
            "ai_model": "gpt-4o-mini"
        }
        for key, value in defaults.items():
            if key not in config_data:
                config_data[key] = value
            elif isinstance(value, dict) and isinstance(config_data[key], dict):
                for subkey, subvalue in value.items():
                    if subkey not in config_data[key]:
                        config_data[key][subkey] = subvalue
        return config_data
    except Exception as e:
        logging.error(f"Failed to load configuration: {str(e)}\n{traceback.format_exc()}")
        return {
            "database": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "",
                "port": 3306
            },
            "openai_api_key": "",
            "ai_model": "gpt-4o-mini"
        }

# Global configuration
config = load_config()

# Initialize the connection pool after loading config
if "database" in config and config["database"]["host"] and config["database"]["database"]:
    initialize_db_pool(config["database"])

@app.route('/api/config', methods=['GET'])
@handle_exceptions
def get_config():
    global config
    safe_config = {
        "database": {
            "host": config["database"]["host"],
            "user": config["database"]["user"],
            "database": config["database"]["database"],
            "port": config["database"]["port"]
        },
        "ai_model": config["ai_model"]
    }
    return jsonify(safe_config)

@app.route('/api/config', methods=['POST'])
@handle_exceptions
def update_config():
    global config, db_pool
    new_config = request.json
    if not new_config or not isinstance(new_config, dict):
        return jsonify({"status": "error", "message": "Invalid configuration format"}), 400
    try:
        if "database" in new_config:
            config["database"].update(new_config["database"])
        if "openai_api_key" in new_config:
            config["openai_api_key"] = new_config["openai_api_key"]
        if "ai_model" in new_config:
            config["ai_model"] = new_config["ai_model"]
        with open("../nl2sql_config.json", "w") as f:
            json.dump(config, f, indent=4)
        if "database" in new_config:
            db_pool = None
            initialize_db_pool(config["database"])
        return jsonify({"status": "success", "message": "Configuration updated successfully"})
    except Exception as e:
        error_msg = f"Failed to update configuration: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/api/test-connection', methods=['POST'])
@handle_exceptions
def test_connection():
    db_config = request.json
    if not db_config or not isinstance(db_config, dict):
        return jsonify({"status": "error", "message": "Invalid database configuration"}), 400
    required_fields = ["host", "user", "password", "database"]
    missing_fields = [field for field in required_fields if field not in db_config]
    if missing_fields:
        return jsonify({
            "status": "error", 
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    try:
        connection = get_db_connection(db_config)
        connection.close()
        return jsonify({"status": "success", "message": "Database connection successful"})
    except Exception as e:
        raise

@app.route('/api/schema', methods=['GET'])
@handle_exceptions
@cache_result(expiry=3600)  # Cache schema for 1 hour
def get_schema():
    try:
        db_config = config["database"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        schema_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            column_info = []
            for col in columns:
                col_name = col[0]
                col_type = col[1]
                column_info.append(f"{col_name} ({col_type})")
            schema_info.append({
                "table": table_name,
                "columns": column_info
            })
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "schema": schema_info})
    except Exception as e:
        error_msg = f"Failed to get database schema: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": error_msg}), 500

def validate_sql(sql_query):
    sql_upper = sql_query.upper()
    if not sql_query.strip():
        return False, "SQL query is empty"
    for cmd in SQL_BLACKLIST:
        pattern = fr'\b{cmd}\b'
        if re.search(pattern, sql_upper):
            if not re.search(fr"['\"][^'\"]*{cmd}[^'\"]*['\"]", sql_query, re.IGNORECASE):
                return False, f"For security reasons, {cmd} commands are not allowed."
    if not (sql_upper.strip().startswith("SELECT") or sql_upper.strip().startswith("SHOW")):
        return False, "Only SELECT and SHOW queries are allowed for security reasons."
    if ";" in sql_query[:-1]:
        return False, "Multiple SQL statements are not allowed."
    injection_patterns = [
        r"--",                     
        r"/\*.*?\*/",             
        r";\s*[a-zA-Z]",          
        r"UNION\s+ALL\s+SELECT",  
        r"OR\s+['\"]\s*['\"]\s*=\s*['\"]\s*['\"]\s*--", 
        r"OR\s+[0-9]\s*=\s*[0-9]"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, sql_query, re.IGNORECASE):
            return False, "Potential SQL injection detected."
    return True, ""

@app.route('/api/execute-query', methods=['POST'])
@handle_exceptions
def execute_query():
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid request format"}), 400
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    if not config["openai_api_key"]:
        return jsonify({"status": "error", "message": "OpenAI API key not configured"}), 400
    start_time = time.time()
    try:
        db_config = config["database"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        schema_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            column_info = []
            for col in columns:
                col_name = col[0]
                col_type = col[1]
                column_info.append(f"{col_name} ({col_type})")
            schema_info.append(f"Table: {table_name}\nColumns: {', '.join(column_info)}")
        cursor.close()
        conn.close()
        schema_text = "\n".join(schema_info)
        sql_query, error = generate_sql(query, schema_text, config["ai_model"], config["openai_api_key"])
        if error:
            return jsonify({"status": "error", "message": error}), 500
        sql_query = fix_ambiguous_columns(sql_query, db_config)
        is_valid, error_msg = validate_sql(sql_query)
        if not is_valid:
            return jsonify({"status": "error", "message": error_msg}), 400
        conn = get_db_connection()
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        table_data = {
            "columns": df.columns.tolist(),
            "data": df.values.tolist()
        }
        chart_data, chart_error = generate_ai_chart(query, df, config["ai_model"], config["openai_api_key"])
        summary = generate_summary(query, sql_query, df, config["ai_model"], config["openai_api_key"])
        response = {
            "status": "success",
            "sql_query": sql_query,
            "table_data": table_data,
            "chart_data": chart_data,
            "summary": summary,
            "row_count": len(df)
        }
        execution_time = time.time() - start_time
        return jsonify(response)
    except Exception as e:
        raise

@app.route('/api/examples', methods=['GET'])
@handle_exceptions
@cache_result(expiry=86400)  # Cache examples for 24 hours
def get_examples():
    examples = [
        "Show all customers from the USA",
        "What are the top 5 products by sales?",
        "List all employees hired in 2022",
        "Show me the total revenue by month",
        "Which customers have placed more than 10 orders?",
        "Show all tables in the database",
        "Display the schema for the customers table"
    ]
    return jsonify({"status": "success", "examples": examples})

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        api_key_status = "configured" if config["openai_api_key"] else "not configured"
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "openai_api": api_key_status,
            "time": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "time": datetime.now().isoformat()
        }), 500

def clean_cache():
    current_time = time.time()
    expired_keys = [k for k, (_, timestamp) in cache.items() if current_time - timestamp > 86400]
    for key in expired_keys:
        del cache[key]

def generate_sql(query, schema_text, model, api_key):
    """
    Generate SQL from natural language query using OpenAI API
    
    Args:
        query: Natural language query
        schema_text: Database schema information
        model: OpenAI model to use
        api_key: OpenAI API key
        
    Returns:
        tuple: (generated_sql, error_message)
    """
    try:
        # Initialize OpenAI client
        # Do NOT pass 'proxies' argument. Proxy support is handled via environment variables (HTTP_PROXY/HTTPS_PROXY).
        client = OpenAI(api_key=api_key)
        
        system_prompt = f"""You are an SQL expert. Convert the natural language query to a valid MySQL SQL query.
        Respond ONLY with the SQL query itself, no explanations or markdown formatting.
        
        Database Schema:
        {schema_text}
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Remove any markdown code block formatting if present
        sql_query = re.sub(r'^```sql\s*|\s*```$', '', sql_query, flags=re.MULTILINE).strip()
        
        return sql_query, None
    except TypeError as e:
        # Catch the specific error about 'proxies' argument
        if "proxies" in str(e):
            error_msg = (
                "Failed to generate SQL: The OpenAI client received an unexpected 'proxies' argument. "
                "Please ensure you are using the latest OpenAI Python SDK and do not pass 'proxies' to OpenAI(). "
                "Proxy support should be configured via environment variables (HTTP_PROXY/HTTPS_PROXY) only."
            )
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return "", error_msg
        else:
            error_msg = f"Failed to generate SQL: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return "", error_msg
    except Exception as e:
        error_msg = f"Failed to generate SQL: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return "", error_msg

def fix_ambiguous_columns(sql_query, db_config):
    """
    Fix ambiguous column references in SQL query by adding table prefixes
    
    Args:
        sql_query: SQL query to fix
        db_config: Database configuration
        
    Returns:
        str: Fixed SQL query
    """
    try:
        # This is a simplified implementation - for a complete solution,
        # you'd need to parse the SQL and resolve ambiguous columns
        conn = get_db_connection(db_config)
        cursor = conn.cursor()
        
        # Get all tables in the query
        tables_in_query = re.findall(r'FROM\s+(\w+)|JOIN\s+(\w+)', sql_query, re.IGNORECASE)
        tables = []
        for from_table, join_table in tables_in_query:
            if from_table:
                tables.append(from_table)
            if join_table:
                tables.append(join_table)
                
        # Get columns for each table
        table_columns = {}
        for table in tables:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = [col[0] for col in cursor.fetchall()]
            table_columns[table] = columns
            
        # Find potentially ambiguous columns (columns with the same name in different tables)
        all_columns = []
        for columns in table_columns.values():
            all_columns.extend(columns)
            
        ambiguous_columns = [col for col in all_columns if all_columns.count(col) > 1]
        
        # Replace ambiguous column references with qualified names
        for col in ambiguous_columns:
            # This is a simplified approach - a real implementation would need to be more sophisticated
            for table in table_columns:
                if col in table_columns[table]:
                    pattern = r'(SELECT|WHERE|ORDER BY|GROUP BY|HAVING)\s+([^,]*\s+|)' + col + r'\b'
                    replacement = r'\1\2' + f"{table}.{col}"
                    sql_query = re.sub(pattern, replacement, sql_query, flags=re.IGNORECASE)
        
        cursor.close()
        conn.close()
        return sql_query
    except Exception as e:
        logging.warning(f"Could not fix ambiguous columns: {str(e)}")
        return sql_query  # Return original query if fixing fails

def generate_chart(df):
    """
    Generate chart visualization from DataFrame
    
    Args:
        df: Pandas DataFrame with query results
        
    Returns:
        tuple: (chart_data_base64, error_message)
    """
    try:
        if df.empty or len(df.columns) < 2:
            return None, "Not enough data for chart visualization"
            
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) == 0:
            return None, "No numeric columns for visualization"
            
        plt.figure(figsize=(10, 6))
        
        # Choose chart type based on data
        if len(df) > 15:  # If many rows, use a line chart
            if len(numeric_cols) >= 2:
                # Line chart
                plt.plot(df.iloc[:, 0], df[numeric_cols[0]], marker='o')
                plt.xlabel(df.columns[0])
                plt.ylabel(numeric_cols[0])
                plt.title(f"{numeric_cols[0]} over {df.columns[0]}")
            else:
                # Bar chart with limited categories
                top_n = df.head(15)  # Limit to 15 items
                top_n.plot.bar(x=df.columns[0], y=numeric_cols[0], ax=plt.gca())
                plt.xticks(rotation=45)
                plt.tight_layout()
        else:
            # Bar chart
            df.plot.bar(x=df.columns[0], y=numeric_cols[0], ax=plt.gca())
            plt.xticks(rotation=45)
            plt.tight_layout()
            
        # Convert plot to base64 for embedding in HTML
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}", None
    except Exception as e:
        error_msg = f"Chart generation failed: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return None, error_msg

def generate_ai_chart(query, df, model, api_key):
    """
    Generate chart configuration using OpenAI based on query and result data
    
    Args:
        query: Original natural language query
        df: Pandas DataFrame with query results
        model: OpenAI model to use
        api_key: OpenAI API key
        
    Returns:
        tuple: (chart_config, error_message)
    """
    try:
        if df.empty or api_key == "":
            # Fall back to normal chart generation if no data or no API key
            return generate_chart(df)
            
        # Convert the dataframe to a JSON-serializable structure
        df_structure = {
            "columns": df.columns.tolist(),
            "sample_data": df.head(5).values.tolist(),
            "row_count": len(df),
            "columns_data_types": {col: str(df[col].dtype) for col in df.columns}
        }
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        system_prompt = """You are a data visualization expert. 
        Given a query and its resulting dataset, create the best Chart.js (version 4) visualization.
        Return ONLY a valid Chart.js configuration object in JSON format.
        
        CHART TYPE GUIDELINES:
        - Time series data → line charts
        - Categorical comparisons → bar charts (horizontal for many categories)
        - Part-to-whole relationships → pie/doughnut charts (only if ≤7 categories)
        - Distributions → histogram or box plot
        - Correlations → scatter plots
        - Geographic data → choose appropriate non-map visualization
        
        DATA MAPPING RULES:
        - First identify which columns should be labels (x-axis/categories) and which should be datasets
        - For dates and text columns: typically good candidates for labels/categories
        - For numeric columns: typically good for datasets/values
        - Limit to 10-15 data points for readability (sample if more)
        - Group less significant values as "Other" if many categories
        
        CHART CONFIGURATION:
        - Must include: type, data (with labels and datasets), and options
        - Use appropriate scales configuration (linear, logarithmic, etc.)
        - Add meaningful title based on the query
        - Include proper axis labels based on column names
        - Configure proper tooltips for better data exploration
        - Use colorblind-friendly palette for accessibility
        
        Your response must be a valid Chart.js configuration object that can be directly passed to new Chart(ctx, config).
        Do not include any explanations, just the JSON configuration.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Original query: {query}\n\nData structure: {json.dumps(df_structure)}"}
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        chart_config = response.choices[0].message.content
        
        try:
            # Validate that the response is valid JSON
            chart_config_json = json.loads(chart_config)
            
            # Ensure the configuration has the required Chart.js structure
            if not isinstance(chart_config_json, dict) or "type" not in chart_config_json or "data" not in chart_config_json:
                # Add minimal structure if missing
                if "datasets" in chart_config_json and "labels" in chart_config_json:
                    # If we just got the data part, wrap it in proper structure
                    chart_config_json = {
                        "type": "bar",  # Default fallback
                        "data": chart_config_json,
                        "options": {
                            "responsive": True,
                            "plugins": {
                                "title": {
                                    "display": True,
                                    "text": f"Results for: {query[:50]}{'...' if len(query) > 50 else ''}"
                                }
                            }
                        }
                    }
                elif not isinstance(chart_config_json, dict):
                    # If completely wrong format, fall back to generate_chart
                    logging.warning(f"AI returned invalid chart structure")
                    return generate_chart(df)
            
            # Ensure datasets array exists and has proper structure
            if "data" in chart_config_json:
                if "datasets" not in chart_config_json["data"]:
                    chart_config_json["data"]["datasets"] = []
                    
                # If labels are missing but we have column names, use first column as labels
                if "labels" not in chart_config_json["data"] and df.columns.size > 0:
                    chart_config_json["data"]["labels"] = df.iloc[:, 0].astype(str).tolist()[:15]  # Limit to 15 items
                    
                # Ensure we have at least one dataset if missing
                if not chart_config_json["data"]["datasets"] and df.columns.size > 1:
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        chart_config_json["data"]["datasets"] = [{
                            "label": numeric_cols[0],
                            "data": df[numeric_cols[0]].tolist()[:15],  # Limit to 15 items
                            "backgroundColor": "rgba(75, 192, 192, 0.5)"
                        }]
            
            logging.info("Successfully generated AI chart configuration")
            return chart_config_json, None
        except json.JSONDecodeError as je:
            # If not valid JSON, fall back to normal chart generation
            logging.warning(f"AI returned invalid chart JSON: {chart_config[:100]}...")
            return generate_chart(df)
            
    except Exception as e:
        error_msg = f"AI chart generation failed: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        # Fall back to normal chart generation
        return generate_chart(df)

def generate_summary(query, sql_query, df, model, api_key):
    """
    Generate a natural language summary of query results
    
    Args:
        query: Original natural language query
        sql_query: Generated SQL query
        df: Pandas DataFrame with query results
        model: OpenAI model to use
        api_key: OpenAI API key
        
    Returns:
        str: Summary text
    """
    try:
        if df.empty:
            return "No data found for this query."
            
        # Create a summary of the data
        data_summary = f"Total rows: {len(df)}\n"
        
        # Add statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            try:
                data_summary += f"\n{col} statistics:\n"
                data_summary += f"- Min: {df[col].min()}\n"
                data_summary += f"- Max: {df[col].max()}\n"
                data_summary += f"- Avg: {df[col].mean():.2f}\n"
            except:
                pass
                
        # For small result sets, provide a brief description
        if len(df) <= 50 and api_key:
            # Use OpenAI to generate a natural language summary
            client = OpenAI(api_key=api_key)
            
            # Create a sample of the data for the AI to summarize
            sample_rows = df.head(10).to_string()
            
            system_prompt = """You are a data analyst. Provide a brief summary of the query results.
            Focus on key insights, patterns, and notable values. Keep your summary concise (2-3 sentences).
            """
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Original Query: {query}\n\nQuery Results (sample of {len(df)} total rows):\n{sample_rows}"}
                    ],
                    temperature=0.5,
                    max_tokens=150
                )
                ai_summary = response.choices[0].message.content.strip()
                return f"{ai_summary}\n\n{data_summary}"
            except Exception as inner_e:
                logging.error(f"Failed to generate AI summary: {str(inner_e)}")
                return data_summary
        else:
            return data_summary
    except Exception as e:
        logging.error(f"Failed to generate summary: {str(e)}\n{traceback.format_exc()}")
        return "Could not generate summary for this query."

if __name__ == '__main__':
    logging.info("Starting Flask app")
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    if not debug_mode:
        logging.getLogger().setLevel(logging.INFO)
    clean_cache()
    app.run(debug=debug_mode, port=5000, host='0.0.0.0')