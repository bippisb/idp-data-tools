import streamlit as st
import pandas as pd
from lib.critic import critique_codebook, critique_sheets, critique_metadata, critique_additional_information
from lib.critic import TestResultType, TestResult
from functools import partial
from json import loads, dumps

# st.set_option('deprecation.showfileUploaderEncoding', False)

st.set_page_config(page_title="Codebook Critic")
st.title('Codebook Critic')

file = st.file_uploader("Choose an Excel file", type=["xlsx"])

with open("./template/dataset_name_codebook.xlsx", "rb") as codebook_template:
    st.download_button(
        label="Download Codebook Template",
        data=codebook_template.read(),
        file_name="dataset_name_codebook.xlsx"
    )


def show_test_result(result: TestResult):
    mapping = {
        TestResultType.ERROR: partial(st.error, icon="🤷‍♀️"),
        TestResultType.SUCCESS: partial(st.success, icon="👌"),
        TestResultType.WARNING: partial(st.warning, icon="👨‍🏫"),
        TestResultType.INFO: partial(st.info, icon="ℹ")
    }
    mapping[result.type](result.message)


if file is not None:
    wb = pd.ExcelFile(file)
    with st.spinner("Running Tests ..."):
        results = critique_sheets(wb, test_results=list())

    st.write("## Structure")
    list(map(show_test_result, results))

    if TestResultType.ERROR not in map(lambda t: t.type, results):
        with st.spinner("Checking 'codebook' sheet"):
            results, codebook = critique_codebook(
                wb.parse("codebook", header=None), test_results=list())
        st.write("## Codebook Sheet")
        list(map(show_test_result, results))
        codebook = st.experimental_data_editor(codebook, num_rows="dynamic")

        with st.spinner("Checking 'metadata information' sheet"):
            results, metadata = critique_metadata(
                wb.parse("metadata information", header=None), test_results=list())
            st.write("## Metadata Information Sheet")
            list(map(show_test_result, results))
            metadata = st.experimental_data_editor(
                metadata, num_rows="dynamic")
            st.warning(
                "Metadata values are not sanity checked. The critic is trusting your judgement.", icon="⚠")

        with st.spinner("Checking 'additional information' sheet"):
            df = wb.parse("additional information", header=None)
            results, extra_info = critique_additional_information(
                df, test_results=list())
            st.write("## Additional Information Sheet")
            list(map(show_test_result, results))
            extra_info = st.experimental_data_editor(
                extra_info, num_rows="dynamic")
            st.warning(
                "Additional Information values are not sanity checked. The critic is trusting your judgement.", icon="⚠")

        st.write("# Export Codebook")
        json_codebook = dumps({
            "additional information": loads(extra_info.to_json(orient="records")),
            "metadata information": loads(metadata.to_json(orient="records")),
            "codebook": loads(codebook.to_json(orient="records"))
        })
        st.download_button(label="Download as json", data=json_codebook,
                           file_name=file.name.replace(".xlsx", ".json"), mime="application/json")

        with pd.ExcelWriter(file.name) as writer:
            codebook.shift()
