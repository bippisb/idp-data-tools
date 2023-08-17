import streamlit as st
import pandas as pd
import base64
import urllib.parse
import csv

def get_special_char_count(column, special_chars_dict):
    """
    Calculates the count of special characters in a given column.
    Parameters:
        column (pandas.Series): The column to count the special characters from.
        special_chars_dict (dict): A dictionary to store the special characters for each column.
    Returns:
        int: The count of special characters in the column.
    """
    if column.dtype == "object":
        special_chars = [char for char in column.unique() if not str(char).isalnum()]
        special_chars_dict[column.name] = special_chars
        return len(special_chars)
    return 0

def generate_dqa_info(data, col, special_chars):
    """
    Generate the data quality assessment (DQA) information for a given column.
    Parameters:
        data (pandas.DataFrame): The dataframe containing the data.
        col (str): The name of the column for which to generate the DQA information.
        special_chars (list): A list of special characters.
    Returns:
        str: The DQA information for the column.
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

def generate_dqa_special_chars_info(col, special_chars):
    """
    Generate the information about special characters in a given column.
    Parameters:
        col (str): The name of the column.
        special_chars (list): A list of special characters.
    Returns:
        str: A formatted string containing the column name and the special character values.
            Returns an empty string if no special characters are provided.
    """
    if special_chars:
        dqa_info = f"### Column: {col}\n"
        dqa_info += f"Special Character Values: {', '.join(map(str, special_chars))}\n\n"
        return dqa_info
    return ""

def generate_dqa_duplicate_info(duplicate_count):
    """
    Generates a description of the number of duplicate rows in the dataset.
    Parameters:
        duplicate_count (int): The number of duplicate rows in the dataset.
    Returns:
        str: A string containing the number of duplicate rows.
    """
    return f"## Number of Duplicate Rows\nNumber of Duplicate Rows: {duplicate_count}\n\n"

def generate_dqa_changes_summary(changes):
    """
    Generate a summary of the data type changes and other changes.
    Parameters:
    - changes (dict): A dictionary containing the column names as keys and the changes as values.
    Returns:
    - dqa_info (str): A string containing the summary of data type changes and other changes.
    """
    dqa_info = "## Data Type Changes and Other Changes Summary\n"
    for col, change in changes.items():
        dqa_info += f"Column/Change: {col}\nChange: {change}\n\n"
    return dqa_info

def generate_dqa_summary_statistics(summary_statistics):
    """
    Generates the summary statistics for the given summary_statistics.
    Parameters:
    - summary_statistics (str): A string containing the summary statistics.
    Returns:
    - dqa_info (str): A string containing the summary statistics for numerical columns.
    """
    dqa_info = "## Summary Statistics for Numerical Columns\n"
    # Use to_string() to format the table
    dqa_info += summary_statistics.to_string()  
    dqa_info += "\n\n"
    return dqa_info

def get_download_link(file_name, content_type):
    """
    Generates a download link for a given file.
    Parameters:
        file_name (str): The name of the file to be downloaded.
        content_type (str): The MIME type of the file.
    Returns:
        str: The HTML code for the download link.
    """
    with open(file_name, "rb") as f:
        data = f.read()
    base64_data = base64.b64encode(data).decode("utf-8")
    encoded_file_name = urllib.parse.quote(file_name)
    href = f"<a href='data:{content_type};base64,{base64_data}' download='{encoded_file_name}'>Download {file_name}</a>"
    return href

def main():
    """
    The main function of the app that handles the dataset QA process.
    Parameters:
    None
    Returns:
    None
    """
    st.set_page_config(page_title="Dataset QA")
    st.title("Dataset QA App")
   
    # File upload
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        
        st.write("## Dataset Preview")
        st.dataframe(data.head())
        
        st.write("## Dataset Information")
        st.write(f"Number of Rows: {data.shape[0]}")
        st.write(f"Number of Columns: {data.shape[1]}")
        
        st.write("## Column Information")
        changes = {}
        special_chars_dict = {}
        dqa_report = "## Data Quality Assessment (DQA) Report\n\n"
        for col in data.columns:
            st.write(f"### Column: {col}")
            st.write(f"Data Type: {data[col].dtype}")
            st.write(f"Number of Numerical Values: {data[col].apply(pd.to_numeric, errors='coerce').notnull().sum()}")
            st.write(f"Number of NaN Values: {data[col].isnull().sum()}")
            st.write(f"Count of Unique Values: {data[col].nunique()}")
            
            # Count special characters
            special_chars = get_special_char_count(data[col], special_chars_dict)
            st.write(f"Count of Special Characters: {special_chars}")
            st.write(f"Unique Values: {data[col].unique()}")
            
            # Format columns
            format_rules = {
                "state_code": 2, "district_code": 3, "sub_district_code": 4,
                "block_code": 4, "village_code": 6, "gp_code": 6
            }
            if col in format_rules:
                data[col] = data[col].apply(lambda x: str(x).zfill(format_rules[col]))
                st.write(f"#### {col} values were formatted to have leading zeros.")
            

            # Change datatype
            new_dtype = st.selectbox(f"Change Data Type for {col}:", ["No Change", "int", "float", "str", "date"], key=f"{col}_dtype")
            if new_dtype != "No Change":
                if new_dtype == "date":
                    data[col] = pd.to_datetime(data[col], errors='coerce', format='%d-%m-%Y')
                    changes[col] = f"Data Type Changed to {new_dtype} (Format: dd-mm-yyyy)"
                else:
                    try:
                        data[col] = data[col].astype(new_dtype)
                        changes[col] = f"Data Type Changed to {new_dtype}"
                    except:
                        changes[col] = "Error: Unable to change data type"
                        
            dqa_report += generate_dqa_info(data, col, special_chars)
            st.write("---")
        
        # Display list of special character values
        st.write("## List of Special Character Values")
        for col, special_chars in special_chars_dict.items():
            if special_chars:
                st.write(f"### Column: {col}")
                special_chars_no_space = [char for char in special_chars if char.strip() != ""]
                st.write(f"Special Character Values: {', '.join(map(str, special_chars_no_space))}")
                dqa_report += generate_dqa_special_chars_info(col, special_chars_no_space)
        
        # Number of duplicate rows
        st.write("## Number of Duplicate Rows")
        duplicate_count = data.duplicated().sum()
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
        dqa_report += generate_dqa_changes_summary(changes)

        # Download updated dataset
        st.write("## Download Updated Dataset")
        if st.button("Download"):
            updated_filename = "updated_dataset.csv"
            data.to_csv(updated_filename, index=False, quoting=csv.QUOTE_ALL)
            st.markdown(get_download_link(updated_filename, "text/csv"), unsafe_allow_html=True)
            
            # Save DQA report to text file
            dqa_filename = "data_quality_report.txt"
            with open(dqa_filename, "w") as f:
                f.write(dqa_report)
            st.markdown(get_download_link(dqa_filename, "text/plain"), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
