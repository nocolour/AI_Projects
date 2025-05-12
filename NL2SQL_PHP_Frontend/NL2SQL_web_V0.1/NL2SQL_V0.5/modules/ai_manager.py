"""
AI Manager module
Handles interactions with OpenAI API for SQL generation and result summarization
"""

import openai
from typing import Optional, Dict, Any
import pandas as pd
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

            # Set up the prompt for AI model
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

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
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
            raise Exception(log_exception("Failed to generate SQL query", e))
    
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
