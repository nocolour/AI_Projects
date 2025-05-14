import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ...utils import log_exception

def create_histogram_chart(df, ax, recommendation):
    """Create a histogram chart"""
    x_col = recommendation.get("x_axis")
    
    # Validate column exists in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
        
    # Need a valid numeric column for histogram
    if not x_col or not pd.api.types.is_numeric_dtype(df[x_col]):
        # Try to find any numeric column
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            x_col = numeric_cols[0]
        else:
            return
            
    # Determine optimal number of bins
    n_bins = min(30, max(10, int(len(df) / 10)))
    
    # Plot histogram
    n, bins, patches = ax.hist(
        df[x_col].dropna(), 
        bins=n_bins, 
        color='steelblue',
        alpha=0.7,
        edgecolor='white'
    )
    
    # Add a density curve if enough data points
    if len(df) > 30:
        try:
            from scipy import stats
            
            density = stats.gaussian_kde(df[x_col].dropna())
            x_range = np.linspace(min(bins), max(bins), 100)
            ax.plot(x_range, density(x_range) * len(df) * (bins[1] - bins[0]), 
                  'r-', linewidth=2)
        except Exception as e:
            log_exception("Failed to add density curve to histogram", e)
            
    # Add vertical lines for mean and median
    mean = df[x_col].mean()
    median = df[x_col].median()
    
    ax.axvline(mean, color='r', linestyle='--', linewidth=1.5, 
             label=f'Mean: {mean:.2f}')
    ax.axvline(median, color='g', linestyle='--', linewidth=1.5,
             label=f'Median: {median:.2f}')
    
    # Add a grid for readability
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # Add labels
    ax.set_xlabel(x_col)
    ax.set_ylabel('Frequency')
    
    # Add legend
    ax.legend()

def create_box_chart(df, ax, recommendation):
    """Create a box chart"""
    x_col = recommendation.get("x_axis")
    y_cols = recommendation.get("y_axis", [])
    
    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
        
    if not y_cols:
        y_cols = [col for col in df.select_dtypes(include=['number']).columns if col != x_col]
    else:
        y_cols = [col for col in y_cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
        
    # Need at least one numeric column for box plot
    if not y_cols:
        return
        
    # If x_col is categorical, create grouped box plot
    if x_col and not pd.api.types.is_numeric_dtype(df[x_col]):
        # Limit to 7 categories for readability
        categories = df[x_col].value_counts().nlargest(7).index
        filtered_df = df[df[x_col].isin(categories)]
        
        # Create box plot
        sns.boxplot(x=x_col, y=y_cols[0], data=filtered_df, ax=ax)
        
        # Rotate x labels if needed
        if len(categories) > 4:
            plt.xticks(rotation=45, ha='right')
            ax.figure.subplots_adjust(bottom=0.2)
            
        ax.set_title(f'Distribution of {y_cols[0]} by {x_col}')
    else:
        # Create box plots for each numeric column
        df.boxplot(column=y_cols, ax=ax, grid=False)
        
        # Add a grid for y-axis only
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Rotate x labels if needed
        if len(y_cols) > 4:
            plt.xticks(rotation=45, ha='right')
            
        ax.set_title('Distribution of Numeric Columns')
        
    # Enhance y-axis
    ax.set_ylabel(y_cols[0] if len(y_cols) == 1 else 'Value')
