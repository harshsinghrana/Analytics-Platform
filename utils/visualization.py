import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

class Visualization:
    """Handles creation of various chart types using Plotly"""
    
    def __init__(self):
        self.chart_types = {
            'Line Chart': self.create_line_chart,
            'Bar Chart': self.create_bar_chart,
            'Scatter Plot': self.create_scatter_plot,
            'Histogram': self.create_histogram,
            'Box Plot': self.create_box_plot,
            'Pie Chart': self.create_pie_chart,
            'Heatmap': self.create_heatmap,
            'Area Chart': self.create_area_chart
        }
    
    def get_available_charts(self):
        """Return list of available chart types"""
        return list(self.chart_types.keys())
    
    def create_chart(self, chart_type, df, config):
        """Create chart based on type and configuration"""
        if chart_type not in self.chart_types:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        try:
            return self.chart_types[chart_type](df, config)
        except Exception as e:
            st.error(f"Error creating {chart_type}: {str(e)}")
            return None
    
    def create_line_chart(self, df, config):
        """Create line chart"""
        x_col = config.get('x_column')
        y_col = config.get('y_column')
        color_col = config.get('color_column')
        
        if not x_col or not y_col:
            raise ValueError("X and Y columns are required for line chart")
        
        fig = px.line(
            df, 
            x=x_col, 
            y=y_col,
            color=color_col if color_col else None,
            title=config.get('title', f'{y_col} over {x_col}')
        )
        
        return fig
    
    def create_bar_chart(self, df, config):
        """Create bar chart"""
        x_col = config.get('x_column')
        y_col = config.get('y_column')
        color_col = config.get('color_column')
        
        if not x_col or not y_col:
            raise ValueError("X and Y columns are required for bar chart")
        
        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            color=color_col if color_col else None,
            title=config.get('title', f'{y_col} by {x_col}')
        )
        
        return fig
    
    def create_scatter_plot(self, df, config):
        """Create scatter plot"""
        x_col = config.get('x_column')
        y_col = config.get('y_column')
        color_col = config.get('color_column')
        size_col = config.get('size_column')
        
        if not x_col or not y_col:
            raise ValueError("X and Y columns are required for scatter plot")
        
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col if color_col else None,
            size=size_col if size_col else None,
            title=config.get('title', f'{y_col} vs {x_col}')
        )
        
        return fig
    
    def create_histogram(self, df, config):
        """Create histogram"""
        x_col = config.get('x_column')
        color_col = config.get('color_column')
        
        if not x_col:
            raise ValueError("X column is required for histogram")
        
        fig = px.histogram(
            df,
            x=x_col,
            color=color_col if color_col else None,
            title=config.get('title', f'Distribution of {x_col}'),
            nbins=config.get('bins', 30)
        )
        
        return fig
    
    def create_box_plot(self, df, config):
        """Create box plot"""
        x_col = config.get('x_column')
        y_col = config.get('y_column')
        color_col = config.get('color_column')
        
        if not y_col:
            raise ValueError("Y column is required for box plot")
        
        fig = px.box(
            df,
            x=x_col if x_col else None,
            y=y_col,
            color=color_col if color_col else None,
            title=config.get('title', f'Box Plot of {y_col}')
        )
        
        return fig
    
    def create_pie_chart(self, df, config):
        """Create pie chart"""
        values_col = config.get('values_column')
        names_col = config.get('names_column')
        
        if not values_col or not names_col:
            raise ValueError("Values and names columns are required for pie chart")
        
        # Aggregate data if needed
        pie_data = df.groupby(names_col)[values_col].sum().reset_index()
        
        fig = px.pie(
            pie_data,
            values=values_col,
            names=names_col,
            title=config.get('title', f'{values_col} by {names_col}')
        )
        
        return fig
    
    def create_heatmap(self, df, config):
        """Create heatmap for correlation matrix"""
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) < 2:
            raise ValueError("At least 2 numeric columns are required for heatmap")
        
        correlation_matrix = df[numeric_cols].corr()
        
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title=config.get('title', 'Correlation Heatmap')
        )
        
        return fig
    
    def create_area_chart(self, df, config):
        """Create area chart"""
        x_col = config.get('x_column')
        y_col = config.get('y_column')
        color_col = config.get('color_column')
        
        if not x_col or not y_col:
            raise ValueError("X and Y columns are required for area chart")
        
        fig = px.area(
            df,
            x=x_col,
            y=y_col,
            color=color_col if color_col else None,
            title=config.get('title', f'{y_col} over {x_col}')
        )
        
        return fig
    
    def create_metric_card(self, value, title, delta=None):
        """Create a metric display card"""
        return {
            'value': value,
            'title': title,
            'delta': delta
        }
    
    def get_suitable_columns(self, df, chart_type):
        """Get columns suitable for specific chart type"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        recommendations = {
            'Line Chart': {
                'x_column': datetime_cols + numeric_cols + categorical_cols,
                'y_column': numeric_cols,
                'color_column': categorical_cols
            },
            'Bar Chart': {
                'x_column': categorical_cols + numeric_cols,
                'y_column': numeric_cols,
                'color_column': categorical_cols
            },
            'Scatter Plot': {
                'x_column': numeric_cols,
                'y_column': numeric_cols,
                'color_column': categorical_cols,
                'size_column': numeric_cols
            },
            'Histogram': {
                'x_column': numeric_cols,
                'color_column': categorical_cols
            },
            'Box Plot': {
                'x_column': categorical_cols,
                'y_column': numeric_cols,
                'color_column': categorical_cols
            },
            'Pie Chart': {
                'values_column': numeric_cols,
                'names_column': categorical_cols
            },
            'Heatmap': {
                'suitable': len(numeric_cols) >= 2
            },
            'Area Chart': {
                'x_column': datetime_cols + numeric_cols + categorical_cols,
                'y_column': numeric_cols,
                'color_column': categorical_cols
            }
        }
        
        return recommendations.get(chart_type, {})
