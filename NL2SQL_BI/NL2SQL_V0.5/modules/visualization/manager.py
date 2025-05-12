import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
import numpy as np
import hashlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import components
from .chart_recommender import ChartRecommender
from .chart_creators import (
    create_enhanced_bar_chart, 
    create_enhanced_line_chart,
    create_scatter_chart,
    create_pie_chart, 
    create_heatmap_chart,
    create_histogram_chart,
    create_box_chart,
    create_radar_chart,
    create_fallback_chart,
    create_universal_fallback_chart
)
from .data_processor import preprocess_dataframe
from .clipboard_utils import copy_figure_to_clipboard
from ..utils import log_exception

class VisualizationManager:
    def __init__(self, ai_manager=None):
        self.ai_manager = ai_manager
        # Set a professional style for charts
        plt.style.use('ggplot')
        # Color maps for consistent colors in comparisons
        self.comparison_colors = plt.cm.tab10.colors
        # Initialize chart recommender
        self.chart_recommender = ChartRecommender(ai_manager)
        # Add chart figure cache to avoid regenerating the same charts
        self.chart_cache = {}
        # Maximum cache size
        self.max_cache_size = 20
    
    def set_ai_manager(self, ai_manager):
        """Set AI manager for chart recommendations"""
        self.ai_manager = ai_manager
        self.chart_recommender.set_ai_manager(ai_manager)
    
    def recommend_chart_type(self, df, query=None):
        """Use AI to recommend the best chart type for the data"""
        return self.chart_recommender.recommend_chart_type(df, query)
    
    def generate_chart(self, df, chart_frame, query=None):
        """Generate appropriate chart for the data based on AI recommendation"""
        try:
            # Generate a cache key
            cache_key = self._get_cache_key(df, query)
            
            # Clear current chart
            for widget in chart_frame.winfo_children():
                widget.destroy()

            # Check if we have data and it's suitable for visualization
            if df.empty:
                ttk.Label(chart_frame, text="No data available for visualization").pack(expand=True)
                return False
            
            # Check cache first before processing
            if cache_key in self.chart_cache:
                # Use cached figure if available
                fig = self.chart_cache[cache_key]
                
                # Embed the cached plot in the chart frame
                canvas = FigureCanvasTkAgg(fig, master=chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add toolbar for navigation
                from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                toolbar_frame = ttk.Frame(chart_frame)
                toolbar_frame.pack(fill=tk.X, expand=False)
                toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                toolbar.update()
                
                # Add copy to clipboard button
                copy_btn = ttk.Button(
                    toolbar_frame,
                    text="Copy to Clipboard",
                    command=lambda: copy_figure_to_clipboard(fig)
                )
                copy_btn.pack(side=tk.RIGHT)
                
                return True
                
            # Preprocess dataframe to ensure optimal visualization
            df_processed = preprocess_dataframe(df)

            # Get AI-based chart recommendation
            recommendation = self.recommend_chart_type(df_processed, query)
            chart_type = recommendation.get("chart_type", "none")
            
            if chart_type == "none":
                ttk.Label(chart_frame, text="This data is not suitable for visualization").pack(expand=True)
                return False
            
            # Create figure and axis with appropriate size based on data
            if recommendation.get("chart_orientation") == "horizontal" and len(df_processed) > 10:
                # For horizontal charts with many items, make the figure taller
                fig_height = min(12, max(6, len(df_processed) * 0.4))  # Dynamic height based on data points
                fig, ax = plt.subplots(figsize=(10, fig_height))
            else:
                fig, ax = plt.subplots(figsize=(10, 6))
            
            # Generate chart based on AI recommendation with error handling
            try:
                # Create the basic chart based on AI recommendation
                if chart_type == "bar":
                    create_enhanced_bar_chart(df_processed, ax, recommendation, self.comparison_colors)
                elif chart_type == "line":
                    create_enhanced_line_chart(df_processed, ax, recommendation, self.comparison_colors)
                elif chart_type == "scatter":
                    create_scatter_chart(df_processed, ax, recommendation)
                elif chart_type == "pie":
                    create_pie_chart(df_processed, ax, recommendation)
                elif chart_type == "heatmap":
                    create_heatmap_chart(df_processed, ax, recommendation)
                elif chart_type == "histogram":
                    create_histogram_chart(df_processed, ax, recommendation)
                elif chart_type == "box":
                    create_box_chart(df_processed, ax, recommendation)
                elif chart_type == "radar":
                    create_radar_chart(df_processed, fig, recommendation, self.comparison_colors)
                else:
                    # Fallback to a simple bar chart
                    create_fallback_chart(df_processed, ax)
                    
                # Apply AI-driven enhancements to the chart
                from .chart_creators import enhance_chart_with_ai
                enhance_chart_with_ai(ax, df_processed, recommendation, chart_type)
                
            except Exception as chart_error:
                log_exception(f"Failed to create {chart_type} chart, attempting fallback", chart_error)
                # If the specific chart creation fails, try the universal fallback chart
                plt.clf()  # Clear the figure
                fig, ax = plt.subplots(figsize=(10, 6))
                create_universal_fallback_chart(df_processed, ax, chart_type)
            
            # Set the title if not a radar chart (which has its own title handling)
            if chart_type != "radar" and not ax.get_title():
                ax.set_title(recommendation.get("title", "Query Results Visualization"))
            
            # Determine chart composition to adjust margins properly
            has_explanation = "explanation" in recommendation
            has_legend = chart_type in ["line", "scatter"] or (chart_type == "bar" and len(recommendation.get("y_axis", [])) > 1)
            
            # Skip tight_layout which can cause warnings
            # Instead, directly set appropriate margins based on chart elements
            if has_explanation and has_legend:
                plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.2)
            elif has_explanation:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)
            elif has_legend:
                plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.15)
            else:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
            
            # Add explanation as a footer note if available
            if has_explanation:
                fig.text(0.5, 0.02, recommendation["explanation"], ha='center', 
                         fontsize=8, fontstyle='italic')

            # Cache the figure for future use
            if len(self.chart_cache) >= self.max_cache_size:
                # Remove oldest cache entry if we exceed max size
                oldest_key = next(iter(self.chart_cache))
                del self.chart_cache[oldest_key]
            
            # Store in cache
            self.chart_cache[cache_key] = fig
            
            # Embed the plot in the chart frame
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add toolbar for navigation
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar_frame = ttk.Frame(chart_frame)
            toolbar_frame.pack(fill=tk.X, expand=False)
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            
            # Add copy to clipboard button
            copy_btn = ttk.Button(
                toolbar_frame,
                text="Copy to Clipboard",
                command=lambda: copy_figure_to_clipboard(fig)
            )
            copy_btn.pack(side=tk.RIGHT)
            
            return True
        except Exception as e:
            error_msg = log_exception("Failed to generate chart", e)
            ttk.Label(chart_frame, text=f"Visualization error: {error_msg}").pack(expand=True)
            return False
    
    def _get_cache_key(self, df, query=None):
        """Generate a cache key for dataframe and query combination"""
        try:
            # Create hashable data from DataFrame
            df_hash = hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()
            query_hash = hashlib.md5(str(query).encode()).hexdigest() if query else "no-query"
            return f"{df_hash}_{query_hash}"
        except:
            # If hashing fails, generate a unique timestamp-based key (fallback)
            import time
            return f"chart_{time.time()}"
