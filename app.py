import streamlit as st
import pandas as pd
from utils.data_processor import DataProcessor
from utils.dashboard_builder import DashboardBuilder
from utils.chatbot import DataChatbot
from utils.report_generator import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'dashboard_config' not in st.session_state:
    st.session_state.dashboard_config = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_openai_key' not in st.session_state:
    st.session_state.user_openai_key = ""
if 'user_gemini_key' not in st.session_state:
    st.session_state.user_gemini_key = ""
if 'api_keys_configured' not in st.session_state:
    st.session_state.api_keys_configured = False

# Initialize components
data_processor = DataProcessor()
dashboard_builder = DashboardBuilder()
chatbot = DataChatbot()
report_generator = ReportGenerator()

# Check if API keys are configured, if not show setup screen
import os

def has_api_keys():
    """Check if Gemini API keys are available from environment or user input"""
    env_gemini = os.getenv("GEMINI_API_KEY", "")
    user_gemini = st.session_state.get('user_gemini_key', '')
    
    return bool(env_gemini or user_gemini)

# Show API setup screen if no keys are configured
if not has_api_keys() and not st.session_state.api_keys_configured:
    st.title("🔑 Gemini API Key Setup")
    st.markdown("To use the AI Data Chat features, please provide your Gemini API key:")
    
    st.subheader("🔮 Gemini API Key")
    st.markdown("For Google AI-powered data analysis and chat")
    gemini_key = st.text_input(
        "Enter Gemini API Key:",
        type="password", 
        placeholder="AI...",
        help="Get your API key from https://makersuite.google.com/app/apikey"
    )
    
    if gemini_key:
        st.session_state.user_gemini_key = gemini_key
    
    st.markdown("---")
    st.info("💡 You can also skip this step and set GEMINI_API_KEY as an environment variable")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Continue with Gemini", disabled=not gemini_key):
            st.session_state.api_keys_configured = True
            st.success("✅ Gemini API key configured! Refreshing app...")
            st.rerun()
    
    with col2:
        if st.button("⏭️ Skip (No AI Features)"):
            st.session_state.api_keys_configured = True
            st.warning("⚠️ AI features will be disabled without API keys")
            st.rerun()
    
    st.stop()

# Main app interface
st.title("📊 Analytics Platform")
st.markdown("Build custom dashboards and chat with your data using AI")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Select a page:",
    ["Data Upload", "Data Cleaning", "Dashboard Builder", "AI Data Chat", "Reports"]
)

# Data Upload Page
if page == "Data Upload":
    st.header("📁 Data Upload & Processing")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your data file to get started"
    )
    
    if uploaded_file is not None:
        try:
            # Process the uploaded file
            data = data_processor.load_file(uploaded_file)
            st.session_state.data = data
            
            st.success(f"✅ File uploaded successfully! Shape: {data.shape}")
            
            # Display data preview
            st.subheader("Data Preview")
            st.dataframe(data.head(10), use_container_width=True)
            
            # Data summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Data Info")
                st.write(f"**Rows:** {data.shape[0]}")
                st.write(f"**Columns:** {data.shape[1]}")
                st.write(f"**Memory Usage:** {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            with col2:
                st.subheader("Column Types")
                st.write(data.dtypes.to_frame('Data Type'))
            
            # Data quality check
            st.subheader("Data Quality")
            missing_data = data.isnull().sum()
            if missing_data.sum() > 0:
                st.warning("⚠️ Missing values detected:")
                st.write(missing_data[missing_data > 0])
                
                # Missing values handler
                with st.expander("🔧 Handle Missing Values", expanded=False):
                    st.markdown("Configure how to handle missing values for each column:")
                    
                    fill_config = {}
                    columns_with_missing = missing_data[missing_data > 0].index.tolist()
                    
                    for col in columns_with_missing:
                        st.markdown(f"**{col}** ({missing_data[col]} missing values)")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fill_method = st.selectbox(
                                "Fill method",
                                ["Skip", "Mean", "Median", "Mode", "Custom Value", "Drop Rows"],
                                key=f"fill_method_{col}"
                            )
                        
                        with col2:
                            custom_value = ""
                            if fill_method == "Custom Value":
                                custom_value = st.text_input(
                                    "Custom value",
                                    key=f"custom_value_{col}"
                                )
                        
                        if fill_method != "Skip":
                            # Map fill method to proper type
                            method_map = {
                                "Mean": "mean",
                                "Median": "median", 
                                "Mode": "mode",
                                "Custom Value": "custom",
                                "Drop Rows": "drop"
                            }
                            fill_config[col] = {
                                'type': method_map.get(fill_method, fill_method.lower()),
                                'value': custom_value
                            }
                    
                    if st.button("Apply Missing Value Handling") and fill_config:
                        try:
                            cleaned_data = data_processor.handle_missing_values(data, fill_config)
                            st.session_state.data = cleaned_data
                            st.session_state.data_cleaned = True  # Flag to show export options
                            st.success("✅ Missing values handled successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error handling missing values: {str(e)}")
                
                # Show updated missing values status in real-time
                st.markdown("---")
                st.markdown("**Current Missing Values Status:**")
                for col in columns_with_missing:
                    current_missing = data[col].isnull().sum()
                    if current_missing == 0:
                        st.success(f"✅ {col}: No missing values")
                    else:
                        st.info(f"ℹ️ {col}: {current_missing} missing values remaining")
            else:
                st.success("✅ No missing values found")
            
            # Export section for processed data (appears after initial processing or cleaning)
            current_missing_total = data.isnull().sum().sum()
            if st.session_state.get('data_cleaned', False) or current_missing_total == 0:
                st.markdown("---")
                st.subheader("📤 Export Processed Data")
                st.info(f"📊 Current status: {current_missing_total:,} missing values in dataset")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📊 Export as CSV", key="export_processed_csv"):
                        try:
                            from io import BytesIO
                            from datetime import datetime
                            
                            csv_buffer = BytesIO()
                            data.to_csv(csv_buffer, index=False)
                            csv_buffer.seek(0)
                            
                            st.download_button(
                                label="⬇️ Download Processed CSV",
                                data=csv_buffer.getvalue(),
                                file_name=f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_processed_csv"
                            )
                            st.success("✅ CSV export ready!")
                        except Exception as e:
                            st.error(f"❌ Error exporting CSV: {str(e)}")
                
                with col2:
                    if st.button("📋 Export as Excel", key="export_processed_excel"):
                        try:
                            from io import BytesIO
                            from datetime import datetime
                            
                            # Convert data to CSV for download (Excel export is complex)
                            csv_buffer = BytesIO()
                            data.to_csv(csv_buffer, index=False)
                            csv_buffer.seek(0)
                            
                            st.download_button(
                                label="⬇️ Download as CSV (Excel compatible)",
                                data=csv_buffer.getvalue(),
                                file_name=f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_processed_csv_excel"
                            )
                            st.success("✅ CSV export ready! (Can be opened in Excel)")
                        except Exception as e:
                            st.error(f"❌ Error exporting file: {str(e)}")
                
                with col3:
                    if st.button("🔄 Refresh Status", key="refresh_missing_values"):
                        st.rerun()
                                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    elif st.session_state.data is not None:
        st.info("📊 Data already loaded. Upload a new file to replace it.")
        st.subheader("Current Data Preview")
        st.dataframe(st.session_state.data.head(5), use_container_width=True)
        
        # Data cleaning section for existing data
        st.markdown("---")
        st.subheader("🔧 Data Cleaning")
        
        current_data = st.session_state.data
        missing_data = current_data.isnull().sum()
        
        if missing_data.sum() > 0:
            st.warning(f"⚠️ {missing_data.sum()} missing values found across {len(missing_data[missing_data > 0])} columns")
            
            with st.expander("Handle Missing Values", expanded=False):
                st.markdown("Configure how to handle missing values for each column:")
                
                fill_config = {}
                columns_with_missing = missing_data[missing_data > 0].index.tolist()
                
                for col in columns_with_missing:
                    st.markdown(f"**{col}** ({missing_data[col]} missing values)")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fill_method = st.selectbox(
                            "Fill method",
                            ["Skip", "Mean", "Median", "Mode", "Custom Value", "Drop Rows"],
                            key=f"existing_fill_method_{col}"
                        )
                    
                    with col2:
                        custom_value = ""
                        if fill_method == "Custom Value":
                            custom_value = st.text_input(
                                "Custom value",
                                key=f"existing_custom_value_{col}"
                            )
                    
                    if fill_method != "Skip":
                        # Map fill method to proper type
                        method_map = {
                            "Mean": "mean",
                            "Median": "median", 
                            "Mode": "mode",
                            "Custom Value": "custom",
                            "Drop Rows": "drop"
                        }
                        fill_config[col] = {
                            'type': method_map.get(fill_method, fill_method.lower()),
                            'value': custom_value
                        }
                
                if st.button("Apply Missing Value Handling", key="existing_data_cleaning") and fill_config:
                    try:
                        cleaned_data = data_processor.handle_missing_values(current_data, fill_config)
                        st.session_state.data = cleaned_data
                        st.session_state.data_cleaned = True  # Flag to show export options
                        st.success("✅ Missing values handled successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error handling missing values: {str(e)}")
                
                # Show updated missing values status in real-time
                st.markdown("---")
                st.markdown("**Current Missing Values Status:**")
                for col in columns_with_missing:
                    current_missing = current_data[col].isnull().sum()
                    if current_missing == 0:
                        st.success(f"✅ {col}: No missing values")
                    else:
                        st.info(f"ℹ️ {col}: {current_missing} missing values remaining")
        else:
            st.success("✅ No missing values found in current data")
        
        # Export cleaned data section
        if st.session_state.get('data_cleaned', False) or missing_data.sum() == 0:
            st.markdown("---")
            st.subheader("📤 Export Cleaned Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Export as CSV", key="export_csv_cleaned"):
                    try:
                        from io import BytesIO
                        from datetime import datetime
                        
                        csv_buffer = BytesIO()
                        current_data.to_csv(csv_buffer, index=False)
                        csv_buffer.seek(0)
                        
                        st.download_button(
                            label="⬇️ Download Cleaned CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="download_csv_cleaned"
                        )
                        st.success("✅ CSV export ready!")
                    except Exception as e:
                        st.error(f"❌ Error exporting CSV: {str(e)}")
            
            with col2:
                if st.button("📋 Export as CSV (Excel Compatible)", key="export_excel_cleaned"):
                    try:
                        from io import BytesIO
                        from datetime import datetime
                        
                        csv_buffer = BytesIO()
                        current_data.to_csv(csv_buffer, index=False)
                        csv_buffer.seek(0)
                        
                        st.download_button(
                            label="⬇️ Download CSV (Excel Compatible)",
                            data=csv_buffer.getvalue(),
                            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="download_csv_excel_cleaned"
                        )
                        st.success("✅ CSV export ready! (Opens in Excel)")
                    except Exception as e:
                        st.error(f"❌ Error exporting file: {str(e)}")
            
            with col3:
                if st.button("📊 Show Data Summary", key="show_summary_cleaned"):
                    st.markdown("**Cleaned Data Summary:**")
                    st.write(f"**Rows:** {current_data.shape[0]:,}")
                    st.write(f"**Columns:** {current_data.shape[1]}")
                    total_missing = current_data.isnull().sum().sum()
                    st.write(f"**Missing Values:** {total_missing:,}")
                    
                    if total_missing == 0:
                        st.success("🎉 Dataset is now complete with no missing values!")
                    else:
                        st.info(f"📊 {total_missing:,} missing values remaining")
                    
                    # Show data types
                    st.markdown("**Data Types:**")
                    st.write(current_data.dtypes.to_frame('Type'))

# Data Cleaning Page
elif page == "Data Cleaning":
    st.header("🧹 Data Cleaning ")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Upload page.")
    else:
        data = st.session_state.data
        
        # Initialize session state for cleaned data if not exists
        if 'cleaned_data' not in st.session_state:
            st.session_state.cleaned_data = data.copy()
        
        # Tabs for different operations
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Missing Values", 
            "➕ Add Column", 
            "🗑️ Drop Columns", 
            "💾 Export Data",
            "⚙️ AI Settings"
        ])
        
        with tab1:
            st.subheader("Missing Values Analysis & Treatment")
            
            # Get missing value summary
            missing_summary = data_processor.get_missing_value_summary(st.session_state.cleaned_data)
            
            # Display summary
            st.write("**Missing Values Summary:**")
            summary_data = []
            for col, info in missing_summary.items():
                if info['has_missing']:
                    summary_data.append({
                        'Column': col,
                        'Missing Count': info['missing_count'],
                        'Total Rows': info['total_count'],
                        'Missing %': f"{info['missing_percentage']:.1f}%",
                        'Data Type': info['data_type']
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Real-time missing value handling
                st.write("**Configure Missing Value Treatment:**")
                fill_config = {}
                
                for col, info in missing_summary.items():
                    if info['has_missing']:
                        with st.expander(f"🔧 {col} ({info['missing_count']} missing values)"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                method_options = ["Skip", "Mean", "Median", "Mode", "Custom Value", "Drop Rows"]
                                if not pd.api.types.is_numeric_dtype(st.session_state.cleaned_data[col]):
                                    method_options = ["Skip", "Mode", "Custom Value", "Drop Rows"]
                                
                                fill_method = st.selectbox(
                                    f"Treatment method for {col}:",
                                    method_options,
                                    key=f"method_{col}"
                                )
                            
                            with col2:
                                custom_value = ""
                                if fill_method == "Custom Value":
                                    custom_value = st.text_input(
                                        "Custom value:",
                                        key=f"custom_{col}"
                                    )
                            
                            # Apply immediately button for each column
                            if st.button(f"Apply to {col}", key=f"apply_{col}"):
                                if fill_method != "Skip":
                                    method_map = {
                                        "Mean": "mean",
                                        "Median": "median", 
                                        "Mode": "mode",
                                        "Custom Value": "custom",
                                        "Drop Rows": "drop"
                                    }
                                    single_config = {
                                        col: {
                                            'type': method_map.get(fill_method, fill_method.lower()),
                                            'value': custom_value
                                        }
                                    }
                                    try:
                                        st.session_state.cleaned_data = data_processor.handle_missing_values(
                                            st.session_state.cleaned_data, single_config
                                        )
                                        st.success(f"✅ Applied {fill_method} to {col}!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")
                
                # Apply all missing value treatments
                st.write("**Apply All Treatments:**")
                if st.button("🚀 Apply All Missing Value Treatments", type="primary"):
                    all_config = {}
                    for col, info in missing_summary.items():
                        if info['has_missing']:
                            method_key = f"method_{col}"
                            custom_key = f"custom_{col}"
                            if method_key in st.session_state:
                                fill_method = st.session_state[method_key]
                                if fill_method != "Skip":
                                    method_map = {
                                        "Mean": "mean",
                                        "Median": "median", 
                                        "Mode": "mode",
                                        "Custom Value": "custom",
                                        "Drop Rows": "drop"
                                    }
                                    all_config[col] = {
                                        'type': method_map.get(fill_method, fill_method.lower()),
                                        'value': st.session_state.get(custom_key, "")
                                    }
                    
                    if all_config:
                        try:
                            st.session_state.cleaned_data = data_processor.handle_missing_values(
                                st.session_state.cleaned_data, all_config
                            )
                            st.success("✅ All missing value treatments applied!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            else:
                st.success("🎉 No missing values found in your data!")
            
            # Real-time status refresh
            if st.button("🔄 Refresh Status"):
                st.rerun()
        
        with tab2:
            st.subheader("Add New Calculated Column ")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                new_column_name = st.text_input("New Column Name:", placeholder="e.g., Total_Cost")
                
                st.write("**Available Columns:**")
                available_cols = list(st.session_state.cleaned_data.columns)
                for i, col in enumerate(available_cols):
                    st.write(f"A{i+1}: {col}")
            
            with col2:
                formula = st.text_area(
                    "Formula (use A1, A2, etc. for columns):",
                    placeholder="e.g., A1 + A2 * 0.1\ne.g., A3 / A4\ne.g., (A1 + A2) * A3",
                    height=100
                )
                
                st.write("**Formula Examples:**")
                st.code("A1 + A2        # Add two columns")
                st.code("A1 * 1.1       # Multiply by constant")
                st.code("(A1 + A2) / A3 # Complex calculation")
            
            if st.button("➕ Add Calculated Column") and new_column_name and formula:
                try:
                    # Create column references mapping
                    column_refs = {}
                    for i, col in enumerate(available_cols):
                        column_refs[f"A{i+1}"] = col
                    
                    cleaned_data_with_calc, error = data_processor.add_calculated_column(
                        st.session_state.cleaned_data, new_column_name, formula, column_refs
                    )
                    
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.session_state.cleaned_data = cleaned_data_with_calc
                        st.success(f"✅ Added column '{new_column_name}'!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error creating column: {str(e)}")
        
        with tab3:
            st.subheader("Drop Columns")
            
            columns_to_drop = st.multiselect(
                "Select columns to remove:",
                options=list(st.session_state.cleaned_data.columns),
                help="Choose columns you want to remove from the dataset"
            )
            
            if columns_to_drop:
                st.write(f"**Columns to drop:** {', '.join(columns_to_drop)}")
                
                if st.button("🗑️ Drop Selected Columns", type="secondary"):
                    try:
                        st.session_state.cleaned_data = data_processor.drop_columns(
                            st.session_state.cleaned_data, columns_to_drop
                        )
                        st.success(f"✅ Dropped {len(columns_to_drop)} columns!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error dropping columns: {str(e)}")
        
        with tab4:
            st.subheader("Export Cleaned Data")
            
            # Show current data preview
            st.write("**Current Dataset Preview:**")
            st.write(f"**Shape:** {st.session_state.cleaned_data.shape[0]} rows × {st.session_state.cleaned_data.shape[1]} columns")
            st.dataframe(st.session_state.cleaned_data.head(), use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Export as CSV"):
                    try:
                        from io import BytesIO
                        from datetime import datetime
                        
                        csv_buffer = BytesIO()
                        st.session_state.cleaned_data.to_csv(csv_buffer, index=False)
                        csv_buffer.seek(0)
                        
                        st.download_button(
                            label="⬇️ Download Cleaned CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        st.success("✅ CSV export ready!")
                    except Exception as e:
                        st.error(f"❌ Error exporting CSV: {str(e)}")
            
            with col2:
                if st.button("💾 Update Main Dataset"):
                    st.session_state.data = st.session_state.cleaned_data.copy()
                    st.success("✅ Main dataset updated with cleaned data!")
                    st.info("You can now use the cleaned data in Dashboard Builder and AI Chat.")
        
        with tab5:
            st.subheader("🤖 AI Settings")
            st.write("Configure your AI API keys to enable enhanced features like intelligent data analysis and smart insights.")
            
            # Check for existing environment variables
            import os
            env_openai = os.getenv('OPENAI_API_KEY', '')
            env_gemini = os.getenv('GEMINI_API_KEY', '')
            
            # OpenAI Configuration
            st.write("**OpenAI Configuration:**")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if env_openai:
                    st.info("🔑 OpenAI API key is already set in environment variables.")
                    st.write("Current status: ✅ Available")
                else:
                    openai_key = st.text_input(
                        "OpenAI API Key:",
                        value=st.session_state.user_openai_key,
                        type="password",
                        help="Enter your OpenAI API key to enable GPT-powered features",
                        placeholder="sk-..."
                    )
                    
                    if openai_key != st.session_state.user_openai_key:
                        st.session_state.user_openai_key = openai_key
                    
                    if st.session_state.user_openai_key:
                        st.success("✅ OpenAI key configured (session only)")
                    else:
                        st.warning("⚠️ No OpenAI key provided")
            
            with col2:
                if st.button("Test OpenAI"):
                    try:
                        import openai
                        api_key = env_openai or st.session_state.user_openai_key
                        if api_key:
                            # Test with a simple API call
                            client = openai.OpenAI(api_key=api_key)
                            response = client.models.list()
                            st.success("✅ OpenAI connection successful!")
                        else:
                            st.error("❌ No API key provided")
                    except Exception as e:
                        st.error(f"❌ OpenAI test failed: {str(e)}")
            
            st.markdown("---")
            
            # Gemini Configuration
            st.write("**Google Gemini Configuration:**")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if env_gemini:
                    st.info("🔑 Gemini API key is already set in environment variables.")
                    st.write("Current status: ✅ Available")
                else:
                    gemini_key = st.text_input(
                        "Gemini API Key:",
                        value=st.session_state.user_gemini_key,
                        type="password",
                        help="Enter your Google Gemini API key to enable Gemini-powered features",
                        placeholder="AI..."
                    )
                    
                    if gemini_key != st.session_state.user_gemini_key:
                        st.session_state.user_gemini_key = gemini_key
                    
                    if st.session_state.user_gemini_key:
                        st.success("✅ Gemini key configured (session only)")
                    else:
                        st.warning("⚠️ No Gemini key provided")
            
            with col2:
                if st.button("Test Gemini"):
                    try:
                        from google import genai
                        api_key = env_gemini or st.session_state.user_gemini_key
                        if api_key:
                            # Test with a simple API call
                            client = genai.Client(api_key=api_key)
                            response = client.models.list()
                            st.success("✅ Gemini connection successful!")
                        else:
                            st.error("❌ No API key provided")
                    except Exception as e:
                        st.error(f"❌ Gemini test failed: {str(e)}")
            
            st.markdown("---")
            
            # AI Features Information
            st.write("**🚀 AI-Powered Features:**")
            st.info("""
            **With API keys configured, you can access:**
            - 🤖 **AI Data Chat**: Ask questions about your data in natural language
            - 📊 **Smart Insights**: Get automated analysis and recommendations
            - 🔍 **Intelligent Data Cleaning**: AI-suggested cleaning operations
            - 📈 **Auto-Generated Reports**: AI-powered report generation
            """)
            
            # Security Notice
            st.warning("""
            **🔒 Security Notice:**
            - API keys entered here are stored in session only (temporary)
            - Keys are not saved permanently or shared
            - For production use, set keys as environment variables
            - Never share your API keys with others
            """)

# Dashboard Builder Page
elif page == "Dashboard Builder":
    st.header("🎨 Dashboard Builder")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Upload page.")
    else:
        dashboard_builder.render_dashboard_builder(st.session_state.data)

# AI Data Chat Page
elif page == "AI Data Chat":
    st.header("🤖 AI Data Chat")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Upload page.")
    else:
        chatbot.render_chat_interface(st.session_state.data)

# Reports Page
elif page == "Reports":
    st.header("📄 Reports")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Upload page.")
    else:
        report_generator.render_report_interface(
            st.session_state.data,
            st.session_state.dashboard_config
        )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Analytics Platform v1.0**")
st.sidebar.markdown("Built with Streamlit")
