import pandas as pd
import streamlit as st
from io import BytesIO

class DataProcessor:
    """Handles data loading, processing, and manipulation operations"""
    
    def __init__(self):
        pass
    
    def load_file(self, uploaded_file):
        """Load CSV or Excel file and return pandas DataFrame"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                # Try different encodings for CSV files
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
            
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Basic data cleaning
            df = self._clean_data(df)
            
            return df
            
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
    
    def _clean_data(self, df):
        """Perform basic data cleaning operations"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Strip whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
        
        # Convert numeric strings to numbers where possible
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Attempt to convert to numeric safely
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    # Only convert if we didn't lose too much data
                    non_null_count = numeric_series.count()
                    if non_null_count > len(df[col]) * 0.5:
                        df[col] = numeric_series
                except:
                    pass
        
        return df
    
    def get_column_info(self, df):
        """Get detailed information about DataFrame columns"""
        info = []
        for col in df.columns:
            col_type = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            unique_count = df[col].nunique()
            
            info.append({
                'Column': col,
                'Type': col_type,
                'Null Count': null_count,
                'Unique Values': unique_count,
                'Sample Values': df[col].dropna().head(3).tolist()
            })
        
        return pd.DataFrame(info)
    
    def filter_data(self, df, filters):
        """Apply filters to DataFrame based on user input"""
        filtered_df = df.copy()
        
        for filter_config in filters:
            column = filter_config['column']
            operator = filter_config['operator']
            value = filter_config['value']
            
            if column not in df.columns:
                continue
            
            try:
                if operator == 'equals':
                    filtered_df = filtered_df[filtered_df[column] == value]
                elif operator == 'not_equals':
                    filtered_df = filtered_df[filtered_df[column] != value]
                elif operator == 'contains':
                    filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(str(value), na=False)]
                elif operator == 'greater_than':
                    filtered_df = filtered_df[filtered_df[column] > value]
                elif operator == 'less_than':
                    filtered_df = filtered_df[filtered_df[column] < value]
                elif operator == 'between':
                    if isinstance(value, list) and len(value) == 2:
                        filtered_df = filtered_df[(filtered_df[column] >= value[0]) & (filtered_df[column] <= value[1])]
            except Exception as e:
                st.error(f"Error applying filter to column {column}: {str(e)}")
        
        return filtered_df
    
    def get_summary_stats(self, df):
        """Generate summary statistics for the DataFrame"""
        stats = {}
        
        # Numeric columns statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats['numeric'] = df[numeric_cols].describe()
        
        # Categorical columns statistics
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            cat_stats = {}
            for col in categorical_cols:
                cat_stats[col] = {
                    'unique_count': df[col].nunique(),
                    'most_frequent': df[col].mode().iloc[0] if not df[col].empty else None,
                    'frequency': df[col].value_counts().head()
                }
            stats['categorical'] = cat_stats
        
        return stats
    
    def handle_missing_values(self, df, fill_config):
        """Handle missing values based on user configuration"""
        df_cleaned = df.copy()
        
        for column, method in fill_config.items():
            if column not in df_cleaned.columns:
                continue
            
            # Track processing for debugging
            missing_before = df_cleaned[column].isnull().sum()
                
            if method['type'] == 'mean':
                # Handle numeric columns
                if pd.api.types.is_numeric_dtype(df_cleaned[column]):
                    mean_val = df_cleaned[column].mean()
                    df_cleaned[column] = df_cleaned[column].fillna(mean_val)
            
            elif method['type'] == 'median':
                # Handle numeric columns
                if pd.api.types.is_numeric_dtype(df_cleaned[column]):
                    median_val = df_cleaned[column].median()
                    df_cleaned[column] = df_cleaned[column].fillna(median_val)
            
            elif method['type'] == 'mode':
                mode_values = df_cleaned[column].mode()
                if not mode_values.empty:
                    mode_val = mode_values.iloc[0]
                    df_cleaned[column] = df_cleaned[column].fillna(mode_val)
            
            elif method['type'] == 'custom':
                custom_value = method.get('value', '')
                if custom_value != '':
                    # Convert custom value to appropriate type
                    if pd.api.types.is_numeric_dtype(df_cleaned[column]):
                        try:
                            if df_cleaned[column].dtype == 'int64':
                                custom_value = int(float(custom_value))
                            else:
                                custom_value = float(custom_value)
                        except (ValueError, TypeError):
                            custom_value = 0
                    
                    df_cleaned[column] = df_cleaned[column].fillna(custom_value)
            
            elif method['type'] == 'drop':
                df_cleaned = df_cleaned.dropna(subset=[column])
        
        return df_cleaned
    
    def add_calculated_column(self, df, column_name, formula, column_references):
        """Add a calculated column based on formula and referenced columns"""
        df_with_calc = df.copy()
        
        try:
            # Replace column references in formula with actual column names
            working_formula = formula
            for ref, actual_col in column_references.items():
                working_formula = working_formula.replace(ref, f"df_with_calc['{actual_col}']")
            
            # Evaluate the formula safely
            df_with_calc[column_name] = eval(working_formula)
            return df_with_calc, None
            
        except Exception as e:
            return df, f"Error in formula: {str(e)}"
    
    def drop_columns(self, df, columns_to_drop):
        """Drop specified columns from DataFrame"""
        df_modified = df.copy()
        existing_columns = [col for col in columns_to_drop if col in df_modified.columns]
        if existing_columns:
            df_modified = df_modified.drop(columns=existing_columns)
        return df_modified
    
    def get_missing_value_summary(self, df):
        """Get comprehensive summary of missing values"""
        missing_info = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            total_count = len(df)
            missing_info[col] = {
                'missing_count': missing_count,
                'total_count': total_count,
                'missing_percentage': (missing_count / total_count * 100) if total_count > 0 else 0,
                'data_type': str(df[col].dtype),
                'has_missing': missing_count > 0
            }
        return missing_info
