import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ...utils import log_exception

def create_fallback_chart(df, ax):
    """Create a fallback chart when other chart types fail"""
    try:
        # Clear the axis
        ax.clear()
        
        # Simple fallback using a bar chart of the first few rows
        if len(df) > 0:
            # Get columns to plot
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            if len(numeric_cols) >= 1:
                # Take first numeric column
                y_col = numeric_cols[0]
                # Limit to first 15 rows for readability
                df_subset = df.head(15)
                
                # Use first non-numeric column as x if available, otherwise use row index
                non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
                if non_numeric_cols:
                    x_col = non_numeric_cols[0]
                    df_subset.plot(kind='bar', x=x_col, y=y_col, ax=ax, legend=False)
                    ax.set_xticklabels(df_subset[x_col], rotation=45, ha='right')
                else:
                    # Use row numbers as x
                    ax.bar(range(len(df_subset)), df_subset[y_col])
                    ax.set_xticks(range(len(df_subset)))
                    ax.set_xticklabels(df_subset.index, rotation=45, ha='right')
                
                ax.set_ylabel(y_col)
                ax.set_title(f"Summary of {y_col}")
            else:
                # No numeric columns, show counts of first categorical column
                if len(df.columns) > 0:
                    col = df.columns[0]
                    value_counts = df[col].value_counts().head(10)  # Top 10 values
                    value_counts.plot(kind='bar', ax=ax)
                    ax.set_title(f"Top values in {col}")
                    ax.set_ylabel("Count")
                else:
                    ax.set_title("No data to visualize")
        else:
            ax.set_title("No data to visualize")
            
        # Add grid for readability
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
    except Exception as e:
        log_exception("Failed to create fallback chart", e)
        ax.clear()
        ax.text(0.5, 0.5, "Could not visualize data", 
                ha='center', va='center', transform=ax.transAxes)

def create_universal_fallback_chart(df, ax, original_chart_type):
    """Create a universally compatible chart based on data content"""
    # Determine what we're working with
    has_numeric = len(df.select_dtypes(include=['number']).columns) > 0
    has_categorical = len(df.select_dtypes(exclude=['number', 'datetime']).columns) > 0
    row_count = len(df)
    col_count = len(df.columns)
    
    try:
        # Display raw data if very small dataset
        if row_count <= 10 and col_count <= 10:
            ax.axis('off')  # Turn off axis
            # Create table with data
            table_data = df.values
            table_cols = df.columns
            
            the_table = ax.table(
                cellText=table_data, 
                colLabels=table_cols,
                loc='center',
                cellLoc='center',
                colColours=['#f2f2f2'] * len(table_cols)
            )
            the_table.auto_set_font_size(False)
            the_table.set_fontsize(9)
            the_table.scale(1.2, 1.5)  # Adjust table size
            ax.set_title(f"Data Table ({row_count} rows, {col_count} columns)")
            return
            
        # Case: Categorical data only
        if not has_numeric and has_categorical:
            # Use the first categorical column
            cat_col = df.select_dtypes(exclude=['number', 'datetime']).columns[0]
            # Create count plot
            value_counts = df[cat_col].value_counts()
            
            # Limit to top 15 categories if too many
            if len(value_counts) > 15:
                value_counts = value_counts.nlargest(15)
                
            # Create horizontal bar for better readability with many categories
            bars = ax.barh(range(len(value_counts)), value_counts.values)
            ax.set_yticks(range(len(value_counts)))
            ax.set_yticklabels(value_counts.index)
            ax.set_xlabel('Count')
            ax.set_title(f'Frequency of {cat_col} Values')
            
            # Add count labels
            for i, v in enumerate(value_counts.values):
                ax.text(v + 0.1, i, str(v), ha='left', va='center')
            
            return
            
        # Case: Numeric data available
        if has_numeric:
            # Get the first numeric column
            num_col = df.select_dtypes(include=['number']).columns[0]
            
            # Different approaches based on data size
            if row_count > 50:
                # For larger datasets, histogram shows distribution better
                ax.hist(df[num_col].dropna(), bins=min(30, max(5, int(row_count/10))), 
                       alpha=0.7, color='steelblue', edgecolor='white')
                ax.set_xlabel(num_col)
                ax.set_ylabel('Frequency')
                ax.set_title(f'Distribution of {num_col}')
                
                # Add summary statistics
                mean = df[num_col].mean()
                median = df[num_col].median()
                ax.axvline(mean, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean:.2f}')
                ax.axvline(median, color='green', linestyle='dashed', linewidth=1, label=f'Median: {median:.2f}')
                ax.legend()
            else:
                # For smaller datasets, bar or line plots work better
                if has_categorical:
                    # If we have a categorical column, use it for x-axis
                    cat_col = df.select_dtypes(exclude=['number']).columns[0]
                    
                    # Sort by numeric value for better visualization
                    df_sorted = df.sort_values(by=num_col, ascending=False)
                    
                    # Limit to first 30 rows if needed
                    if len(df_sorted) > 30:
                        df_sorted = df_sorted.head(30)
                    
                    # Plot bar chart
                    bars = ax.bar(range(len(df_sorted)), df_sorted[num_col].values, color='skyblue')
                    ax.set_xticks(range(len(df_sorted)))
                    ax.set_xticklabels(df_sorted[cat_col].values, rotation=45, ha='right')
                    ax.set_ylabel(num_col)
                    ax.set_title(f'{num_col} by {cat_col}')
                    
                    # Add value labels on top of bars
                    for i, v in enumerate(df_sorted[num_col].values):
                        ax.text(i, v + 0.1, f'{v:.1f}', ha='center', fontsize=8)
                else:
                    # No categorical column, plot simple line
                    ax.plot(df[num_col].values, marker='o', linestyle='-', color='royalblue')
                    ax.set_xticks(range(len(df)))
                    ax.set_xticklabels(range(1, len(df) + 1))
                    ax.set_xlabel('Row Number')
                    ax.set_ylabel(num_col)
                    ax.set_title(f'Values of {num_col}')
                    
                    # Add grid for readability
                    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
            
            return
            
    except Exception as e:
        log_exception(f"Failed to create universal fallback chart for {original_chart_type}", e)
    
    # Worst case: Can't find appropriate visualization
    ax.text(0.5, 0.5, "Could not visualize this data", 
           ha='center', va='center', fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.45, "Try a different query with numeric or categorical data", 
           ha='center', va='center', fontsize=10, transform=ax.transAxes, 
           color='gray', style='italic')
