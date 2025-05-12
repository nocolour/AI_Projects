import logging
import re
import pandas as pd
from sqlalchemy import create_engine, text, inspect, pool
from urllib.parse import quote_plus
from .utils import log_exception

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "",
            "port": 3306
        }
        
        # SQL commands blacklist for security
        self.sql_blacklist = [
            "DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
            "CREATE", "RENAME", "REPLACE", "GRANT", "REVOKE"
        ]
        
        self.schema_cache = {}  # Add cache for schema information
    
    def update_config(self, config):
        """Update database configuration and create new engine"""
        self.db_config = config
        self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine from current configuration with connection pooling"""
        try:
            # Only create engine if we have a database name
            if self.db_config.get("database"):
                # Properly escape username and password for URL
                safe_user = quote_plus(self.db_config['user'])
                safe_password = quote_plus(self.db_config['password'])
                
                connection_string = (
                    f"mysql+pymysql://{safe_user}:{safe_password}@"
                    f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
                )
                
                # Create engine with connection pool
                self.engine = create_engine(
                    connection_string,
                    pool_size=5,               # Default number of connections to keep open
                    max_overflow=10,           # Allow up to 10 more connections when needed
                    pool_timeout=30,           # Timeout waiting for connection (seconds)
                    pool_recycle=3600          # Recycle connections after 1 hour
                )
                
                logging.info("SQLAlchemy engine created successfully with connection pooling")
            else:
                self.engine = None
        except Exception as e:
            self.engine = None
            log_exception("Failed to create SQLAlchemy engine", e)
    
    def test_connection(self, host, user, password, database, port):
        """Test database connection with provided credentials"""
        try:
            # Properly escape username and password for URL
            safe_user = quote_plus(user)
            safe_password = quote_plus(password)
            
            # Create a test connection string
            connection_string = f"mysql+pymysql://{safe_user}:{safe_password}@{host}:{port}/{database}"
            test_engine = create_engine(connection_string)
            
            # Test the connection
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
    
    def execute_sql(self, sql_query):
        """Execute SQL query using SQLAlchemy engine and return pandas DataFrame"""
        try:
            if not self.engine:
                raise Exception("Database connection not configured")

            # For large result sets, use chunks
            if sql_query.upper().startswith("SELECT"):
                # Use chunks for large datasets to reduce memory usage
                chunk_size = 10000
                chunks = []
                
                # Execute query with chunking for large results
                for chunk in pd.read_sql_query(
                    sql=text(sql_query), 
                    con=self.engine, 
                    chunksize=chunk_size
                ):
                    chunks.append(chunk)
                
                # Combine chunks if needed or return first chunk if only one
                if not chunks:
                    return pd.DataFrame()
                elif len(chunks) == 1:
                    return chunks[0]
                else:
                    return pd.concat(chunks)
            else:
                # For non-SELECT queries (like SHOW)
                return pd.read_sql_query(sql=text(sql_query), con=self.engine)
        except Exception as e:
            raise Exception(log_exception("Failed to execute SQL query", e))
    
    def get_db_schema(self):
        """Get the database schema using SQLAlchemy with caching"""
        try:
            if not self.engine:
                raise Exception("Database connection not configured")
            
            # Return cached schema if available
            db_name = self.db_config.get("database")
            if db_name in self.schema_cache:
                return self.schema_cache[db_name]
                
            inspector = inspect(self.engine)
            schema_info = []
            
            # Get all table names
            tables = inspector.get_table_names()
            
            # Get columns for each table
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                column_info = []
                
                for column in columns:
                    col_name = column['name']
                    col_type = str(column['type'])
                    column_info.append(f"{col_name} ({col_type})")
                
                schema_info.append(f"Table: {table_name}\nColumns: {', '.join(column_info)}\n")
            
            # Cache the schema info
            self.schema_cache[db_name] = "\n".join(schema_info)
            return self.schema_cache[db_name]
        except Exception as e:
            raise Exception(log_exception("Failed to get database schema", e))
    
    def clear_schema_cache(self):
        """Clear the schema cache when database structure might have changed"""
        self.schema_cache = {}
    
    def validate_sql(self, sql_query):
        """Validate SQL for safety, return (is_valid, error_message)"""
        try:
            sql_upper = sql_query.upper()

            # Check for blacklisted commands
            for cmd in self.sql_blacklist:
                if cmd in sql_upper and not f"'{cmd}" in sql_upper and not f'"{cmd}' in sql_upper:
                    return False, f"For security reasons, {cmd} commands are not allowed."

            # Ensure the query is a SELECT or SHOW statement
            if not (sql_upper.strip().startswith("SELECT") or sql_upper.strip().startswith("SHOW")):
                return False, "Only SELECT and SHOW queries are allowed for security reasons."

            # Ensure no multiple statements (no semicolons except at the end)
            if ";" in sql_query[:-1]:
                return False, "Multiple SQL statements are not allowed."

            return True, ""
        except Exception as e:
            error_msg = log_exception("Failed to validate SQL", e)
            return False, error_msg
    
    def fix_ambiguous_columns(self, sql_query):
        """Fix ambiguous column references in the SQL query using SQLAlchemy"""
        try:
            # Check if the query has JOINs (indicating potential for ambiguity)
            if " JOIN " not in sql_query.upper() or not self.engine:
                return sql_query
            
            # Get an inspector for database introspection
            inspector = inspect(self.engine)
            
            # Extract table names from the query
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
                    # Get columns using SQLAlchemy inspector
                    columns = [col['name'] for col in inspector.get_columns(table)]
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
            
            return sql_query
        except Exception as e:
            # Log the error but return the original query to avoid blocking execution
            log_exception("Error fixing ambiguous columns", e)
            return sql_query
