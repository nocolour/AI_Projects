import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ...utils import log_exception

def create_enhanced_bar_chart(df, ax, recommendation, comparison_colors):
    """Create an enhanced bar chart with better handling of comparisons and non-numeric data"""
    x_col = recommendation.get("x_axis")
    y_cols = recommendation.get("y_axis", [])
    color_by = recommendation.get("color_by")
    is_comparison = recommendation.get("is_comparison", False)
    orientation = recommendation.get("chart_orientation", "vertical")
    comparison_entities = recommendation.get("comparison_entities", [])
    
    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
    
    if not y_cols:
        # If no y columns specified, try to find numeric columns
        y_cols = [col for col in df.select_dtypes(include=['number']).columns if col != x_col]
        
        # If no numeric columns, create counts from categorical data
        if not y_cols and x_col:
            # Create a count-based visualization
            value_counts = df[x_col].value_counts()
            df_counts = value_counts.reset_index()
            df_counts.columns = [x_col, 'Count']
            
            # Use this new dataframe for visualization
            df = df_counts
            y_cols = ['Count']
    else:
        # Filter to ensure only existing columns are used
        y_cols = [col for col in y_cols if col in df.columns]
    
    # Can't create chart if we don't have valid x or y columns
    if not x_col or not y_cols:
        return
        
    # Check if y_cols contain numeric data
    numeric_y_cols = []
    for col in y_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_y_cols.append(col)
        else:
            # Try to convert non-numeric columns to numeric if possible
            try:
                df[f"{col}_numeric"] = pd.to_numeric(df[col], errors='coerce')
                if not df[f"{col}_numeric"].isna().all():  # If conversion produced some valid values
                    numeric_y_cols.append(f"{col}_numeric")
            except:
                pass
    
    # If we couldn't get any numeric y columns, fallback to counts
    if not numeric_y_cols and x_col:
        # Create a count-based visualization
        value_counts = df[x_col].value_counts()
        df = value_counts.reset_index()
        df.columns = [x_col, 'Count']
        numeric_y_cols = ['Count']
    
    # Still no numeric data?
    if not numeric_y_cols:
        return
        
    # Use our numeric columns for plotting
    y_cols = numeric_y_cols[:5]  # Limit to 5 columns
    
    # For horizontal orientation, we transpose x and y
    if orientation == "horizontal":
        # For horizontal bars, we use pandas plot with kind='barh'
        if len(y_cols) == 1:
            # Sort data for better visualization
            df_sorted = df.sort_values(by=y_cols[0])
            df_sorted.plot(kind='barh', x=x_col, y=y_cols[0], ax=ax, legend=False, colormap='viridis')
            ax.set_xlabel(y_cols[0])  # Use y_cols as x-axis label for horizontal
        else:
            # For multiple columns in horizontal mode
            df.plot(kind='barh', x=x_col, y=y_cols, ax=ax, colormap='viridis')
            ax.legend(title='Metrics', bbox_to_anchor=(1.05, 1), loc='upper left')
            
        # Format labels for better readability in horizontal mode
        ax.tick_params(axis='y', labelsize=9)  # Make y labels (categories) slightly smaller
        
    # Standard vertical orientation
    else:
        # Generate better colors for bars, especially for comparison
        if is_comparison and len(y_cols) == 1:
            # Enhanced comparison visualization
            categories = df[x_col].unique()
            bar_positions = np.arange(len(categories))
            
            # Use color palette for comparison bars
            colors = comparison_colors[:len(categories)]
            
            # Draw the bars with clear separation and nice colors
            for i, (category, color) in enumerate(zip(categories, colors)):
                value = df[df[x_col] == category][y_cols[0]].values[0]
                ax.bar(i, value, color=color, label=category, width=0.7)
            
            # Set x-tick labels and positions
            ax.set_xticks(bar_positions)
            ax.set_xticklabels(categories, rotation=45 if len(categories) > 4 else 0, ha='right' if len(categories) > 4 else 'center')
            
            # Add value labels on top of bars
            for i, v in enumerate(df[y_cols[0]]):
                ax.text(i, v + 0.1, f'{v:.1f}', ha='center', fontsize=9)
            
            ax.set_ylabel(y_cols[0])
            
        # For single y-column (not explicit comparison)
        elif len(y_cols) == 1:
            # Sort data for better visualization if less than 20 items
            if len(df) < 20:
                try:
                    df_sorted = df.sort_values(by=y_cols[0], ascending=False)
                    df_sorted.plot(kind='bar', x=x_col, y=y_cols[0], ax=ax, legend=False, colormap='viridis')
                except:
                    df.plot(kind='bar', x=x_col, y=y_cols[0], ax=ax, legend=False, colormap='viridis')
            else:
                df.plot(kind='bar', x=x_col, y=y_cols[0], ax=ax, legend=False, colormap='viridis')
            
            ax.set_ylabel(y_cols[0])
            
        # For multiple y-columns - grouped bar chart
        else:
            # Enhanced grouped bar chart for better comparison
            df.plot(kind='bar', x=x_col, y=y_cols, ax=ax, colormap='viridis')
    
    # Format x-axis labels if too many
    if orientation == "vertical" and len(df) > 6:
        plt.xticks(rotation=45, ha='right')
        ax.figure.subplots_adjust(bottom=0.2)

    # Add grid lines for easier value comparison
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
