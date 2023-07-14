import streamlit as st
import string
import random

st.header("Dataset ID Creator")

granularities = {
    "Country": "CN",
    "India": "IN",
    "State": "ST",
    "District": "DT",
    "Tehsil": "TH",
    "Block": "BL",
    "Sub-District": "SD",
    "Gram Panchayat": "GP",
    "City": "CT",
    "Village": "VL",
    "Local Body": "LB",
    "Assembly Constituency": "AC",
    "Parliamentary Constituency": "PC",
    "Other Level": "OL",
    "Point Level": "PL",
}
granularity = st.selectbox(
    "What's the granularity of the dataset (Spatial Resolution)?",
    granularities.keys()
)

frequencies = {
    "Daily": "DL",
    "Weekly": "WK",
    "Fortnightly": "FN",
    "Monthly": "MN",
    "Quarterly": "QT",
    "Seasonally": "SN",
    "Yearly": "YR",
    "Quinquennial": "QQ",
    "Decadal": "DC",
    "Other / One Time": "OT",
}

frequency = st.selectbox(
    "What's the frequency of the dataset (Temporal Resolution)?",
    frequencies.keys()
)

dataset_name = st.text_input(
    "What's the name of the dataset? Don't use spaces or special characters.", max_chars=12)
source_name = st.text_input(
    "What's the name of the source of the dataset? Don't use spaces or special characters.", max_chars=6)


def generate_dataset_id(name: str, source: str, granularity: str, frequency: str):
    suffix = "".join(random.choices(string.ascii_lowercase, k=3))
    id = "-".join((name, source, granularity, frequency, suffix))
    return id.strip().replace(" ", "").lower()


st.success(generate_dataset_id(
    dataset_name,
    source_name,
    granularities[granularity],
    frequencies[frequency]
))
