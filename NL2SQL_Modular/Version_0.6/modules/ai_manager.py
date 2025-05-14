"""
AI Manager module
Handles interactions with OpenAI API for SQL generation and result summarization
"""

import openai
from typing import Optional, Dict, Any, List
import pandas as pd
import json
import re
from .utils import log_exception
from .constants import DEFAULT_MODEL

class AIManager:
    """
    Manages interactions with AI services for natural language to SQL conversion
    and data summarization.
    """
    
    def __init__(self) -> None:
        """Initialize the AI manager with default settings"""
        self.api_key: str = ""
        self.model: str = DEFAULT_MODEL
        # Add context retention for better understanding
        self.query_history: List[Dict[str, str]] = []
        self.max_history = 5
    
    def update_config(self, api_key: str, model: str) -> None:
        """
        Update AI configuration with new API key and model
        
        Args:
            api_key: OpenAI API key
            model: AI model to use for queries
        """
        self.api_key = api_key
        self.model = model
    
    def generate_sql(self, query: str, schema_info: str) -> str:
        """
        Generate SQL from natural language using selected AI model
        
        Args:
            query: Natural language query
            schema_info: Database schema information
        
        Returns:
            A valid SQL query string
        """
        try:
            if not self.api_key:
                raise Exception("API key not configured")

            # Extract database structure for better context
            tables_and_columns = self._extract_schema_structure(schema_info)
            
            # Determine query type to provide better context
            query_type = self._determine_query_type(query)
            
            # Create few-shot examples based on query type
            examples = self._get_few_shot_examples(query_type, tables_and_columns)
            
            # Build query history context
            history_context = self._build_history_context()
                
            # Set up the enhanced prompt for AI model with few-shot examples
            prompt = f"""
            You are an advanced natural language to SQL converter with expertise in MySQL. Convert the following question into a precise, efficient SQL query.
            
            Database schema:
            {schema_info}
            
            Database structure:
            {json.dumps(tables_and_columns, indent=2)}
            
            {history_context}
            
            Question: {query}
            
            Identified query type: {query_type}
            
            {examples}
            
            Important guidelines:
            1. Only return the SQL query without any explanation or markdown formatting
            2. Do not use backticks or any other formatting
            3. Only use SELECT statements or SHOW statements for security
            4. Your response should be a valid SQL query that can be executed directly
            5. Keep it focused on answering the question with the most efficient query
            6. ALWAYS use fully qualified column names (table_name.column_name) in SELECT, JOIN, WHERE, GROUP BY, 
               and ORDER BY clauses when the query involves multiple tables
            7. Be particularly careful with JOIN operations to avoid ambiguous column references
            8. Use aliases for table names when appropriate to make the query more readable
            
            SQL Query:
            """

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL query generator that translates natural language to precise, efficient SQL queries. You have deep understanding of database structures and query optimization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more consistent output
                max_tokens=300
            )

            # Extract SQL query from response
            sql_query = response.choices[0].message.content.strip()

            # Validate and clean the SQL query
            sql_query = self._validate_and_clean_sql(sql_query)

            # Store successful query in history for context
            self._add_to_history(query, sql_query)

            return sql_query
            
        except Exception as e:
            raise Exception(log_exception("Failed to generate SQL query", e))
    
    def _extract_schema_structure(self, schema_info: str) -> Dict[str, List[str]]:
        """Extract tables and columns structure from schema information"""
        tables_and_columns = {}
        
        # Parse the schema info to extract tables and columns
        current_table = None
        for line in schema_info.split('\n'):
            if line.startswith('Table:'):
                current_table = line.replace('Table:', '').strip()
                tables_and_columns[current_table] = []
            elif current_table and 'Columns:' in line:
                columns_part = line.split('Columns:')[1].strip()
                columns = []
                # Extract column names from format: "name (type), name2 (type2), ..."
                for col_info in columns_part.split(','):
                    col_match = re.search(r'(\w+)\s*\(', col_info)
                    if col_match:
                        columns.append(col_match.group(1).strip())
                tables_and_columns[current_table] = columns
        
        return tables_and_columns
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of SQL query needed based on the question"""
        query_lower = query.lower()
        
        # Check for aggregations
        if any(term in query_lower for term in ['average', 'avg', 'mean', 'sum', 'total', 'count', 'how many']):
            return "AGGREGATION"
        
        # Check for comparisons
        if any(term in query_lower for term in ['compare', 'comparison', 'vs', 'versus', 'difference between']):
            return "COMPARISON"
        
        # Check for filtering
        if any(term in query_lower for term in ['where', 'which', 'find', 'search', 'filter']):
            return "FILTERING"
        
        # Check for sorting/ranking
        if any(term in query_lower for term in ['top', 'bottom', 'highest', 'lowest', 'best', 'worst', 'order', 'sort', 'rank']):
            return "SORTING"
        
        # Check for grouping
        if any(term in query_lower for term in ['group', 'by each', 'for each', 'categorize', 'segment']):
            return "GROUPING"
        
        # Check for time-based analysis
        if any(term in query_lower for term in ['trend', 'over time', 'by year', 'by month', 'by date', 'period']):
            return "TIME_ANALYSIS"
        
        # Check for listings
        if any(term in query_lower for term in ['show', 'list', 'display', 'all', 'view']):
            return "LISTING"
        
        # Default to general query
        return "GENERAL"
    
    def _get_few_shot_examples(self, query_type: str, schema_structure: Dict[str, List[str]]) -> str:
        """Provide few-shot examples based on query type and schema structure"""
        examples = "Here are a few examples of similar queries:\n\n"
        
        # Select table names for examples (up to 2)
        table_names = list(schema_structure.keys())
        if not table_names:
            return ""  # No tables available for examples
        
        example_tables = table_names[:min(2, len(table_names))]
        
        # Get some column names for each table
        example_columns = {}
        for table in example_tables:
            cols = schema_structure.get(table, [])
            example_columns[table] = cols[:min(3, len(cols))] if cols else []
        
        # Generate examples based on query type
        if query_type == "AGGREGATION":
            for table in example_tables:
                cols = example_columns[table]
                if len(cols) >= 2:
                    examples += f"Question: What is the average {cols[0]} for each {cols[1]} in {table}?\n"
                    examples += f"SQL: SELECT {table}.{cols[1]}, AVG({table}.{cols[0]}) FROM {table} GROUP BY {table}.{cols[1]};\n\n"
        
        elif query_type == "COMPARISON":
            if len(example_tables) >= 2:
                table1, table2 = example_tables[:2]
                cols1 = example_columns[table1]
                cols2 = example_columns[table2]
                if cols1 and cols2:
                    examples += f"Question: Compare the {cols1[0]} between {table1} and {table2}\n"
                    examples += f"SQL: SELECT {table1}.{cols1[0]}, {table2}.{cols2[0]} FROM {table1} JOIN {table2} ON {table1}.id = {table2}.{table1}_id;\n\n"
        
        elif query_type == "FILTERING":
            for table in example_tables:
                cols = example_columns[table]
                if len(cols) >= 2:
                    examples += f"Question: Find all {table} where {cols[0]} is greater than 100\n"
                    examples += f"SQL: SELECT * FROM {table} WHERE {table}.{cols[0]} > 100;\n\n"
        
        elif query_type == "SORTING":
            for table in example_tables:
                cols = example_columns[table]
                if len(cols) >= 2:
                    examples += f"Question: Show the top 5 {table} by {cols[0]}\n"
                    examples += f"SQL: SELECT * FROM {table} ORDER BY {table}.{cols[0]} DESC LIMIT 5;\n\n"
        
        elif query_type == "GROUPING":
            for table in example_tables:
                cols = example_columns[table]
                if len(cols) >= 2:
                    examples += f"Question: Group {table} by {cols[0]} and count them\n"
                    examples += f"SQL: SELECT {table}.{cols[0]}, COUNT(*) FROM {table} GROUP BY {table}.{cols[0]};\n\n"
        
        elif query_type == "TIME_ANALYSIS":
            date_columns = []
            for table, cols in example_columns.items():
                for col in cols:
                    if any(date_term in col.lower() for date_term in ['date', 'time', 'year', 'month', 'day']):
                        date_columns.append((table, col))
                        
            if date_columns:
                table, date_col = date_columns[0]
                examples += f"Question: Show the trend of records in {table} over time\n"
                examples += f"SQL: SELECT {table}.{date_col}, COUNT(*) FROM {table} GROUP BY {table}.{date_col} ORDER BY {table}.{date_col};\n\n"
        
        elif query_type == "LISTING":
            for table in example_tables:
                examples += f"Question: List all {table}\n"
                examples += f"SQL: SELECT * FROM {table};\n\n"
                
                cols = example_columns[table]
                if len(cols) >= 3:
                    examples += f"Question: Show {cols[0]} and {cols[1]} from {table}\n"
                    examples += f"SQL: SELECT {table}.{cols[0]}, {table}.{cols[1]} FROM {table};\n\n"
        
        else:  # GENERAL
            for table in example_tables:
                examples += f"Question: Get information about {table}\n"
                examples += f"SQL: SELECT * FROM {table} LIMIT 10;\n\n"
        
        return examples
    
    def _build_history_context(self) -> str:
        """Build context from query history for better understanding"""
        if not self.query_history:
            return ""
        
        context = "Here are some recent successful queries for context:\n\n"
        for item in self.query_history:
            context += f"Question: {item['query']}\n"
            context += f"SQL: {item['sql']}\n\n"
        
        return context
    
    def _add_to_history(self, query: str, sql: str) -> None:
        """Add a successful query to history"""
        self.query_history.append({"query": query, "sql": sql})
        # Keep history within size limit
        if len(self.query_history) > self.max_history:
            self.query_history.pop(0)
    
    def _validate_and_clean_sql(self, sql_query: str) -> str:
        """Validate and clean up the SQL query"""
        # Remove any markdown formatting
        sql_query = re.sub(r'```sql|```', '', sql_query)
        
        # Ensure query ends with semicolon
        if not sql_query.rstrip().endswith(';'):
            sql_query = sql_query.rstrip() + ';'
        
        # Check for multiple statements (security)
        if ";" in sql_query[:-1]:
            # Keep only the first statement
            sql_query = sql_query.split(";")[0] + ";"
        
        return sql_query

    def generate_summary(self, query: str, sql_query: str, df: pd.DataFrame) -> str:
        """
        Generate summary of the query results using selected AI model
        
        Args:
            query: Natural language query
            sql_query: SQL query string
            df: DataFrame containing query results
        
        Returns:
            A concise summary of the query results
        """
        try:
            if not self.api_key:
                raise Exception("API key not configured")
                
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
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
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
            error_msg = log_exception("Failed to generate summary", e)
            return f"Could not generate summary: {error_msg}"
