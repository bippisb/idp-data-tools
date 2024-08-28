import streamlit as st
import polars as pl
import base64
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import re

st.set_page_config(page_title="Dataset QA")

def get_download_link(file_name, mime_type):
    """Generates a download link for a file."""
    with open(file_name, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{file_name}">Download {file_name}</a>'

def get_special_char_count(column):
    """This function counts the number of special characters in a column."""
    if column.dtype == pl.Utf8:
        # Use regex to filter rows with special characters (non-alphanumeric characters)
        special_chars = column.str.contains(r'[^a-zA-Z0-9\s]')
        return special_chars.sum()  # Return the count of rows with special characters
    return 0

def generate_dqa_info(data, col, special_chars_count):
    """Generates Data Quality Assessment (DQA) information for a given column."""
    dtype = data[col].dtype
    unique_values = data[col].n_unique()

    dqa_info = f"### Column: {col}\n"
    dqa_info += f"Data Type: {dtype}\n"
    dqa_info += f"Unique Values: {unique_values}\n"
    
    # Handle special characters count properly
    if isinstance(special_chars_count, int):
        dqa_info += f"Count of Special Characters: {special_chars_count}\n"
    else:
        dqa_info += "Count of Special Characters: 0\n"
    
    return dqa_info

def generate_dqa_summary_statistics(summary_statistics):
    return f"### Summary Statistics\n{summary_statistics}\n"

def generate_dqa_changes_summary(changes):
    return "### Changes Summary\n" + "\n".join(f"{k}: {v}" for k, v in changes.items())

def convert_to_desired_format(date):
    try:
        return datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
    except Exception:
        return None

def process_column(data, col, special_char_counts, dqa_report, changes, state_lgd_data, district_lgd_data):
    """Processes a single column for various checks and manipulations."""
    dtype = data[col].dtype
    unique_values = data[col].unique().to_list()
    # Filter out None or null values before displaying
    filtered_unique_values = [value for value in unique_values if value is not None]



    st.write(f"### Column: {col}")
    st.write(f"Data Type: {dtype}")
    # st.write(f"Unique Values: {unique_values[:30]}...") if len(unique_values) > 30 else st.write(f"Unique Values: {unique_values}")
    # Display unique values
    # Display unique values, handling the possibility of an empty list after filtering
    if len(filtered_unique_values) > 30:
        st.write(f"Unique Values: {filtered_unique_values[:30]}...")
    elif len(filtered_unique_values) > 0:
        st.write(f"Unique Values: {filtered_unique_values}")
    else:
        st.write("No unique non-null values found.")

    special_chars = special_char_counts.get(col, None)
    if special_chars is not None and isinstance(special_chars, int):
        st.write(f"Count of Special Characters: {special_chars}")
    else:
        st.write("No special characters found in this column.")
    
    if data[col].dtype == pl.Utf8:
    # Check if any value is not in title case
        if not all(data[col].apply(lambda x: x.istitle() if isinstance(x, str) else True).to_list()):
            # If any value is not in title case, provide an option to convert
            if st.button(f"Convert '{col}' to Title Case"):
                data = data.with_columns(
                    pl.col(col).apply(lambda x: x.title() if isinstance(x, str) and not x.istitle() else x).alias(col)
                )
                st.success(f"Converted '{col}' to title case.")
        else:
            st.write(f"All values in column '{col}' are already in title case.")
        has_special_chars = any(re.search(r"[^a-zA-Z0-9\s]", str(x)) for x in data[col].to_list())

        if has_special_chars:
            # Check if the user wants to clean the 'state_name' column
            if st.button(f"Clean '{col}' Column"):
                # Clean the column by replacing '&' with 'and', and removing other special characters
                data = data.with_columns(
                    pl.col(col).str.replace('&', 'And')
                            .str.replace(r'[^a-zA-Z\s]', '')
                            .str.strip()
                )
                st.success(f"Cleaned special characters from '{col}' column.")
                
                # Update the special character count for the cleaned column
                special_chars = special_char_counts.get(col, [])

    if col == 'state_name':
    # Check if the column contains special characters
        has_special_chars = any(re.search(r"[^a-zA-Z0-9\s]", str(x)) for x in data[col].to_list())

        if has_special_chars:
            # Check if the user wants to clean the 'state_name' column
            if st.button(f"Clean '{col}' Column"):
                # Clean the column by replacing '&' with 'and', and removing other special characters
                data = data.with_columns(
                    pl.col(col).str.replace('&', 'And')
                            .str.replace(r'[^a-zA-Z\s]', '')
                            .str.strip()
                )
                st.success(f"Cleaned special characters from '{col}' column.")
                
                # Update the special character count for the cleaned column
                special_chars = special_char_counts.get(col, [])


    # Handling 'state_name' replacement logic if column name is state_name and data has state_code column
    if col == 'state_name' and 'state_code' in data.columns:
        unique_state_pairs = data.select(['state_code', 'state_name']).unique()

        for row in unique_state_pairs.to_dicts():
            state_code = str(row['state_code'])
            state_name = row['state_name']
            # Find matching state name in the state_lgd_data
            matching_state = state_lgd_data.filter(pl.col('state_lgd_code') == state_code)
            
            if len(matching_state) > 0 and matching_state[0, 'state_name'] != state_name:
                
                replace_state = st.checkbox(f"Replace '{state_name}' with '{matching_state[0, 'state_name']}'?", key=state_code)
                if replace_state:
                    data = data.with_columns(
                        pl.when(pl.col('state_code') == state_code)
                        .then(pl.lit(matching_state[0, 'state_name']))  # Wrap the string literal with pl.lit()
                        .otherwise(pl.col('state_name'))
                        .alias('state_name')
                    )
                    changes['state_name'] = f"State names replaced based on state_lgd.csv data."
                    st.success(f"Replaced '{state_name}' with '{matching_state[0, 'state_name']}' in state_name column.")
        # Handling 'district_name' replacement logic
    if col == 'district_name' and 'district_code' in data.columns:
        unique_district_pairs = data.select(['district_code', 'district_name']).unique()

        for row in unique_district_pairs.to_dicts():
            district_code = str(row['district_code'])
            district_name = row['district_name']

            # Find matching district name in the district_lgd_data
            matching_district = district_lgd_data.filter(pl.col('district_lgd_code') == district_code)

            if len(matching_district) > 0 and matching_district[0, 'district_name'] != district_name:
                replace_district = st.checkbox(f"Replace '{district_name}' with '{matching_district[0, 'district_name']}'?", key=district_code)
                if replace_district:
                    data = data.with_columns(
                        pl.when(pl.col('district_code') == district_code)
                        .then(pl.lit(matching_district[0, 'district_name']))  # Wrap the string literal with pl.lit()
                        .otherwise(pl.col('district_name'))
                        .alias('district_name')
                    )
                    changes['district_name'] = f"District names replaced based on district_lgd.csv data."
                    st.success(f"Replaced '{district_name}' with '{matching_district[0, 'district_name']}' in district_name column.")



    # Formatting columns with leading zeros
    format_rules = {
        "state_code": 2, "district_code": 3, "sub_district_code": 4,
        "block_code": 4, "village_code": 6, "gp_code": 6
    }
    if col in format_rules:
        data = data.with_columns(
            pl.col(col).cast(pl.Utf8).apply(lambda x: x.zfill(format_rules[col]) if x else None)
        )
        st.write(f"##### {col} values were formatted to have leading zeros.")
        st.write(f"Unique Values: {data[col].unique().to_list()}")

    # Change datatype logic
    new_dtype = st.selectbox(f"Change Data Type for {col}:", ["No Change", "int", "float", "str", "date"], key=f"{col}_dtype")
    if new_dtype != "No Change":
        try:
            if new_dtype == "date":
                data = data.with_columns(
                    pl.col(col).apply(lambda date: convert_to_desired_format(date) if date else None).alias(col)
                )
                changes[col] = f"Data Type Changed to {new_dtype} (Format: dd-mm-yyyy)"
                st.write(f"###### Data Type Changed to {new_dtype} (Format: dd-mm-yyyy)")
            elif new_dtype == "int":
                data = data.with_columns(
                    pl.col(col).cast(pl.Int64)
                )
                changes[col] = f"Data Type Changed to {new_dtype}"
                st.write(f"###### Data Type Changed to {new_dtype}")
            elif new_dtype == "float":
                data = data.with_columns(
                    pl.col(col).cast(pl.Float64).apply(lambda x: round(x, 3) if x is not None else None)
                )
                changes[col] = f"Data Type Changed to {new_dtype}"
                st.write(f"###### Data Type Changed to {new_dtype}")
        except Exception as e:
            changes[col] = f"Error-{e}: Unable to change data type"
            st.write(f"Unable to change data type for {col} because of {e}")

    # Count special characters
    if isinstance(special_chars, pl.Series):
        st.write(f"Count of Special Characters: {len(special_chars)}")
        if len(special_chars) > 30:
            st.write(f"Special Character Values: {special_chars[:30]}...")
        else:
            st.write(f"Special Character Values: {special_chars}")
    else:
        st.write("Count of Special Characters: 0")

    return data

try:
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'data' not in st.session_state:
        st.session_state.data = pl.DataFrame()

    st.title("Dataset QA App")

    uploaded_file = st.file_uploader("Upload a data file", type=["csv", "parquet"])

    file_name = ""
    data = None
    if uploaded_file:
        file_name = uploaded_file.name.split(".")[0]
        if not st.session_state.data_loaded or st.session_state.get('uploaded_file_name') != file_name:
            st.session_state.data = pl.read_parquet(uploaded_file) if uploaded_file.name.endswith(".parquet") else pl.read_csv(uploaded_file)
            st.session_state.data_loaded = True
            st.session_state.uploaded_file_name = file_name

    if not st.session_state.data.is_empty():
        st.write("## Dataset Preview")
        st.dataframe(st.session_state.data.head())

        st.write(f"Number of Rows: {st.session_state.data.shape[0]}")
        st.write(f"Number of Columns: {st.session_state.data.shape[1]}")

        # Load state_lgd_data and district_lgd_data
        state_lgd_data = pl.read_csv("https://raw.githubusercontent.com/Suryakandukuri/idp-data-tools/master/state_lgd.csv")
        district_lgd_data = pl.read_csv("https://raw.githubusercontent.com/Suryakandukuri/idp-data-tools/master/district_lgd.csv")

        state_lgd_data = state_lgd_data.with_columns(pl.col('state_lgd_code').cast(pl.Utf8))
        district_lgd_data = district_lgd_data.with_columns(pl.col('district_lgd_code').cast(pl.Utf8))

        # Column Information
        changes = {}
        special_chars_dict = {}
        dqa_report = "## Data Quality Assessment (DQA) Report\n\n"

        # Special character counts
        with ThreadPoolExecutor(max_workers=4) as executor:
            special_char_counts = {col: get_special_char_count(st.session_state.data[col]) for col in st.session_state.data.columns}

        for col in st.session_state.data.columns:
            st.session_state.data = process_column(st.session_state.data, col, special_char_counts, dqa_report, changes, state_lgd_data, district_lgd_data)
            special_chars = special_char_counts[col]
            dqa_report += generate_dqa_info(st.session_state.data, col, special_chars)

        # Count duplicate rows in polars
        duplicate_count = st.session_state.data.shape[0] - st.session_state.data.unique().shape[0]
        st.write(f"Number of Duplicate Rows: {duplicate_count}")
        # Remove duplicate rows in polars
        if st.button("Remove Duplicate Rows"):
            st.session_state.data = st.session_state.data.unique(keep='first')
            st.success("Duplicate rows removed.")

        # Summary statistics for numerical columns
        numerical_columns = [col for col in st.session_state.data.columns if st.session_state.data[col].dtype in [pl.Float64, pl.Int64]]
        summary_statistics = st.session_state.data.select(numerical_columns).describe()
        st.write("## Summary Statistics")
        st.write(summary_statistics)

        # Changes summary
        dqa_report += generate_dqa_summary_statistics(summary_statistics)
        dqa_report += generate_dqa_changes_summary(changes)

                # After Update Preview
        st.write("## Updated Dataset Preview")
        st.dataframe(st.session_state.data.head())
        st.dataframe(st.session_state.data.tail())

        # Download dataset
        if st.button("Download the updated dataset"):
            updated_filename = f"{file_name}_updated.csv"
            st.session_state.data.write_csv(updated_filename)
            st.markdown(get_download_link(updated_filename, "text/csv"), unsafe_allow_html=True)

            dqa_filename = f"{file_name}_data_quality_report.txt"
            with open(dqa_filename, "w") as f:
                f.write(dqa_report)
            st.markdown(get_download_link(dqa_filename, "text/plain"), unsafe_allow_html=True)
            # clear the cache in streamlit application and refresh the page
            st.cache_resource.clear()
            st.experimental_memo.clear()
            st.experimental_singleton.clear()
            st.experimental_rerun()

except Exception as e:
    st.error(f"An error occurred: {e}")
