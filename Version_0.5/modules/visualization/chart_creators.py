import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ..utils import log_exception

# Import specific chart creation modules
from .charts.bar_charts import create_enhanced_bar_chart
from .charts.line_charts import create_enhanced_line_chart
from .charts.scatter_charts import create_scatter_chart
from .charts.pie_charts import create_pie_chart
from .charts.heatmap_charts import create_heatmap_chart, create_correlation_heatmap
from .charts.statistical_charts import create_histogram_chart, create_box_chart
from .charts.radar_charts import create_radar_chart
from .charts.fallback_charts import create_fallback_chart, create_universal_fallback_chart
from .charts.ai_enhancer import AIChartEnhancer

# Re-export all chart creation functions
__all__ = [
    'create_enhanced_bar_chart',
    'create_enhanced_line_chart',
    'create_scatter_chart',
    'create_pie_chart',
    'create_heatmap_chart',
    'create_correlation_heatmap',
    'create_histogram_chart',
    'create_box_chart',
    'create_radar_chart',
    'create_fallback_chart',
    'create_universal_fallback_chart',
    'enhance_chart_with_ai'
]

def enhance_chart_with_ai(ax, df, recommendation, chart_type):
    """Apply AI-driven enhancements to charts"""
    return AIChartEnhancer.enhance_chart(ax, df, recommendation, chart_type)
