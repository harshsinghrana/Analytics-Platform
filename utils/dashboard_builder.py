import streamlit as st
import pandas as pd
from utils.visualization import Visualization

class DashboardBuilder:
    """Handles dashboard creation and management"""
    
    def __init__(self):
        self.viz = Visualization()
    
    def render_dashboard_builder(self, data):
        """Render the dashboard builder interface"""
        # Initialize dashboard config in session state
        if 'dashboard_config' not in st.session_state:
            st.session_state.dashboard_config = []
        
        # Dashboard controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Dashboard Components")
        
        with col2:
            if st.button("➕ Add Component", type="primary"):
                self._add_new_component()
        
        # Display existing components
        if st.session_state.dashboard_config:
            self._render_dashboard_components(data)
        else:
            st.info("🎯 Click 'Add Component' to start building your dashboard")
        
        # Dashboard actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Dashboard"):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Dashboard") and st.session_state.dashboard_config:
                st.session_state.dashboard_config = []
                st.rerun()
        
        with col3:
            if st.button("💾 Save Dashboard"):
                self._save_dashboard_config()
    
    def _add_new_component(self):
        """Add new component configuration"""
        new_component = {
            'id': len(st.session_state.dashboard_config),
            'type': 'chart',
            'chart_type': 'Bar Chart',
            'config': {},
            'title': f'Component {len(st.session_state.dashboard_config) + 1}'
        }
        st.session_state.dashboard_config.append(new_component)
        st.rerun()
    
    def _render_dashboard_components(self, data):
        """Render all dashboard components"""
        for i, component in enumerate(st.session_state.dashboard_config):
            with st.expander(f"📊 {component['title']}", expanded=True):
                self._render_single_component(data, component, i)
    
    def _render_single_component(self, data, component, index):
        """Render a single dashboard component"""
        col1, col2 = st.columns([3, 1])
        
        with col2:
            # Component controls
            if st.button("🗑️", key=f"delete_{index}", help="Delete component"):
                st.session_state.dashboard_config.pop(index)
                st.rerun()
            
            # Component type selection
            component_type = st.selectbox(
                "Type",
                ["chart", "metric", "table"],
                index=["chart", "metric", "table"].index(component.get('type', 'chart')),
                key=f"type_{index}"
            )
            component['type'] = component_type
        
        with col1:
            # Component title
            component['title'] = st.text_input(
                "Title",
                value=component.get('title', ''),
                key=f"title_{index}"
            )
            
            if component_type == 'chart':
                self._render_chart_component(data, component, index)
            elif component_type == 'metric':
                self._render_metric_component(data, component, index)
            elif component_type == 'table':
                self._render_table_component(data, component, index)
    
    def _render_chart_component(self, data, component, index):
        """Render chart component configuration and display"""
        # Chart type selection
        chart_type = st.selectbox(
            "Chart Type",
            self.viz.get_available_charts(),
            index=self.viz.get_available_charts().index(component.get('chart_type', 'Bar Chart')),
            key=f"chart_type_{index}"
        )
        component['chart_type'] = chart_type
        
        # Get suitable columns for this chart type
        suitable_cols = self.viz.get_suitable_columns(data, chart_type)
        
        # Chart configuration
        config = component.get('config', {})
        
        if chart_type in ['Line Chart', 'Bar Chart', 'Area Chart']:
            col1, col2 = st.columns(2)
            with col1:
                if 'x_column' in suitable_cols:
                    config['x_column'] = st.selectbox(
                        "X Column",
                        suitable_cols['x_column'],
                        key=f"x_col_{index}"
                    )
            with col2:
                if 'y_column' in suitable_cols:
                    config['y_column'] = st.selectbox(
                        "Y Column",
                        suitable_cols['y_column'],
                        key=f"y_col_{index}"
                    )
            
            if 'color_column' in suitable_cols and suitable_cols['color_column']:
                config['color_column'] = st.selectbox(
                    "Color Column (Optional)",
                    [None] + suitable_cols['color_column'],
                    key=f"color_col_{index}"
                )
        
        elif chart_type == 'Scatter Plot':
            col1, col2 = st.columns(2)
            with col1:
                config['x_column'] = st.selectbox(
                    "X Column",
                    suitable_cols.get('x_column', []),
                    key=f"x_col_{index}"
                )
                config['color_column'] = st.selectbox(
                    "Color Column (Optional)",
                    [None] + suitable_cols.get('color_column', []),
                    key=f"color_col_{index}"
                )
            with col2:
                config['y_column'] = st.selectbox(
                    "Y Column",
                    suitable_cols.get('y_column', []),
                    key=f"y_col_{index}"
                )
                config['size_column'] = st.selectbox(
                    "Size Column (Optional)",
                    [None] + suitable_cols.get('size_column', []),
                    key=f"size_col_{index}"
                )
        
        elif chart_type == 'Histogram':
            config['x_column'] = st.selectbox(
                "Column",
                suitable_cols.get('x_column', []),
                key=f"x_col_{index}"
            )
            config['bins'] = st.slider(
                "Number of Bins",
                10, 100, 30,
                key=f"bins_{index}"
            )
        
        elif chart_type == 'Box Plot':
            config['y_column'] = st.selectbox(
                "Y Column",
                suitable_cols.get('y_column', []),
                key=f"y_col_{index}"
            )
            config['x_column'] = st.selectbox(
                "X Column (Optional)",
                [None] + suitable_cols.get('x_column', []),
                key=f"x_col_{index}"
            )
        
        elif chart_type == 'Pie Chart':
            col1, col2 = st.columns(2)
            with col1:
                config['values_column'] = st.selectbox(
                    "Values Column",
                    suitable_cols.get('values_column', []),
                    key=f"values_col_{index}"
                )
            with col2:
                config['names_column'] = st.selectbox(
                    "Names Column",
                    suitable_cols.get('names_column', []),
                    key=f"names_col_{index}"
                )
        
        # Add data filtering options for charts
        st.markdown("**Data Filtering (Optional)**")
        col1, col2 = st.columns(2)
        
        with col1:
            config['limit_data'] = st.selectbox(
                "Limit Data",
                ["All data", "Top 5", "Top 10", "Top 20", "Top 50"],
                index=["All data", "Top 5", "Top 10", "Top 20", "Top 50"].index(config.get('limit_data', 'All data')),
                key=f"chart_limit_{index}"
            )
        
        with col2:
            if config.get('limit_data', 'All data') != 'All data':
                sortable_cols = data.select_dtypes(include=['number']).columns.tolist()
                if sortable_cols:
                    config['sort_by'] = st.selectbox(
                        "Sort by",
                        sortable_cols,
                        key=f"chart_sort_{index}"
                    )
                    config['sort_order'] = st.selectbox(
                        "Order",
                        ["Descending", "Ascending"],
                        key=f"chart_order_{index}"
                    )
        
        component['config'] = config
        
        # Display the chart
        try:
            # Apply data filtering if specified
            chart_data = data.copy()
            limit_data = config.get('limit_data', 'All data')
            
            if limit_data != 'All data':
                sort_by = config.get('sort_by')
                if sort_by and sort_by in chart_data.columns:
                    ascending = config.get('sort_order', 'Descending') == 'Ascending'
                    chart_data = chart_data.sort_values(by=sort_by, ascending=ascending)
                    
                    # Apply limit
                    if limit_data == "Top 5":
                        chart_data = chart_data.head(5)
                    elif limit_data == "Top 10":
                        chart_data = chart_data.head(10)
                    elif limit_data == "Top 20":
                        chart_data = chart_data.head(20)
                    elif limit_data == "Top 50":
                        chart_data = chart_data.head(50)
            
            if chart_type == 'Heatmap':
                if suitable_cols.get('suitable', False):
                    fig = self.viz.create_chart(chart_type, chart_data, config)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ Heatmap requires at least 2 numeric columns")
            else:
                fig = self.viz.create_chart(chart_type, chart_data, config)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Show data info if limited
            if limit_data != 'All data' and len(chart_data) < len(data):
                st.caption(f"Chart showing {len(chart_data):,} of {len(data):,} rows")
                
        except Exception as e:
            st.error(f"❌ Error creating chart: {str(e)}")
    
    def _render_metric_component(self, data, component, index):
        """Render metric component configuration and display"""
        config = component.get('config', {})
        
        # Metric configuration
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            st.warning("⚠️ No numeric columns available for metrics")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            config['column'] = st.selectbox(
                "Column",
                numeric_cols,
                key=f"metric_col_{index}"
            )
            
            config['aggregation'] = st.selectbox(
                "Aggregation",
                ["sum", "mean", "count", "min", "max", "median"],
                key=f"metric_agg_{index}"
            )
        
        with col2:
            config['format'] = st.selectbox(
                "Format",
                ["number", "currency", "percentage"],
                key=f"metric_format_{index}"
            )
        
        component['config'] = config
        
        # Calculate and display metric
        try:
            column = config.get('column')
            aggregation = config.get('aggregation', 'sum')
            format_type = config.get('format', 'number')
            
            if column and column in data.columns:
                # Calculate metric value
                if aggregation == 'sum':
                    value = data[column].sum()
                elif aggregation == 'mean':
                    value = data[column].mean()
                elif aggregation == 'count':
                    value = data[column].count()
                elif aggregation == 'min':
                    value = data[column].min()
                elif aggregation == 'max':
                    value = data[column].max()
                elif aggregation == 'median':
                    value = data[column].median()
                else:
                    value = 0
                
                # Format value
                if format_type == 'currency':
                    formatted_value = f"${value:,.2f}"
                elif format_type == 'percentage':
                    formatted_value = f"{value:.2%}"
                else:
                    formatted_value = f"{value:,.2f}"
                
                st.metric(
                    label=component['title'],
                    value=formatted_value
                )
            else:
                st.warning("⚠️ Please select a valid column for the metric")
        except Exception as e:
            st.error(f"❌ Error calculating metric: {str(e)}")
    
    def _render_table_component(self, data, component, index):
        """Render table component configuration and display"""
        config = component.get('config', {})
        
        # Table configuration
        col1, col2 = st.columns(2)
        
        with col1:
            config['columns'] = st.multiselect(
                "Select Columns",
                data.columns.tolist(),
                default=config.get('columns', data.columns.tolist()[:5]),
                key=f"table_cols_{index}"
            )
            
            # Limit options
            config['limit_type'] = st.selectbox(
                "Show",
                ["All rows", "Top 5", "Top 10", "Top 20", "Custom"],
                index=["All rows", "Top 5", "Top 10", "Top 20", "Custom"].index(config.get('limit_type', 'All rows')),
                key=f"table_limit_type_{index}"
            )
            
            if config['limit_type'] == "Custom":
                config['max_rows'] = st.slider(
                    "Max Rows",
                    10, 1000, config.get('max_rows', 100),
                    key=f"table_rows_{index}"
                )
        
        with col2:
            # Sorting options
            config['sort_column'] = st.selectbox(
                "Sort by Column (Optional)",
                [None] + data.columns.tolist(),
                index=0 if config.get('sort_column') is None else data.columns.tolist().index(config.get('sort_column')) + 1,
                key=f"table_sort_col_{index}"
            )
            
            if config['sort_column']:
                config['sort_order'] = st.selectbox(
                    "Sort Order",
                    ["Ascending", "Descending"],
                    index=["Ascending", "Descending"].index(config.get('sort_order', 'Ascending')),
                    key=f"table_sort_order_{index}"
                )
        
        component['config'] = config
        
        # Display table
        try:
            selected_cols = config.get('columns', [])
            
            if selected_cols:
                display_data = data[selected_cols].copy()
                
                # Apply sorting if specified
                sort_column = config.get('sort_column')
                if sort_column and sort_column in display_data.columns:
                    ascending = config.get('sort_order', 'Ascending') == 'Ascending'
                    display_data = display_data.sort_values(by=sort_column, ascending=ascending)
                
                # Apply row limit
                limit_type = config.get('limit_type', 'All rows')
                if limit_type == "Top 5":
                    display_data = display_data.head(5)
                elif limit_type == "Top 10":
                    display_data = display_data.head(10)
                elif limit_type == "Top 20":
                    display_data = display_data.head(20)
                elif limit_type == "Custom":
                    max_rows = config.get('max_rows', 100)
                    display_data = display_data.head(max_rows)
                
                st.dataframe(display_data, use_container_width=True)
                
                # Show info about the displayed data
                total_rows = len(data)
                displayed_rows = len(display_data)
                if displayed_rows < total_rows:
                    st.caption(f"Showing {displayed_rows:,} of {total_rows:,} rows")
            else:
                st.warning("⚠️ Please select at least one column")
        except Exception as e:
            st.error(f"❌ Error displaying table: {str(e)}")
    
    def _save_dashboard_config(self):
        """Save dashboard configuration"""
        if st.session_state.dashboard_config:
            st.success("✅ Dashboard configuration saved to session!")
            # In a real application, you would save this to a database or file
        else:
            st.warning("⚠️ No dashboard components to save")
