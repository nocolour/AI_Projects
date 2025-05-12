import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ...utils import log_exception

def create_scatter_chart(df, ax, recommendation):
    """Create a scatter chart"""
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
        
    # Can't create chart if we don't have valid x or y columns
    if not x_col or not y_cols:
        return
        
    # Only use first y column for scatter plot
    y_col = y_cols[0]
    
    # Check if we should color points by another column
    if color_by and color_by in df.columns:
        scatter = ax.scatter(df[x_col], df[y_col], c=df[color_by], cmap='viridis', 
                           alpha=0.7, edgecolors='w', linewidths=0.5)
        # Add a colorbar
        plt.colorbar(scatter, ax=ax, label=color_by)
    else:
        ax.scatter(df[x_col], df[y_col], alpha=0.7, edgecolors='w', linewidths=0.5)
        
    # Set labels
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add trend line (linear regression)
    try:
        # Only if we have numerical data
        if (pd.api.types.is_numeric_dtype(df[x_col]) and 
            pd.api.types.is_numeric_dtype(df[y_col])):
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(df[x_col], df[y_col])
            x_range = np.linspace(df[x_col].min(), df[x_col].max(), 100)
            ax.plot(x_range, intercept + slope * x_range, 'r--', 
                  label=f'Trend (r²={r_value**2:.2f})')
            ax.legend()
    except Exception as e:
        log_exception("Failed to add trend line to scatter plot", e)
