import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from ...utils import log_exception

class AIChartEnhancer:
    """
    Enhances charts based on AI recommendations, applying smart formatting
    and highlighting insights detected by AI.
    """
    
    @staticmethod
    def enhance_chart(ax, df, recommendation, chart_type):
        """Apply AI-recommended enhancements to a chart"""
        try:
            # Apply universal enhancements
            AIChartEnhancer._enhance_title(ax, recommendation)
            AIChartEnhancer._enhance_labels(ax, recommendation)
            
            # Apply chart-specific enhancements
            if chart_type == "bar":
                AIChartEnhancer._enhance_bar_chart(ax, df, recommendation)
            elif chart_type == "line":
                AIChartEnhancer._enhance_line_chart(ax, df, recommendation)
            elif chart_type == "scatter":
                AIChartEnhancer._enhance_scatter_chart(ax, df, recommendation)
            elif chart_type == "pie":
                AIChartEnhancer._enhance_pie_chart(ax, recommendation)
                
            return True
        except Exception as e:
            log_exception("Failed to apply AI enhancements to chart", e)
            return False
    
    @staticmethod
    def _enhance_title(ax, recommendation):
        """Improve chart title based on AI recommendation"""
        title = recommendation.get("title")
        if title:
            # Make the title more descriptive and impactful
            if recommendation.get("is_comparison", False):
                if not title.lower().startswith("comparison"):
                    title = f"Comparison of {title}"
                    
            ax.set_title(title, fontweight='bold', pad=15)
    
    @staticmethod
    def _enhance_labels(ax, recommendation):
        """Improve axis labels based on AI recommendation"""
        x_label = recommendation.get("x_axis")
        y_cols = recommendation.get("y_axis", [])
        
        if x_label:
            # Improve x-axis label
            if x_label == "_row_index":
                ax.set_xlabel("Data Points", fontsize=10)
            else:
                ax.set_xlabel(x_label, fontsize=10)
        
        if y_cols and len(y_cols) == 1:
            # Improve y-axis label
            ax.set_ylabel(y_cols[0], fontsize=10)
    
    @staticmethod
    def _enhance_bar_chart(ax, df, recommendation):
        """Apply AI-driven enhancements to bar charts"""
        # Highlight the most significant bar
        y_cols = recommendation.get("y_axis", [])
        x_axis = recommendation.get("x_axis")
        
        if y_cols and len(y_cols) == 1 and x_axis and x_axis in df.columns:
            try:
                y_col = y_cols[0]
                
                # Find max and min values
                max_idx = df[y_col].idxmax()
                max_val = df.loc[max_idx, y_col]
                max_x = df.loc[max_idx, x_axis]
                
                # Find the position of max_x in the plot
                if len(ax.patches) > 0:
                    for i, patch in enumerate(ax.patches):
                        # Try to match the patch to the max value
                        if abs(patch.get_height() - max_val) < 0.001:
                            # Highlight this bar
                            patch.set_edgecolor('red')
                            patch.set_linewidth(2)
                            
                            # Add annotation
                            ax.annotate(f'Highest: {max_val:.1f}',
                                      xy=(patch.get_x() + patch.get_width()/2, patch.get_height()),
                                      xytext=(0, 10),
                                      textcoords='offset points',
                                      ha='center', va='bottom',
                                      fontsize=9, fontweight='bold',
                                      color='darkred',
                                      bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.3))
                            break
            except Exception as e:
                # Silently handle errors in enhancement
                pass
    
    @staticmethod
    def _enhance_line_chart(ax, df, recommendation):
        """Apply AI-driven enhancements to line charts"""
        y_cols = recommendation.get("y_axis", [])
        
        if len(y_cols) == 1:
            try:
                y_col = y_cols[0]
                
                # Get the line objects
                lines = ax.get_lines()
                if lines:
                    # Add subtle trend markers for significant changes
                    line = lines[0]
                    y_data = line.get_ydata()
                    x_data = line.get_xdata()
                    
                    if len(y_data) > 5:
                        # Find significant rising or falling trends
                        for i in range(2, len(y_data)-2):
                            # Check for rising trend
                            if (y_data[i-2] < y_data[i-1] < y_data[i] < y_data[i+1] < y_data[i+2]):
                                # Mark rising trend
                                ax.annotate('↗', 
                                         xy=(x_data[i], y_data[i]),
                                         xytext=(0, 10),
                                         textcoords='offset points',
                                         ha='center', fontsize=12, color='green',
                                         alpha=0.7)
                                
                            # Check for falling trend
                            elif (y_data[i-2] > y_data[i-1] > y_data[i] > y_data[i+1] > y_data[i+2]):
                                # Mark falling trend
                                ax.annotate('↘', 
                                         xy=(x_data[i], y_data[i]),
                                         xytext=(0, 10),
                                         textcoords='offset points',
                                         ha='center', fontsize=12, color='red',
                                         alpha=0.7)
            except Exception as e:
                # Silently handle errors in enhancement
                pass
    
    @staticmethod
    def _enhance_scatter_chart(ax, df, recommendation):
        """Apply AI-driven enhancements to scatter charts"""
        x_col = recommendation.get("x_axis")
        y_cols = recommendation.get("y_axis", [])
        
        if x_col and y_cols and len(y_cols) > 0:
            try:
                # Add a simple trendline
                x = df[x_col].values
                y = df[y_cols[0]].values
                
                # Only add trendline if there are sufficient points
                if len(x) > 5 and pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_cols[0]]):
                    from scipy import stats
                    
                    # Calculate trendline
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    
                    if not np.isnan(slope) and not np.isnan(intercept):
                        # Add trendline
                        x_line = np.linspace(min(x), max(x), 100)
                        y_line = slope * x_line + intercept
                        
                        # Add correlation coefficient
                        correlation_text = f"Correlation: {r_value:.2f}"
                        
                        # Different styling based on correlation strength
                        if abs(r_value) > 0.7:
                            # Strong correlation
                            line_style = 'solid'
                            line_width = 2
                            line_color = 'red'
                            text_color = 'red'
                            text_weight = 'bold'
                        elif abs(r_value) > 0.3:
                            # Medium correlation
                            line_style = 'dashed'
                            line_width = 1.5
                            line_color = 'orange'
                            text_color = 'darkorange'
                            text_weight = 'normal'
                        else:
                            # Weak correlation
                            line_style = 'dotted'
                            line_width = 1
                            line_color = 'gray'
                            text_color = 'gray'
                            text_weight = 'normal'
                            
                        # Draw trendline
                        ax.plot(x_line, y_line, linestyle=line_style, 
                              linewidth=line_width, color=line_color, alpha=0.8)
                        
                        # Add correlation text
                        ax.annotate(correlation_text, 
                                  xy=(0.05, 0.95), xycoords='axes fraction',
                                  fontsize=9, fontweight=text_weight, color=text_color, 
                                  bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.8))
            except Exception as e:
                # Silently handle errors in enhancement
                pass
    
    @staticmethod
    def _enhance_pie_chart(ax, recommendation):
        """Apply AI-driven enhancements to pie charts"""
        # Add simple enhancements for pie charts
        try:
            # Make the largest slice stand out slightly
            wedges = ax.patches if hasattr(ax, 'patches') else []
            if wedges:
                largest = max(wedges, key=lambda x: x.theta2 - x.theta1)
                largest.set_edgecolor('darkred')
                largest.set_linewidth(2)
                largest.set_alpha(0.9)
        except:
            pass
