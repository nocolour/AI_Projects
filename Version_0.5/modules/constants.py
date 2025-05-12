"""Constants used throughout the application"""

# Application info
APP_NAME = "Natural Language to SQL Query System"
APP_VERSION = "1.0.0"

# Default settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 3306
DEFAULT_MODEL = "gpt-4o-mini"

# Available AI models
AI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"]

# SQL security
SQL_BLACKLIST = [
    "DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "CREATE", "RENAME", "REPLACE", "GRANT", "REVOKE"
]

# Example queries
EXAMPLE_QUERIES = [
    "Show all customers from the USA",
    "What are the top 5 products by sales?",
    "List all employees hired in 2022",
    "Show me the total revenue by month",
    "Which customers have placed more than 10 orders?",
    "Show all tables in the database",
    "Display the schema for the customers table"
]

# UI dimensions
WINDOW_SIZE = "1200x800"
MIN_WINDOW_SIZE = (800, 600)

# Chart settings
CHART_FIGSIZE = (10, 6)
CHART_MARGINS = {
    "default": {"left": 0.1, "right": 0.9, "top": 0.9, "bottom": 0.15},
    "with_explanation": {"left": 0.1, "right": 0.9, "top": 0.9, "bottom": 0.2},
    "with_legend": {"left": 0.1, "right": 0.8, "top": 0.9, "bottom": 0.15},
    "with_both": {"left": 0.1, "right": 0.8, "top": 0.9, "bottom": 0.2}
}
MAX_CHART_COLUMNS = 3
