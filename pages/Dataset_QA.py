import streamlit as st
import pandas as pd
import base64
import urllib.parse
import csv

def get_special_char_count(column, special_chars_dict):
    if column.dtype == "object":
        special_chars = [char for char in column.unique() if not str(char).isalnum()]
        special_chars_dict[column.name] = special_chars
        return len(special_chars)
    return 0

def generate_dqa_info(data, col, special_chars):
    dqa_info = f"### Column: {col}\n"
    dqa_info += f"Data Type: {data[col].dtype}\n"
    dqa_info += f"Number of Numerical Values: {data[col].apply(pd.to_numeric, errors='coerce').notnull().sum()}\n"
    dqa_info += f"Number of NaN Values: {data[col].isnull().sum()}\n"
    dqa_info += f"Count of Unique Values: {data[col].nunique()}\n"
    dqa_info += f"Count of Special Characters: {len(special_chars) if special_chars is not None and isinstance(special_chars, list) else 0}\n"
    dqa_info += f"Unique Values: {', '.join(map(str, data[col].unique()))}\n\n"
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
    dqa_info = "## Data Type Changes Summary\n"
    for col, change in changes.items():
        dqa_info += f"Column: {col}\nChange: {change}\n\n"
    return dqa_info

def get_download_link(file_name, content_type):
    with open(file_name, "rb") as f:
        data = f.read()
    base64_data = base64.b64encode(data).decode("utf-8")
    encoded_file_name = urllib.parse.quote(file_name)
    href = f"<a href='data:{content_type};base64,{base64_data}' download='{encoded_file_name}'>Download {file_name}</a>"
    return href

def main():
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
            
            # Change datatype
            new_dtype = st.selectbox(f"Change Data Type for {col}:", ["No Change", "int", "float", "str"], key=f"{col}_dtype")
            if new_dtype != "No Change":
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
            
        # Format state_code and district_code columns
        if "state_code" in data.columns:
            data["state_code"] = data["state_code"].apply(lambda x: str(x).zfill(2))
        if "district_code" in data.columns:
            data["district_code"] = data["district_code"].apply(lambda x: str(x).zfill(3))
        if "subdistrict_code" in data.columns:
            data["subdistrict_code"] = data["subdistrict_code"].apply(lambda x: str(x).zfill(4))
        if "sub_district_code" in data.columns:
            data["sub_district_code"] = data["sub_district_code"].apply(lambda x: str(x).zfill(4))
        if "block_code" in data.columns:
            data["block_code"] = data["block_code"].apply(lambda x: str(x).zfill(4))
        if "village_code" in data.columns:
            data["village_code"] = data["village_code"].apply(lambda x: str(x).zfill(6))
        if "gp_code" in data.columns:
            data["gp_code"] = data["gp_code"].apply(lambda x: str(x).zfill(6))
        
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
