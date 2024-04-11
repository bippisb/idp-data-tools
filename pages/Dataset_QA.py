import streamlit as st
import pandas as pd
import base64
import urllib.parse
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import re

def get_special_char_count(column):
    # write docstring for this function
    """
    This function counts the number of special characters in a column
    """
    if column.dtype == "object":
        special_chars = [char for char in column.unique() if not str(char).isalnum()]
        return special_chars
    return 0

def generate_dqa_info(data, col, special_chars):
    # write docstring for this function
    """
    This function generates the DQA information for a given column
    """
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


def clean_state_name_column(data, col):
    try:
        if 'state_name' in data.columns:
            # Replace "&" with "and", remove special characters except spaces and alphabets, and trim spaces
            data['state_name'] = data['state_name'].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x.replace("&", "and")).strip())
        return data
    except Exception as e:
        print(f"Error processing the file: {e}")
        return None

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


def process_column(data,col,special_char_counts, dqa_report, changes, state_lgd_data, district_lgd_data):
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
    
    if col == 'state_name':
        has_special_chars = any(re.search(r"[^a-zA-Z0-9\s]", str(x)) for x in data[col])
        if has_special_chars:
            if st.button(f"Clean '{col}' Column"):
                data[col] = data[col].apply(lambda x: re.sub(r'[&]', 'and', x))
                data[col] = data[col].apply(lambda x: re.sub(r'[^a-zA-Z\s]', '', x).strip())
                st.success(f"Cleaned special characters from '{col}' column.")
                special_chars = special_char_counts[col]
    
    if data[col].dtype in ['float64', 'float32']:
        # For rounding decimal numbers
        if any(data[col].apply(lambda x: len(str(x).split('.')[1]) > 2 if '.' in str(x) else False)):
            if st.button(f"Round Off Decimal Numbers in {col}"):
                data[col] = data[col].round(2)
                st.success(f"Rounded off decimal numbers to 2 decimal places in {col}.")
    
    if data[col].dtype in ['object', 'str']:
        # Check if any value is not already in title case
        if not all(data[col].apply(lambda x: x.istitle() if isinstance(x, str) else True)):
            if st.button(f"Convert {col} to Title Case"):
                data[col] = data[col].apply(lambda x: x.title() if isinstance(x, str) and not x.istitle() else x)
                st.success(f"Converted {col} to title case.")
        else:
            st.write(f"The values in column '{col}' are already in title case.")
        
    if data[col].dtype in ['int64', 'int32', 'float64', 'float32']:
        has_negatives = (data[col] < 0).any()
        if has_negatives:
            if st.button(f"Convert Negative Numbers to Absolute in {col}"):
                data[col] = data[col].abs()
                st.success(f"Converted negative numbers to absolute values in {col}.")
    
    # if col == 'state_name':
    #     if not state_lgd_data.empty:
    #         # Create a button to replace state names
    #         for index, row in data.iterrows():
    #             state_code = row['state_code']
    #             state_name = row['state_name']

    #             # Find matching state_code in state_lgd_data
    #             matching_state = state_lgd_data[state_lgd_data['state_lgd_code'] == state_code]

    #             # If matching state is found and state_name is different, replace state_name
    #             if not matching_state.empty and matching_state.iloc[0]['state_name'] != state_name:
    #                 button_key = f"replace_state_button_{state_code}"  # Unique key based on state_code
    #                 if st.button(f"Replace '{state_name}' with '{matching_state.iloc[0]['state_name']}' in state_name column", key=button_key):
    #                     data.at[index, 'state_name'] = matching_state.iloc[0]['state_name']
    #                     changes['state_name'] = f"State names replaced based on state_lgd.csv data."
    #                     st.success(f"Replaced '{state_name}' with '{matching_state.iloc[0]['state_name']}' in state_name column.")
    # Get unique pairs of state_code and state_name
    unique_state_pairs = data[['state_code', 'state_name']].drop_duplicates()

    if col == 'state_name' :
        # Iterate over unique pairs to create buttons
        for index, row in unique_state_pairs.iterrows():
            state_code = str(row['state_code'])
            state_name = row['state_name']
            # find matching state_code in state_lgd_data
            matching_state = state_lgd_data[state_lgd_data['state_lgd_code'] == state_code]

            # if matching state is found and state_name is different, replace state_name
            if not matching_state.empty and matching_state.iloc[0]['state_name'] != state_name:
                button_key = f"replace_state_button_{state_code}"  # Unique key based on state_code
                if st.button(f"Replace '{state_name}' with '{matching_state.iloc[0]['state_name']}' in state_name column", key=button_key):
                    data.at[index, 'state_name'] = matching_state.iloc[0]['state_name']
                    changes['state_name'] = f"State names replaced based on state_lgd.csv data."
                    st.success(f"Replaced '{state_name}' with '{matching_state.iloc[0]['state_name']}' in state_name column.")


    if "district_name" in data.columns and "district_code" in data.columns:
        if not district_lgd_data.empty:
            # Iterate over rows and replace district_name if necessary
            if st.button("Replace District Names"):
                for index, row in data.iterrows():
                    district_code = row['district_code']
                    district_name = row['district_name']

                    # Find matching district_code in district_lgd_data
                    matching_district = district_lgd_data[district_lgd_data['district_lgd_code'] == district_code]

                    # If matching district is found and district_name is different, replace district_name
                    if not matching_district.empty and matching_district.iloc[0]['district_name'] != district_name:
                            # unique key based on district_code
                            button_key = f"replace_district_button_{district_code}"  # Unique key based on district_code
                            if st.button(f"Replace '{district_name}' with '{matching_district.iloc[0]['district_name']}' in '{col}'", key=button_key):
                                data.at[index, 'district_name'] = matching_district.iloc[0]['district_name']
                                changes['district_name'] = f"District names replaced based on district_lgd.csv data."
                                st.success(f"Replaced '{district_name}' with '{matching_district.iloc[0]['district_name']}' in '{col}'.")

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
    # return data
    return data
    
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
            # Check if 'data' and 'data_loaded' flags exist in session state, initialize if not
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'data' not in st.session_state:
            st.session_state.data = pd.DataFrame()

        st.title("Dataset QA App")
        
        uploaded_file = st.file_uploader("Upload a data file", type=["csv", "parquet"])

        file_name = ""
        data = None
        if 'data' not in st.session_state:
            st.session_state.data = pd.DataFrame()  # Initializes an empty DataFrame or loads initial data
        if uploaded_file:
            file_name = uploaded_file.name.split(".")[0]
            # Load the data only if it hasn't been loaded before or a new file is uploaded
            if not st.session_state.data_loaded or st.session_state.uploaded_file_name != file_name:
                st.session_state.data = pd.read_parquet(uploaded_file) if uploaded_file.name.endswith(".parquet") else pd.read_csv(uploaded_file)
                st.session_state.data_loaded = True
                st.session_state.uploaded_file_name = file_name  # Keep track of the loaded file name

        if not st.session_state.data.empty:
            # Proceed with displaying and processing the DataFrame
            st.write("## Dataset Preview")
            st.dataframe(st.session_state.data.head())
            
            st.write("## Dataset Preview")
            st.dataframe(st.session_state.data.head())
            
            st.write("## Dataset Information")
            st.write(f"Number of Rows: {st.session_state.data.shape[0]}")
            st.write(f"Number of Columns: {st.session_state.data.shape[1]}")

            # read state_lgd_data and district_lgd_data
            # modify the file path accordingly

            state_lgd_data = pd.read_csv("https://raw.githubusercontent.com/Suryakandukuri/idp-data-tools/master/state_lgd.csv")
            district_lgd_data = pd.read_csv("https://raw.githubusercontent.com/Suryakandukuri/idp-data-tools/master/district_lgd.csv")

            state_lgd_data['state_lgd_code'] = state_lgd_data['state_lgd_code'].astype(str)
            district_lgd_data['district_lgd_code'] = district_lgd_data['district_lgd_code'].astype(str)
            
            st.write("## Column Information")
            changes = {}
            special_chars_dict = {}
            dqa_report = "## Data Quality Assessment (DQA) Report\n\n"
            
            # Parallel Processing for special character counts
            with ThreadPoolExecutor(max_workers=4) as executor:
                special_char_counts = {col: get_special_char_count(st.session_state.data[col]) for col in st.session_state.data.columns}

            for col in st.session_state.data.columns:
                st.session_state.data = process_column(st.session_state.data, col, special_char_counts, dqa_report, changes, state_lgd_data, district_lgd_data)
                special_chars = special_char_counts[col]
                dqa_report += generate_dqa_info(st.session_state.data, col, special_chars)
                st.write("---")

            # Number of duplicate rows
            duplicate_count = st.session_state.data.duplicated().sum()
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
            numerical_columns = st.session_state.data.select_dtypes(include=["int64", "float64"]).columns
            summary_statistics = st.session_state.data[numerical_columns].describe()
            st.write(summary_statistics)
            dqa_report += generate_dqa_summary_statistics(summary_statistics)

            # Changes summary
            # Check if there are any numeric columns
            if st.session_state.data.select_dtypes(include=["int64", "float64"]).shape[1] > 0:
                
                # Summary statistics
                st.write("## Summary Statistics for Numerical Columns")
                numerical_columns = st.session_state.data.select_dtypes(include=["int64", "float64"]).columns
                summary_statistics = st.session_state.data[numerical_columns].describe()
                st.write(summary_statistics)
                dqa_report += generate_dqa_summary_statistics(summary_statistics)
            
                # Changes summary
                dqa_report += generate_dqa_changes_summary(changes)            
            else:
                st.write("No numeric columns found in the dataset.")
            
            # After Update Preview
            st.write("## Update Dataset Preview")
            st.dataframe(st.session_state.data.head())
            st.dataframe(st.session_state.data.tail())

            # Download updated dataset
            st.write("## Download Updated Dataset")
            if st.button("Download"):
                updated_filename = f"{file_name}_updated.csv"
                st.session_state.data.to_csv(updated_filename, index=False, quoting=csv.QUOTE_ALL)
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
