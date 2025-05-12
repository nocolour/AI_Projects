import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ...utils import log_exception

def create_radar_chart(df, fig, recommendation, comparison_colors):
    """Create a radar chart"""
    x_col = recommendation.get("x_axis")
    y_cols = recommendation.get("y_axis", [])
    
    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
        
    if not y_cols:
        y_cols = [col for col in df.select_dtypes(include=['number']).columns if col != x_col]
    else:
        y_cols = [col for col in y_cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
        
    # Need at least 3 numeric columns and 1 categorical column for radar chart
    if not x_col or len(y_cols) < 3:
        # Use a polar projection for the figure
        ax = fig.add_subplot(111, projection='polar')
        ax.text(0, 0, "Not enough data for radar chart\nNeed at least 3 metrics", 
              ha='center', va='center', fontsize=12)
        return
        
    # Limit to 5 categories and 5 metrics for readability
    categories = df[x_col].value_counts().nlargest(5).index
    filtered_df = df[df[x_col].isin(categories)]
    y_cols = y_cols[:5]
    
    # Create a new polar axis
    ax = fig.add_subplot(111, projection='polar')
    
    # Number of variables
    N = len(y_cols)
    
    # What will be the angle of each axis in the plot (divide the plot / number of variables)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Normalize the data for each metric to 0-1 scale
    normalized_data = {}
    for col in y_cols:
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val > min_val:
            normalized_data[col] = (df[col] - min_val) / (max_val - min_val)
        else:
            normalized_data[col] = df[col] / df[col]  # All 1's
    
    # Plot each category
    for i, category in enumerate(categories):
        cat_data = filtered_df[filtered_df[x_col] == category]
        
        if len(cat_data) == 0:
            continue
            
        # Get normalized values for this category
        values = [normalized_data[col].loc[cat_data.index].mean() for col in y_cols]
        values += values[:1]  # Close the loop
        
        # Plot the category
        ax.plot(angles, values, linewidth=2, label=category, 
              color=comparison_colors[i % len(comparison_colors)])
        ax.fill(angles, values, alpha=0.1, 
              color=comparison_colors[i % len(comparison_colors)])
        
    # Set the labels for each axis
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(y_cols, fontsize=9)
    
    # Add legend
    ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # Add title
    fig.suptitle(f'Radar Chart Comparing {x_col} Categories', fontsize=12)
