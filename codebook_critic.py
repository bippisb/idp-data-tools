import streamlit as st
import pandas as pd
from lib.critic import critique_codebook, critique_sheets, critique_metadata
from lib.critic import TestResultType, TestResult
from functools import partial

st.set_option('deprecation.showfileUploaderEncoding', False)

st.set_page_config(page_title="Codebook Critic")
st.title('Codebook Critic')

file = st.file_uploader("Choose an Excel file", type=["xlsx"])


def show_test_result(result: TestResult):
    mapping = {
        TestResultType.ERROR: partial(st.error, icon="🤷‍♀️"),
        TestResultType.SUCCESS: partial(st.success, icon="👌"),
        TestResultType.WARNING: partial(st.warning, icon="👨‍🏫"),
        TestResultType.INFO: partial(st.info, icon="😇")
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
        st.dataframe(codebook)

        with st.spinner("Checking 'metadata information' sheet"):
            results, metadata = critique_metadata(wb.parse("metadata information", header=None), test_results=list())
            st.write("## Metadata Information Sheet")
            list(map(show_test_result, results))
            st.dataframe(metadata.T.fillna(pd.NA))

