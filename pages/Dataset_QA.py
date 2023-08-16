import streamlit as st

st.set_page_config(page_title="Dataset QA")


content = """
# Dataset_QA
[Dataset Quality Assessment Streamlit application](https://datasetqualitycheck.streamlit.app/) 

Streamlit application code that performs data quality assessment (DQA) on a CSV dataset. The application allows users to upload a CSV file, analyze the dataset, and generate a DQA report. The report includes information about column data types, counts of numerical values, NaN values, unique values, and special characters. Users can also change the data type of columns, remove duplicate rows, and download the updated dataset along with the DQA report.

It's important to note that this application requires the Streamlit library to run.

Here's a breakdown of the main components and functionalities of the code:

File Upload: Users can upload a CSV file using the st.file_uploader function.

Dataset Preview: The uploaded dataset is displayed as a preview using the st.dataframe function.

Dataset Information: Basic information about the dataset, such as the number of rows and columns, is displayed using the st.write function.

Column Information: The application iterates through each column in the dataset and provides information about data type, numerical values, NaN values, unique values, special characters, and unique values. Users have the option to change the data type of columns using a dropdown.

List of Special Character Values: If special characters are detected in any column, the application displays a list of those special character values.

Number of Duplicate Rows: The number of duplicate rows in the dataset is displayed.

Remove Duplicate Rows: Users can click a button to remove duplicate rows from the dataset.

Format Columns: Certain columns (e.g., "state_code", "district_code") are formatted with leading zeroes using the zfill function.

Download Updated Dataset: Users can download the updated dataset after making changes using a button. The dataset is saved as a CSV file, and a download link is provided.

Save DQA Report: A DQA report is generated and saved to a text file. Users can download the DQA report using a separate download link.

It provides a useful tool for data analysts and practitioners to quickly assess and improve the quality of their datasets. To run this code, make sure you have the Streamlit library installed (pip install streamlit), and then execute the script using the command streamlit run your_script.py in your terminal.
"""

st.markdown(content)