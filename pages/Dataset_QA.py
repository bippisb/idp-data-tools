import streamlit as st
import pandas as pd
import base64
import urllib.parse
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

def get_special_char_count(column):
    if column.dtype == "object":
        special_chars = [char for char in column.unique() if not str(char).isalnum()]
        return special_chars
    return 0

def generate_dqa_info(data, col, special_chars):
    dqa_info = f"### Column: {col}\n"
    dqa_info += f"Data Type: {data[col].dtype}\n"
    dqa_info += f"Number of Numerical Values: {data[col].apply(pd.to_numeric, errors='coerce').notnull().sum()}\n"
    dqa_info += f"Number of NaN Values: {data[col].isnull().sum()}\n"
    dqa_info += f"Count of Unique Values: {data[col].nunique()}\n"
    dqa_info += f"Count of Special Characters: {len(special_chars) if special_chars is not None and isinstance(special_chars, list) else 0}\n"
    dqa_info += f"Unique Values: {', '.join(map(str, data[col].unique()))}\n\n"

     # Include formatting details if applicable
    if col == "state_code" or col == "district_code" or col == "block_code" or col == "gp_code"  or col == "village_code" or col == "sub_district_code" or col == "subdistrict_code":
        dqa_info += f"Formatting: {col} values were formatted to have leading zeros.\n"
    
    dqa_info += "\n"
    return dqa_info

def generate_dqa_special_chars_info(col, special_chars):
    if special_chars:
        dqa_info = f"### Column: {col}\n"
        dqa_info += f"Special Character Values: {', '.join(map(str, special_chars))}\n\n"
        return dqa_info
    return ""

def generate_dqa_duplicate_info(duplicate_count):
    return f"## Number of Duplicate Rows\nNumber of Duplicate Rows: {duplicate_count}\n\n"

def generate_dqa_changes_summary(changes):
    dqa_info = "## Data Type Changes and Other Changes Summary\n"
    for col, change in changes.items():
        dqa_info += f"Column/Change: {col}\nChange: {change}\n\n"
    return dqa_info

def generate_dqa_summary_statistics(summary_statistics):
    dqa_info = "## Summary Statistics for Numerical Columns\n"
    # Use to_string() to format the table
    dqa_info += summary_statistics.to_string()  
    dqa_info += "\n\n"
    return dqa_info

def get_download_link(file_name, content_type):
    with open(file_name, "rb") as f:
        data = f.read()
    base64_data = base64.b64encode(data).decode("utf-8")
    encoded_file_name = urllib.parse.quote(file_name)
    href = f"<a href='data:{content_type};base64,{base64_data}' download='{encoded_file_name}'>Download {file_name}</a>"
    return href

# Update the 'date' column to the desired format
def convert_to_desired_format(date_str):
    try:
        # Try to parse the input date using different formats
        formats = ["%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%m-%Y", "%d-%m-%Y", "%Y", "%d-%b-%Y", "%m/%d/%Y",
                   "%d/%m/%Y", "%Y.%m.%d", "%m/%d/%y", "%d/%m/%y", "%b %d, %Y", "%d-%m-%y", "%Y/%m/%d"]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%d-%m-%Y")
            except ValueError:
                pass
        
        return "Invalid Date"
    except Exception as e:
        return "Error: " + str(e)


def process_column(data,col,special_char_counts, dqa_report, changes):
    # Process each column
    st.write(f"### Column: {col}")
    st.write(f"Data Type: {data[col].dtype}")
    st.write(f"Number of Numerical Values: {data[col].apply(pd.to_numeric, errors='coerce').notnull().sum()}")
    st.write(f"Number of NaN Values: {data[col].isnull().sum()}")
    st.write(f"Count of Unique Values: {data[col].nunique()}")
    if data[col].nunique() > 50:
        st.write(f"Unique Values: {data[col].unique()[:30]}...")
    else:
        st.write(f"Unique Values: {data[col].unique()}")
    
    special_chars = special_char_counts[col]

    # Perform other specific operations on the column data
    format_rules = {
        "state_code": 2, "district_code": 3, "sub_district_code": 4,
        "block_code": 4, "village_code": 6, "gp_code": 6
    }
    if col in format_rules:
        data[col] = data[col].apply(lambda x: str(int(x)).zfill(format_rules[col]) if pd.notna(x) else None)
        st.write(f"##### {col} values were formatted to have leading zeros.")
        st.write(f"Unique Values: {data[col].unique()}")    
    
    # Change datatype
    new_dtype = st.selectbox(f"Change Data Type for {col}:", ["No Change", "int", "float", "str", "date"], key=f"{col}_dtype")
    if new_dtype != "No Change":
        try:
            if new_dtype == "date":
                data[col] = data[col].astype(str).apply(lambda date: convert_to_desired_format(date) if pd.notna(date) else None)
                changes[col] = f"Data Type Changed to {new_dtype} (Format: dd-mm-yyyy)"
                st.write(f"###### Data Type Changed to {new_dtype} (Format: dd-mm-yyyy)")
            elif new_dtype == "int":
                valid_format_mask = data[col].notnull()
                data[col] = data.loc[valid_format_mask, col].astype(new_dtype)
                changes[col] = f"Data Type Changed to {new_dtype}"
                st.write(f"###### Data Type Changed to {new_dtype}")
            elif new_dtype == "float":
                valid_format_mask = data[col].notnull()
                data[col] = data.loc[valid_format_mask, col].astype(new_dtype)
                data[col] = data[col].apply(lambda x: round(x, 3) if pd.notna(x) else None)
                changes[col] = f"Data Type Changed to {new_dtype}"
                st.write(f"###### Data Type Changed to {new_dtype}")
        except Exception as e:
            changes[col] = f"Error-{e}: Unable to change data type"
            st.write(f"Unable to change data type for {col} because of {e}")

    if isinstance(special_chars, list):
        st.write(f"Count of Special Characters: {len(special_chars)}")
        if len(special_chars) > 30:
            st.write(f"Special Character Values: {special_chars[:30]}...")
        else:
            st.write(f"Special Character Values: {special_chars}")
    else:
        st.write("Count of Special Characters: 0")
    
    # drop column

def main():
    """
    The main function of the app that handles the dataset QA process.
    Parameters:
    None
    Returns:
    None
    """
    st.set_page_config(page_title="Dataset QA")
    try:
        st.title("Dataset QA App")
        
        uploaded_file = st.file_uploader("Upload a data file", type=["csv", "parquet"])

        file_name = ""
        data = None
        if uploaded_file:
            file_name = uploaded_file.name.split(".")[0]
            data = pd.read_parquet(uploaded_file) if uploaded_file.name.endswith(".parquet") else pd.read_csv(uploaded_file)
            
            st.write("## Dataset Preview")
            st.dataframe(data.head())
            
            st.write("## Dataset Information")
            st.write(f"Number of Rows: {data.shape[0]}")
            st.write(f"Number of Columns: {data.shape[1]}")
            
            st.write("## Column Information")
            changes = {}
            special_chars_dict = {}
            dqa_report = "## Data Quality Assessment (DQA) Report\n\n"
            
            # Parallel Processing for special character counts
            with ThreadPoolExecutor(max_workers=4) as executor:
                special_char_counts = {col: get_special_char_count(data[col]) for col in data.columns}

            for col in data.columns:
                process_column(data, col, special_char_counts, dqa_report, changes)
                special_chars = special_char_counts[col]
                dqa_report += generate_dqa_info(data, col, special_chars)
                st.write("---")

            # Number of duplicate rows
            duplicate_count = data.duplicated().sum()
            st.write("## Number of Duplicate Rows")
            st.write(f"Number of Duplicate Rows: {duplicate_count}")

            dqa_report += generate_dqa_duplicate_info(duplicate_count)

            # Remove duplicate rows
            if st.button("Remove Duplicate Rows"):
                data.drop_duplicates(inplace=True)
                st.success("Duplicate rows removed.")
                changes["Duplicate Rows"] = "Duplicate rows were removed."
            # Summary statistics
            st.write("## Summary Statistics for Numerical Columns")
            numerical_columns = data.select_dtypes(include=["int64", "float64"]).columns
            summary_statistics = data[numerical_columns].describe()
            st.write(summary_statistics)
            dqa_report += generate_dqa_summary_statistics(summary_statistics)

            # Changes summary
            # Check if there are any numeric columns
            if data.select_dtypes(include=["int64", "float64"]).shape[1] > 0:
                
                # Summary statistics
                st.write("## Summary Statistics for Numerical Columns")
                numerical_columns = data.select_dtypes(include=["int64", "float64"]).columns
                summary_statistics = data[numerical_columns].describe()
                st.write(summary_statistics)
                dqa_report += generate_dqa_summary_statistics(summary_statistics)
            
                # Changes summary
                dqa_report += generate_dqa_changes_summary(changes)
            
                # After Update Preview
                st.write("## Update Dataset Preview")
                st.dataframe(data.head())
                st.dataframe(data.tail())
            
            else:
                st.write("No numeric columns found in the dataset.")

            # Download updated dataset
            st.write("## Download Updated Dataset")
            if st.button("Download"):
                updated_filename = f"{file_name}_updated.csv"
                data.to_csv(updated_filename, index=False, quoting=csv.QUOTE_ALL)
                st.markdown(get_download_link(updated_filename, "text/csv"), unsafe_allow_html=True)
                
                # Save DQA report to text file
                dqa_filename = f"{file_name}_data_quality_report.txt"
                with open(dqa_filename, "w") as f:
                    f.write(dqa_report)
                st.markdown(get_download_link(dqa_filename, "text/plain"), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
