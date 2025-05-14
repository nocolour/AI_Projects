import pandas as pd
import numpy as np
import re
from ..utils import log_exception

def preprocess_dataframe(df):
    """Preprocess dataframe to make it more suitable for visualization"""
    if df.empty:
        return df
        
    df_processed = df.copy()
    
    # Step 1: Handle missing values
    for col in df_processed.columns:
        # Replace missing values in numeric columns with 0
        if pd.api.types.is_numeric_dtype(df_processed[col]):
            df_processed[col] = df_processed[col].fillna(0)
        # Replace missing values in string columns with "N/A"
        elif pd.api.types.is_string_dtype(df_processed[col]) or pd.api.types.is_object_dtype(df_processed[col]):
            df_processed[col] = df_processed[col].fillna("N/A")
    
    # Step 2: Convert date-like string columns to datetime
    for col in df_processed.select_dtypes(include=['object']).columns:
        # Check if column might be a date
        try:
            # More comprehensive date pattern detection
            date_patterns = [
                r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'^\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'^\d{1,2}-[A-Za-z]{3}-\d{4}',  # D-MMM-YYYY
                r'^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}'  # D MMM YYYY
            ]
            
            is_date = False
            for pattern in date_patterns:
                if df_processed[col].astype(str).str.match(pattern).any():
                    is_date = True
                    break
                    
            if is_date:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
                
                # If column name doesn't indicate it's a date, add metadata
                if not any(term in col.lower() for term in ['date', 'time', 'year', 'month', 'day']):
                    # Store the fact that this is a date column in attributes
                    if not hasattr(df_processed, 'date_columns'):
                        df_processed.date_columns = []
                    df_processed.date_columns.append(col)
        except:
            pass  # Keep as string if operation fails
    
    # Step 3: Convert categorical string columns with numeric values to numeric when appropriate
    for col in df_processed.select_dtypes(include=['object']).columns:
        # Try to convert string columns that might contain numeric values
        try:
            # Check if the column contains what looks like numbers
            if df_processed[col].astype(str).str.match(r'^-?\d+\.?\d*$').all():
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
        except:
            pass
    
    # Step 4: Sort data if possible to identify trends
    # This is particularly useful for line charts with time series or numeric x-axis
    for col in df_processed.columns:
        if pd.api.types.is_datetime64_dtype(df_processed[col]) or 'date' in col.lower():
            try:
                df_processed = df_processed.sort_values(by=col)
                df_processed.attrs['sorted'] = True
                df_processed.attrs['sorted_by'] = col
                break  # Priority to date columns for sorting
            except:
                pass
    
    # If not already sorted by date, try to sort by a potential index column
    if 'sorted' not in df_processed.attrs:
        potential_id_cols = [col for col in df_processed.columns if 
                           any(term in col.lower() for term in ['id', 'index', 'key', 'no']) and
                           pd.api.types.is_numeric_dtype(df_processed[col])]
        if potential_id_cols:
            try:
                df_processed = df_processed.sort_values(by=potential_id_cols[0])
                df_processed.attrs['sorted'] = True
                df_processed.attrs['sorted_by'] = potential_id_cols[0]
            except:
                pass
    
    # Step 5: Limit number of rows for visualization performance
    max_rows = 100
    if len(df_processed) > max_rows:
        # If data is sorted, take first and last rows to preserve trends
        if 'sorted' in df_processed.attrs and df_processed.attrs['sorted']:
            rows_each_end = max_rows // 2
            df_processed = pd.concat([
                df_processed.head(rows_each_end),
                df_processed.tail(rows_each_end)
            ])
        else:
            df_processed = df_processed.head(max_rows)
    
    # Step 6: Add metadata about original dataset size
    df_processed.attrs['original_size'] = len(df)
    
    return df_processed
