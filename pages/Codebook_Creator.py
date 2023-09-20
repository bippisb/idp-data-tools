import streamlit as st
import polars as pl
from lib.types import alphanumeric_name, polars_dtype_to_postgres_dtype_mapping
from lib.types import Variable, ResourceMetadata, AdditionalInformation
from lib.types import GranularityLevel, Sectors, Frequency
from lib.bipp.codebook.export import to_excel_codebook
from pydantic import ValidationError
import json

st.set_page_config(page_title="Codebook Creator")
st.title("Codebook Creator")

file = st.file_uploader("Upload a dataset",
                        type=["csv", "parquet"])

if file is not None:
    # TODO: lazy load data file.
    df = pl.read_parquet(file) if file.name.endswith(
        ".parquet") else pl.read_csv(file)
    st.dataframe(df.to_pandas().sample(5))
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
    st.write("For a start variable descriptions are same as variable names. Please edit varaible descriptions.")
    edited_data_dict = st.experimental_data_editor(
        pl.from_records([var.model_dump() for var in data_dict]).to_pandas()
    )
    if st.button("Validate Data Dictionary"):
        for i, var in enumerate(edited_data_dict.to_dict("records")):
            try:
                Variable.model_validate(var)
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
    methodology = st.text_input(
        "Data collection methodology used by the source.")
    data_extraction_page = st.text_input(
        "URL to the exact page from which the data is extracted?")
    frequency = st.selectbox(
        "What is the frequency (temporal resolution) of the dataset?",
        Frequency.__args__)
    granularity_level = st.selectbox(
        "What is the granularity (spatial resolution) of the dataset?", GranularityLevel.__args__)
    data_extraction_date = st.date_input(
        "When was the data extracted from source?")
    data_last_updated = st.date_input(
        "When was the data last updated on source?")
    about = st.text_area(
        "Provide a description for the dataset. It will show up as resource description on the data portal.", height=5)
    data_insights = st.text_area(
        "What are the insights that can be gained from the dataset?")
    seo_tags = st.text_input(
        "SEO tags: multiple tags can be separated by comma.")

    st.write("## Additional Information")
    st.write("#### Dataset Description")
    st.dataframe(df.describe().to_pandas())
    st.write("#### Number of unique values per-column")
    st.dataframe(df.select(pl.all().n_unique()).to_pandas())
    years_covered = st.text_input("*Time period* covered by the dataset.")
    no_of_states = st.number_input(
        "Number of *states* covered by the dataset.", step=1)
    no_of_districts = st.number_input(
        "Number of *districts* covered by the dataset.", step=1)
    no_of_tehsils = st.number_input(
        "Number of *tehsils* covered by the dataset.", step=1)
    no_of_gps = st.number_input(
        "Number of *gram panchayats* covered by the dataset.", step=1)
    no_of_villages = st.number_input(
        "Number of *villages* covered by the dataset.", step=1)
    notes = st.text_area(
        "Any notes or remarks for the end users of this dataset.")
    no_of_indicators = df.select(pl.col(pl.NUMERIC_DTYPES)).shape[1]

    if st.button("Generate Codebook"):
        metadata = ResourceMetadata(
            domains=domains,
            dataset_name=dataset_name,
            granularity_level=granularity_level,
            frequency=frequency,
            source_name=source_name,
            source_link=source_link,
            methodology=methodology,
            data_extraction_page=data_extraction_page,
            data_retrieval_date=data_extraction_date.strftime("%d-%m-%Y"),
            data_last_updated=data_last_updated.strftime("%d-%m-%Y"),
            about=about,
            data_insights=data_insights,
            resource=resource_name,
            tags=seo_tags.split(","),
            similar_datasets=[]
        )

        additional_info = AdditionalInformation(
            years_covered=years_covered,
            no_of_states=no_of_states,
            no_of_districts=no_of_districts,
            no_of_gps=no_of_gps,
            no_of_tehsils=no_of_tehsils,
            no_of_villages=no_of_villages,
            no_of_indicators=no_of_indicators,
            notes=notes,
        )
        cb = {
            "variables": list(map(lambda v: Variable.model_validate(v).model_dump(), edited_data_dict.to_dict("records"))),
            "additional_information": additional_info.model_dump(),
            "metadata": metadata.model_dump(),
        }
        excel = to_excel_codebook(cb=cb)
        st.download_button("Download Codebook", excel,
                           file_name="dataset_sku_codebook.xlsx")
