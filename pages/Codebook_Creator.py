import streamlit as st
import polars as pl
from lib.types import alphanumeric_name, polars_dtype_to_postgres_dtype_mapping, Variable, GranularityLevel, Sectors, Frequency
from pydantic import ValidationError

st.set_page_config(page_title="Codebook Creator")
st.title("Codebook Creator")

file = st.file_uploader("Upload a dataset",
                        type=["csv", "parquet"])

if file is not None:
    # TODO: lazy load data file.
    df = pl.read_parquet(file) if file.name.endswith(
        ".parquet") else pl.read_csv(file)

    # create data dictionary
    data_dict = [
        Variable(
            name=alphanumeric_name(col),
            description=col,
            data_type=polars_dtype_to_postgres_dtype_mapping[str(dtype)],
        )
        for col, dtype in df.schema.items()
    ]
    cln_df = df.rename({
        var.description: var.name
        for var in data_dict
    })

    st.write("## Data Dictionary")
    edited_data_dict = st.experimental_data_editor(
        pl.from_records([var.dict() for var in data_dict]).to_pandas()
    )
    if st.button("Validate Data Dictionary"):
        for i, var in enumerate(edited_data_dict.to_dict("records")):
            try:
                Variable.parse_obj(var)
            except ValidationError as e:
                for err in e.errors():
                    st.error(
                        f"🤷‍♀️ _{', '.join(err['loc'])}_ in row {i}: {err['msg']}")
    st.write("## Metadata")
    domains = st.multiselect(
        "What are the domains (sectors) of the dataset?",
        Sectors.__args__
    )
    dataset_name = st.text_input("What is the name of the dataset (package)?")
    resource_name = st.text_input("What is the name of the resource?")
    source_name = st.text_input("What is the name of the source?")
    source_link = st.text_input("What is the website of the source?")
    frequency = st.selectbox(
        "What is the frequency at which the data collected?",
        Frequency.__args__)
    granularity_level = st.selectbox(
        "What is the granularity of the dataset?", GranularityLevel.__args__)
    data_extraction_date = st.date_input(
        "When was the data extracted from source?")
    data_last_updated = st.date_input(
        "When was the data last updated on source?")
