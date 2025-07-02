import streamlit as st
import pandas as pd
import json
import os
from openai import OpenAI

class DataChatbot:
    """AI-powered chatbot for data analysis and queries"""
    
    def __init__(self):
        self.openai_api_key = "your-openai-api-key"  # Replace with your OpenAI API key
        # Optionally set a custom OpenAI base URL
        self.openai_base_url = "base-url"
        
        if self.openai_api_key:
            # Initialize OpenAI client with custom base URL if provided
            if self.openai_base_url:
                self.client = OpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url)
            else:
                self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
    
    def render_chat_interface(self, data):
        """Render the chat interface"""
        if not self.client:
            st.error("❌ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            st.info("💡 Optional: You can also set OPENAI_BASE_URL if using a custom OpenAI-compatible endpoint.")
            return
        
        # Chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "data" in message:
                    if isinstance(message["data"], pd.DataFrame):
                        st.dataframe(message["data"], use_container_width=True)
                    elif isinstance(message["data"], dict) and "chart" in message["data"]:
                        st.plotly_chart(message["data"]["chart"], use_container_width=True)
        
        # Chat input
        if prompt := st.chat_input("Ask me about your data..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your data..."):
                    response = self._generate_response(prompt, data)
                    
                    if response:
                        st.write(response["text"])
                        
                        # Add response to chat history
                        history_entry = {"role": "assistant", "content": response["text"]}
                        
                        if "data" in response:
                            st.dataframe(response["data"], use_container_width=True)
                            history_entry["data"] = response["data"]
                        
                        if "chart" in response:
                            st.plotly_chart(response["chart"], use_container_width=True)
                            history_entry["data"] = {"chart": response["chart"]}
                        
                        st.session_state.chat_history.append(history_entry)
                    else:
                        error_msg = "I'm sorry, I couldn't process your request. Please try rephrasing your question."
                        st.write(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
        
        # Quick action buttons
        st.markdown("---")
        st.subheader("💡 Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Data Summary"):
                self._add_quick_query("Give me a summary of this dataset", data)
        
        with col2:
            if st.button("🔍 Missing Values"):
                self._add_quick_query("Show me missing values in the data", data)
        
        with col3:
            if st.button("📈 Correlations"):
                self._add_quick_query("Show correlations between numeric columns", data)
        
        with col4:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    def _add_quick_query(self, query, data):
        """Add a quick query to the chat"""
        st.session_state.chat_history.append({"role": "user", "content": query})
        response = self._generate_response(query, data)
        
        if response:
            history_entry = {"role": "assistant", "content": response["text"]}
            if "data" in response:
                history_entry["data"] = response["data"]
            if "chart" in response:
                history_entry["data"] = {"chart": response["chart"]}
            st.session_state.chat_history.append(history_entry)
        
        st.rerun()
    
    def _generate_response(self, query, data):
        """Generate AI response based on user query and data"""
        try:
            # Get data context
            data_context = self._get_data_context(data)
            
            # Create system prompt
            system_prompt = f"""You are a data analyst assistant. You have access to a dataset with the following information:
            
            {data_context}
            
            Based on user queries, you should:
            1. Analyze the data and provide insights
            2. Suggest appropriate visualizations
            3. Answer questions about the data
            4. Provide data summaries and statistics
            
            Respond in JSON format with the following structure:
            {{
                "text": "Your response text",
                "action": "none|show_data|create_chart",
                "data_query": "pandas query if needed",
                "chart_config": {{
                    "type": "chart_type",
                    "config": {{}}
                }}
            }}
            """
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            if not self.client:
                return None
                
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
                
            result = json.loads(content)
            
            # Process the response
            response_data = {"text": result.get("text", "")}
            
            # Handle data operations
            if result.get("action") == "show_data":
                data_query = result.get("data_query")
                if data_query:
                    try:
                        filtered_data = self._execute_data_query(data, data_query)
                        response_data["data"] = filtered_data
                    except Exception as e:
                        response_data["text"] += f"\n\nNote: Could not execute data query: {str(e)}"
            
            # Handle chart creation
            elif result.get("action") == "create_chart":
                chart_config = result.get("chart_config", {})
                try:
                    chart = self._create_chart_from_config(data, chart_config)
                    if chart:
                        response_data["chart"] = chart
                except Exception as e:
                    response_data["text"] += f"\n\nNote: Could not create chart: {str(e)}"
            
            # Handle common queries directly
            if "summary" in query.lower() or "overview" in query.lower():
                response_data.update(self._get_data_summary(data))
            elif "missing" in query.lower() and "value" in query.lower():
                response_data.update(self._get_missing_values(data))
            elif "correlation" in query.lower():
                response_data.update(self._get_correlations(data))
            
            return response_data
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return None
    
    def _get_data_context(self, data):
        """Get context information about the dataset"""
        context = f"""
        Dataset shape: {data.shape[0]} rows, {data.shape[1]} columns
        
        Columns and types:
        {data.dtypes.to_string()}
        
        Sample data (first 3 rows):
        {data.head(3).to_string()}
        
        Numeric columns summary:
        {data.describe().to_string() if len(data.select_dtypes(include=['number']).columns) > 0 else 'No numeric columns'}
        """
        return context
    
    def _execute_data_query(self, data, query):
        """Execute a pandas query on the data"""
        # Simple query execution - in production, you'd want more security
        try:
            if query.startswith("data."):
                result = eval(query)
                if isinstance(result, pd.DataFrame):
                    return result.head(20)  # Limit results
                else:
                    return pd.DataFrame({"Result": [result]})
        except:
            pass
        
        return data.head(10)
    
    def _create_chart_from_config(self, data, chart_config):
        """Create chart based on AI-generated configuration"""
        from utils.visualization import Visualization
        viz = Visualization()
        
        chart_type = chart_config.get("type")
        config = chart_config.get("config", {})
        
        if chart_type and chart_type in viz.get_available_charts():
            return viz.create_chart(chart_type, data, config)
        
        return None
    
    def _get_data_summary(self, data):
        """Get data summary information"""
        summary_text = f"""
        **Dataset Summary:**
        - **Rows:** {data.shape[0]:,}
        - **Columns:** {data.shape[1]}
        - **Memory Usage:** {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB
        
        **Column Types:**
        """
        
        for dtype, count in data.dtypes.value_counts().items():
            summary_text += f"\n- {dtype}: {count} columns"
        
        # Missing values
        missing = data.isnull().sum()
        if missing.sum() > 0:
            summary_text += f"\n\n**Missing Values:** {missing.sum():,} total"
        else:
            summary_text += "\n\n**Missing Values:** None"
        
        return {"text": summary_text, "data": data.describe() if len(data.select_dtypes(include=['number']).columns) > 0 else None}
    
    def _get_missing_values(self, data):
        """Get missing values information"""
        missing = data.isnull().sum()
        missing_df = missing[missing > 0].to_frame('Missing Count')
        missing_df['Percentage'] = (missing_df['Missing Count'] / len(data) * 100).round(2)
        
        if len(missing_df) > 0:
            text = f"Found missing values in {len(missing_df)} columns:"
            return {"text": text, "data": missing_df}
        else:
            return {"text": "No missing values found in the dataset! 🎉"}
    
    def _get_correlations(self, data):
        """Get correlation analysis"""
        numeric_cols = data.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) < 2:
            return {"text": "Need at least 2 numeric columns to calculate correlations."}
        
        corr_matrix = data[numeric_cols].corr()
        
        # Find strongest correlations
        correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                correlations.append({
                    'Column 1': col1,
                    'Column 2': col2,
                    'Correlation': round(corr_value, 3)
                })
        
        correlations_df = pd.DataFrame(correlations)
        correlations_df = correlations_df.reorder_levels([0]).sort_values('Correlation', key=abs, ascending=False)
        
        text = "**Correlation Analysis:**\n\nStrongest correlations between numeric columns:"
        
        return {"text": text, "data": correlations_df.head(10)}
