import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ...utils import log_exception

def create_pie_chart(df, ax, recommendation):
    """Create a pie chart"""
    x_col = recommendation.get("x_axis")
    y_cols = recommendation.get("y_axis", [])
    
    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
        
    # For pie chart, if y_cols is empty, use counts of x_col categories
    if not y_cols:
        # Use value counts
        counts = df[x_col].value_counts()
        labels = counts.index
        sizes = counts.values
    else:
        # Use first y column for values and x_col for labels
        y_col = y_cols[0]
        if y_col not in df.columns:
            return
            
        # Group by x_col and sum y_col values
        grouped = df.groupby(x_col)[y_col].sum()
        labels = grouped.index
        sizes = grouped.values
    
    # Limit to top 8 categories for readability, group the rest as "Other"
    if len(labels) > 8:
        top_sizes = sorted(sizes, reverse=True)[:7]
        threshold = top_sizes[-1]
        
        mask_top = sizes >= threshold
        
        top_labels = labels[mask_top]
        top_sizes = sizes[mask_top]
        
        other_size = sum(sizes[~mask_top])
        
        labels = np.append(top_labels, ['Other'])
        sizes = np.append(top_sizes, other_size)
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=90,
        shadow=False,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1},
        textprops={'fontsize': 9}
    )
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    
    # Make percentage labels more readable
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
