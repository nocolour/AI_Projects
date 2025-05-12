import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ...utils import log_exception

def create_heatmap_chart(df, ax, recommendation):
    """Create a heatmap chart"""
    x_col = recommendation.get("x_axis")
    y_cols = recommendation.get("y_axis", [])
    color_by = recommendation.get("color_by")
    
    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
        
    if not y_cols:
        y_cols = [col for col in df.select_dtypes(include=['number']).columns if col != x_col]
    else:
        y_cols = [col for col in y_cols if col in df.columns]
        
    # Need at least one numeric column for heatmap
    if not y_cols:
        return
        
    # If color_by is specified and valid, use it; otherwise use first y_col
    if color_by and color_by in df.columns and pd.api.types.is_numeric_dtype(df[color_by]):
        value_col = color_by
    else:
        value_col = y_cols[0]
        
    # For heatmap, we need to pivot the data
    # We need another categorical column to pivot
    categorical_cols = [col for col in df.columns 
                       if col != x_col and col not in y_cols and not pd.api.types.is_numeric_dtype(df[col])]
    
    if len(categorical_cols) > 0:
        pivot_col = categorical_cols[0]
        
        try:
            # Create pivot table
            pivot_data = df.pivot_table(
                index=x_col, 
                columns=pivot_col, 
                values=value_col,
                aggfunc='mean'
            )
            
            # Plot heatmap
            sns.heatmap(pivot_data, cmap='viridis', ax=ax, annot=True, fmt=".1f", 
                       linewidths=.5, cbar_kws={'label': value_col})
        except Exception as e:
            # Fallback to correlation heatmap if pivoting fails
            log_exception("Failed to create pivot heatmap, using correlation heatmap", e)
            create_correlation_heatmap(df, ax, y_cols)
    else:
        # Fallback to correlation heatmap if we don't have enough categorical columns
        create_correlation_heatmap(df, ax, y_cols)

def create_correlation_heatmap(df, ax, columns):
    """Create a correlation heatmap for numeric columns"""
    # Use only specified columns or all numeric columns
    if columns:
        numeric_df = df[columns]
    else:
        numeric_df = df.select_dtypes(include=['number'])
    
    # Calculate correlation matrix
    corr = numeric_df.corr()
    
    # Plot heatmap
    sns.heatmap(corr, cmap='coolwarm', ax=ax, annot=True, fmt=".2f", 
               linewidths=.5, vmin=-1, vmax=1, center=0,
               cbar_kws={'label': 'Correlation Coefficient'})
    
    ax.set_title('Correlation Matrix')
