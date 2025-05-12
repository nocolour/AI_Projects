import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ...utils import log_exception

def create_enhanced_line_chart(df, ax, recommendation, comparison_colors):
    """Create an enhanced line chart with better handling of comparisons"""
    x_col = recommendation.get("x_axis")
    y_cols = recommendation.get("y_axis", [])
    color_by = recommendation.get("color_by")
    is_comparison = recommendation.get("is_comparison", False)
    
    # Handle special case where x_col is "index" (for datasets with only numeric columns)
    if x_col == "index":
        # Create a column for indices
        df = df.copy()
        df['_row_index'] = range(1, len(df) + 1)
        x_col = '_row_index'
        
    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
    
    if not y_cols:
        # If no y columns specified, use numeric columns (except x_col)
        y_cols = [col for col in df.select_dtypes(include=['number']).columns if col != x_col]
    else:
        # Filter to ensure only existing columns are used
        y_cols = [col for col in y_cols if col in df.columns]
    
    # Can't create chart if we don't have valid x or y columns
    if not x_col or not y_cols:
        return
    
    # Try to detect time series data for better formatting
    is_time_series = (
        pd.api.types.is_datetime64_dtype(df[x_col]) or
        'date' in x_col.lower() or 'time' in x_col.lower() or
        'year' in x_col.lower() or 'month' in x_col.lower() or
        'day' in x_col.lower()
    )
    
    # Limit to 5 y columns for readability
    y_cols = y_cols[:5]
    
    # Optimize sampling for large datasets
    large_dataset = len(df) > 50
    if large_dataset:
        # Sample points more intelligently for large datasets
        if x_col != '_row_index' and pd.api.types.is_numeric_dtype(df[x_col]):
            # For numeric x-axis, sample evenly across the range
            try:
                df_sorted = df.sort_values(by=x_col)
                # Take systematic sample if more than 50 points
                if len(df_sorted) > 50:
                    sample_size = 50  # Good balance for visualization
                    indices = np.linspace(0, len(df_sorted) - 1, sample_size).astype(int)
                    df_plot = df_sorted.iloc[indices]
                else:
                    df_plot = df_sorted
            except Exception:
                df_plot = df
        else:
            # For categorical/datetime x-axis
            try:
                df_sorted = df.sort_values(by=x_col)
                if len(df_sorted) > 50:
                    # Take first/last points plus systematic samples in between
                    head_size = 10
                    tail_size = 10
                    middle_size = 30
                    
                    head = df_sorted.head(head_size)
                    tail = df_sorted.tail(tail_size)
                    
                    if len(df_sorted) > (head_size + tail_size):
                        middle_indices = np.linspace(head_size, len(df_sorted) - tail_size - 1, middle_size).astype(int)
                        middle = df_sorted.iloc[middle_indices]
                        df_plot = pd.concat([head, middle, tail])
                    else:
                        df_plot = pd.concat([head, tail])
                else:
                    df_plot = df_sorted
            except Exception:
                # If sorting fails, take systematic sample
                if len(df) > 50:
                    indices = np.linspace(0, len(df) - 1, 50).astype(int)
                    df_plot = df.iloc[indices]
                else:
                    df_plot = df
    else:
        # For smaller datasets, try to sort by x_col
        try:
            df_plot = df.sort_values(by=x_col)
        except Exception:
            df_plot = df
    
    # Set marker style based on dataset size
    if large_dataset:
        marker_style = 'o' if len(df_plot) <= 30 else '.'
        marker_size = 4 if len(df_plot) <= 30 else 3
    else:
        marker_style = 'o'
        marker_size = 6
        
    # Use enhanced styling for line charts
    try:
        # Different rendering based on dataset characteristics
        if is_comparison and len(y_cols) == 1 and color_by and color_by in df_plot.columns:
            # Plot lines grouped by the color_by column
            # Limit to top 10 categories for color_by if too many
            unique_categories = df_plot[color_by].unique()
            if len(unique_categories) > 10:
                # Find top categories by y-value
                top_categories = df_plot.groupby(color_by)[y_cols[0]].sum().nlargest(10).index
                df_plot = df_plot[df_plot[color_by].isin(top_categories)]
                
            for i, (name, group) in enumerate(df_plot.groupby(color_by)):
                color = comparison_colors[i % len(comparison_colors)]
                group.plot(kind='line', x=x_col, y=y_cols[0], ax=ax, 
                          marker=marker_style, markersize=marker_size, linewidth=2,
                          linestyle='-', color=color, label=name)
        else:
            # Standard line chart with improved styling
            df_plot.plot(kind='line', x=x_col, y=y_cols, ax=ax, 
                       marker=marker_style, markersize=marker_size, linewidth=2,
                       linestyle='-', colormap='viridis')
            
        # Add a subtle grid that doesn't interfere with the lines
        ax.grid(True, linestyle='--', alpha=0.3, which='both')
        
        # For time series or large datasets, consider adding minor gridlines
        if is_time_series or large_dataset:
            ax.grid(True, which='minor', linestyle=':', alpha=0.2)
            ax.minorticks_on()
            
        # Better legend placement
        if len(y_cols) > 1 or (is_comparison and color_by):
            title = 'Metrics' if len(y_cols) > 1 else color_by
            ax.legend(title=title, bbox_to_anchor=(1.05, 1), loc='upper left',
                    framealpha=0.9, fancybox=True, shadow=True)
            
        # Time series specific formatting
        if is_time_series:
            # Rotate labels for time series
            plt.xticks(rotation=45, ha='right')
            ax.figure.subplots_adjust(bottom=0.2)
            
            # For datetime columns, format x-axis with appropriate date format
            if pd.api.types.is_datetime64_dtype(df_plot[x_col]):
                from matplotlib.dates import DateFormatter
                
                # Choose format based on date range
                date_range = df_plot[x_col].max() - df_plot[x_col].min()
                if date_range.days > 365*2:  # More than 2 years
                    date_format = '%Y'  # Just year
                elif date_range.days > 60:  # More than 2 months
                    date_format = '%b %Y'  # Month and year
                else:
                    date_format = '%d %b'  # Day and month
                    
                ax.xaxis.set_major_formatter(DateFormatter(date_format))
        elif len(df_plot) > 10:
            # Format x-axis labels if too many
            plt.xticks(rotation=45, ha='right')
            ax.figure.subplots_adjust(bottom=0.15)
        
        # Enhance axes for better readability
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['top'].set_visible(False)  # Remove top spine
        ax.spines['right'].set_visible(False)  # Remove right spine
        
        # Add y-axis label
        if len(y_cols) == 1:
            ax.set_ylabel(y_cols[0], fontsize=10, fontweight='bold')
            
        # Add x-axis label
        if x_col != '_row_index':  # Don't label if it's just row indices
            ax.set_xlabel(x_col, fontsize=10, fontweight='bold')
        else:
            ax.set_xlabel("Data Points", fontsize=10, fontweight='bold')
            
    except Exception as e:
        # If the enhanced visualization fails, fall back to a simpler approach
        log_exception("Enhanced line chart failed, using fallback", e)
        try:
            df.plot(kind='line', x=x_col, y=y_cols, ax=ax, marker='o')
            plt.xticks(rotation=45, ha='right')
            ax.figure.subplots_adjust(bottom=0.15)
        except:
            pass  # Let the caller handle complete failure
