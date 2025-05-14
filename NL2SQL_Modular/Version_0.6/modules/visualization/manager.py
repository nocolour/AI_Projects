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
from ..constants import CHART_TYPES, CHART_POPUP_SIZE, MAIN_CHART_POPUP_SIZE

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
        # Track open chart windows
        self.chart_windows = {}
        # Track alternative chart windows
        self.alt_chart_windows = {}
    
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
    
    def open_chart_in_new_window(self, df, query=None, parent=None):
        """Open the chart in a separate window"""
        try:
            # Generate cache key to reuse chart if possible
            cache_key = self._get_cache_key(df, query)
            
            # Check if we already have a window open for this chart
            if cache_key in self.chart_windows and self.chart_windows[cache_key].winfo_exists():
                # If window exists, bring it to front
                window = self.chart_windows[cache_key]
                window.lift()
                window.focus_force()
                return window
            
            # Create new toplevel window
            window = tk.Toplevel(parent)
            window_title = "Chart Visualization"
            if query:
                # Use the query as part of the window title, but limit its length
                query_excerpt = query[:50] + "..." if len(query) > 50 else query
                window_title = f"Chart: {query_excerpt}"
            window.title(window_title)
            window.geometry(MAIN_CHART_POPUP_SIZE)  # Use constant for window size
            
            # Create frame for chart
            chart_frame = ttk.Frame(window, padding=10)
            chart_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create button frame at the bottom
            button_frame = ttk.Frame(window, padding=(10, 0, 10, 10))
            button_frame.pack(fill=tk.X, expand=False)
            
            # Add button to show alternative chart types
            alt_charts_btn = ttk.Button(
                button_frame,
                text="Show Other Chart Types",
                command=lambda: self.show_alternative_charts(df, query, window)
            )
            alt_charts_btn.pack(side=tk.RIGHT, padx=5)
            
            # Generate the chart in this frame
            self.generate_chart(df, chart_frame, query)
            
            # Store window reference with cache key
            self.chart_windows[cache_key] = window
            
            # Handle window close event to remove from tracking
            window.protocol("WM_DELETE_WINDOW", lambda: self._on_chart_window_close(window, cache_key))
            
            return window
        except Exception as e:
            error_msg = log_exception("Failed to open chart in new window", e)
            if parent:
                from tkinter import messagebox
                messagebox.showerror("Visualization Error", error_msg)
            return None
    
    def show_alternative_charts(self, df, query=None, parent_window=None):
        """Show alternative chart types for the same data"""
        try:
            # Get current chart type from cache
            cache_key = self._get_cache_key(df, query)
            current_chart_type = None
            recommendation = None
            
            if cache_key in self.chart_cache:
                # Extract the current chart type from recommendation
                recommendation = self.recommend_chart_type(df, query)
                current_chart_type = recommendation.get("chart_type")
            
            # Use AI-recommended alternatives if available, otherwise fall back to constants
            chart_types = []
            alternative_explanations = {}
            
            if recommendation and "alternative_charts" in recommendation:
                # Use AI-recommended alternatives
                for alt in recommendation["alternative_charts"]:
                    chart_type = alt.get("chart_type")
                    explanation = alt.get("explanation", "")
                    if chart_type and chart_type != current_chart_type:
                        chart_types.append(chart_type)
                        alternative_explanations[chart_type] = explanation
            else:
                # Fall back to predefined alternatives
                chart_types = CHART_TYPES["alternative"].copy()
                # Remove current chart type from the list
                if current_chart_type and current_chart_type in chart_types:
                    chart_types.remove(current_chart_type)
            
            # Show a message if no charts are being created
            if not chart_types:
                from tkinter import messagebox
                messagebox.showinfo("Chart Types", "No additional chart types available for this data.")
                return
                
            # Track newly created windows for this set of alternative charts
            alt_chart_windows = []
            
            # Create one window per chart type
            for chart_type in chart_types:
                # Create a customized recommendation for this chart type
                custom_recommendation = self._create_custom_recommendation(df, chart_type, query)
                
                if not custom_recommendation:
                    continue  # Skip if we couldn't create a recommendation
                
                # Add explanation from AI if available
                if chart_type in alternative_explanations:
                    custom_recommendation["explanation"] = alternative_explanations[chart_type]
                
                # Create new toplevel window
                chart_window = tk.Toplevel(parent_window)
                chart_window.title(f"{chart_type.capitalize()} Chart View")
                chart_window.geometry(CHART_POPUP_SIZE)  # Use constant for window size
                
                # Create frame for chart
                chart_frame = ttk.Frame(chart_window, padding=10)
                chart_frame.pack(fill=tk.BOTH, expand=True)
                
                # Try to generate this chart type
                try:
                    # Create figure and axis
                    fig, ax = plt.subplots(figsize=(9, 5))
                    
                    # Create the chart based on type - use our already imported functions
                    if chart_type == "bar":
                        create_enhanced_bar_chart(df, ax, custom_recommendation, self.comparison_colors)
                    elif chart_type == "line":
                        create_enhanced_line_chart(df, ax, custom_recommendation, self.comparison_colors)
                    elif chart_type == "scatter":
                        create_scatter_chart(df, ax, custom_recommendation)
                    elif chart_type == "pie":
                        create_pie_chart(df, ax, custom_recommendation)
                    elif chart_type == "heatmap":
                        create_heatmap_chart(df, ax, custom_recommendation)
                    elif chart_type == "histogram":
                        create_histogram_chart(df, ax, custom_recommendation)
                    elif chart_type == "box":
                        create_box_chart(df, ax, custom_recommendation)
                    else:
                        # Fallback
                        create_fallback_chart(df, ax)
                    
                    # Add AI explanation if available
                    if "explanation" in custom_recommendation:
                        explanation = custom_recommendation["explanation"]
                        fig.text(0.5, 0.01, explanation, ha='center', fontsize=8, 
                               fontstyle='italic', wrap=True)
                        fig.subplots_adjust(bottom=0.2)  # Make space for explanation
                    
                    # Adjust margins
                    plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Leave room for explanation
                    
                    # Embed in tkinter window
                    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                    
                    # Add navigation toolbar
                    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                    toolbar_frame = ttk.Frame(chart_frame)
                    toolbar_frame.pack(fill=tk.X, expand=False)
                    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                    toolbar.update()
                    
                    # Add to list of created windows
                    alt_chart_windows.append(chart_window)
                    
                except Exception as e:
                    log_exception(f"Failed to create {chart_type} chart", e)
                    chart_window.destroy()  # Close the window if chart creation failed
                    continue
                
                # Position windows in cascade
                if len(alt_chart_windows) > 1:
                    last_window = alt_chart_windows[-2]
                    x = last_window.winfo_x() + 50
                    y = last_window.winfo_y() + 50
                    chart_window.geometry(f"+{x}+{y}")
            
            # Track these windows
            if cache_key not in self.alt_chart_windows:
                self.alt_chart_windows[cache_key] = []
                
            self.alt_chart_windows[cache_key].extend(alt_chart_windows)
            
            # Return the created windows
            return alt_chart_windows
            
        except Exception as e:
            error_msg = log_exception("Failed to show alternative charts", e)
            from tkinter import messagebox
            messagebox.showerror("Visualization Error", error_msg)
            return None
    
    def _create_custom_recommendation(self, df, chart_type, query=None):
        """Create a custom recommendation for a specific chart type"""
        try:
            # Start with basic recommendation to get columns
            base_rec = self.recommend_chart_type(df, query)
            
            # Create a new recommendation with the specified chart type
            custom_rec = {
                "chart_type": chart_type,
                "x_axis": base_rec.get("x_axis"),
                "y_axis": base_rec.get("y_axis", []),
                "title": f"{chart_type.capitalize()} Chart of {base_rec.get('title', 'Data')}",
                "color_by": base_rec.get("color_by"),
                "is_comparison": base_rec.get("is_comparison", False),
                "chart_orientation": "vertical" if chart_type != "bar" else base_rec.get("chart_orientation", "vertical")
            }
            
            # Copy AI-specific fields from the original recommendation
            for field in ["explanation", "comparison_entities", "comparison_type"]:
                if field in base_rec:
                    custom_rec[field] = base_rec[field]
            
            # Find the explanation for this chart type in alternative_charts if available
            if "alternative_charts" in base_rec:
                for alt in base_rec["alternative_charts"]:
                    if alt.get("chart_type") == chart_type and "explanation" in alt:
                        custom_rec["explanation"] = alt["explanation"]
                        break
            
            # For pie charts, we need only one y-axis column
            if chart_type == "pie" and custom_rec["y_axis"]:
                custom_rec["y_axis"] = [custom_rec["y_axis"][0]]
            
            # For scatter plots, we need two numeric columns
            if chart_type == "scatter":
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if len(numeric_cols) >= 2:
                    if custom_rec["x_axis"] not in numeric_cols:
                        custom_rec["x_axis"] = numeric_cols[0]
                    
                    y_numeric = [col for col in numeric_cols if col != custom_rec["x_axis"]]
                    if y_numeric:
                        custom_rec["y_axis"] = [y_numeric[0]]
            
            return custom_rec
        except Exception as e:
            log_exception(f"Failed to create custom recommendation for {chart_type}", e)
            return None
    
    def _on_chart_window_close(self, window, cache_key):
        """Handle chart window closing"""
        # Remove from tracking dictionaries
        if cache_key in self.chart_windows:
            del self.chart_windows[cache_key]
            
        # Close any related alternative chart windows
        if cache_key in self.alt_chart_windows:
            for alt_window in self.alt_chart_windows[cache_key]:
                if alt_window.winfo_exists():
                    alt_window.destroy()
            del self.alt_chart_windows[cache_key]
            
        # Destroy the window
        window.destroy()
