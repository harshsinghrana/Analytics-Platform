import streamlit as st
import pandas as pd
import json
import os
from google import genai
from google.genai import types

class DataChatbot:
    """AI-powered chatbot for data analysis and queries using Gemini"""
    
    def __init__(self):
        # Check for API keys from environment or session state
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    
    def _get_gemini_client(self):
        """Get Gemini client with user or environment API key"""
        # Check session state for user-provided keys
        user_gemini_key = st.session_state.get('user_gemini_key', '')
        
        # Use user key if provided, otherwise fall back to environment
        api_key = user_gemini_key if user_gemini_key else self.gemini_api_key
        
        if api_key:
            return genai.Client(api_key=api_key)
        return None
    
    def render_chat_interface(self, data):
        """Render the chat interface"""
        client = self._get_gemini_client()
        if not client:
            st.error("❌ Gemini API key not found. Please configure your API key in the startup screen.")
            st.info("💡 You can also set GEMINI_API_KEY as an environment variable.")
            return
        
        # Chat history
        st.subheader("💬 Chat with Your Data")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "data" in message and isinstance(message["data"], pd.DataFrame):
                    st.dataframe(message["data"], use_container_width=True)
                elif "data" in message and "chart" in str(message["data"]):
                    # Handle chart data if present
                    pass
        
        # Chat input
        if prompt := st.chat_input("Ask me about your data..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your data..."):
                    response = self._generate_response(prompt, data, client)
                    
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
                self._add_quick_query("Give me a summary of this dataset", data, client)
        
        with col2:
            if st.button("🔍 Missing Values"):
                self._add_quick_query("Show me missing values in the data", data, client)
        
        with col3:
            if st.button("📈 Correlations"):
                self._add_quick_query("Show correlations between numeric columns", data, client)
        
        with col4:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    def _add_quick_query(self, query, data, client):
        """Add a quick query to the chat"""
        st.session_state.chat_history.append({"role": "user", "content": query})
        response = self._generate_response(query, data, client)
        
        if response:
            st.write(response["text"])
            
            history_entry = {"role": "assistant", "content": response["text"]}
            
            if "data" in response:
                st.dataframe(response["data"], use_container_width=True)
                history_entry["data"] = response["data"]
            
            if "chart" in response:
                st.plotly_chart(response["chart"], use_container_width=True)
                history_entry["data"] = {"chart": response["chart"]}
            st.session_state.chat_history.append(history_entry)
        
        st.rerun()
    
    def _generate_response(self, query, data, client):
        """Generate AI response based on user query and data using Gemini"""
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
            
            Always respond in JSON format with the following structure:
            {{
                "text": "your analysis and insights",
                "action": "show_data|show_chart|none",
                "data_query": "pandas query if showing data",
                "chart_config": {{
                    "type": "line|bar|scatter|histogram|box|pie",
                    "x_column": "column_name",
                    "y_column": "column_name",
                    "title": "Chart Title"
                }}
            }}
            """
            
            # Use Gemini API
            if not client:
                return None
                
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"{system_prompt}\n\nUser query: {query}")])
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            content = response.text
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
                        if filtered_data is not None:
                            response_data["data"] = filtered_data
                    except Exception as e:
                        response_data["text"] += f"\n\nNote: Could not execute data query: {str(e)}"
            
            # Handle chart creation
            elif result.get("action") == "show_chart":
                chart_config = result.get("chart_config")
                if chart_config:
                    try:
                        chart = self._create_chart_from_config(data, chart_config)
                        if chart:
                            response_data["chart"] = chart
                    except Exception as e:
                        response_data["text"] += f"\n\nNote: Could not create chart: {str(e)}"
            
            return response_data
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return None
    
    def _get_data_context(self, data):
        """Get context information about the dataset"""
        context = f"""
        Dataset Shape: {data.shape[0]} rows, {data.shape[1]} columns
        
        Columns:
        {data.dtypes.to_string()}
        
        Sample Data:
        {data.head().to_string()}
        
        Missing Values:
        {data.isnull().sum().to_string()}
        """
        return context
    
    def _execute_data_query(self, data, query):
        """Execute a pandas query on the data"""
        try:
            # Simple query execution for common operations
            if "head" in query.lower():
                return data.head(10)
            elif "describe" in query.lower():
                return data.describe()
            elif "info" in query.lower():
                return pd.DataFrame({
                    'Column': data.columns,
                    'Type': data.dtypes,
                    'Non-Null Count': data.notna().sum(),
                    'Null Count': data.isnull().sum()
                })
            elif "missing" in query.lower() or "null" in query.lower():
                missing_data = data.isnull().sum()
                return missing_data[missing_data > 0].to_frame('Missing Values')
            else:
                # Try to execute as pandas query
                return data.query(query) if query else data.head()
        except Exception:
            return data.head()
    
    def _create_chart_from_config(self, data, chart_config):
        """Create chart based on AI-generated configuration"""
        try:
            from utils.visualization import Visualization
            viz = Visualization()
            
            chart_type = chart_config.get("type", "bar")
            x_col = chart_config.get("x_column")
            y_col = chart_config.get("y_column")
            title = chart_config.get("title", "Data Visualization")
            
            # Prepare config for visualization
            config = {
                "x_column": x_col,
                "y_column": y_col,
                "title": title
            }
            
            return viz.create_chart(chart_type, data, config)
        except Exception:
            return None
    
    def _get_data_summary(self, data):
        """Get data summary information"""
        summary = {
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": data.dtypes.to_dict(),
            "missing_values": data.isnull().sum().to_dict(),
            "numeric_summary": data.describe().to_dict() if not data.select_dtypes(include=['number']).empty else {}
        }
        return summary
    
    def _get_missing_values(self, data):
        """Get missing values information"""
        missing = data.isnull().sum()
        missing_info = missing[missing > 0].to_dict()
        return missing_info
    
    def _get_correlations(self, data):
        """Get correlation analysis"""
        try:
            numeric_data = data.select_dtypes(include=['number'])
            if numeric_data.empty:
                return "No numeric columns found for correlation analysis."
            
            correlations = numeric_data.corr()
            return correlations.to_dict()
        except Exception as e:
            return f"Error calculating correlations: {str(e)}"
