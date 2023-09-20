# %%
from functools import partial
import pandas as pd
from rapidfuzz.process import extractOne
from lib.bipp.codebook.schema.variables import CodebookSchemaV0, codebook_columns_v0
from lib.bipp.codebook.schema.variables import Variable, cast_codebook
from lib.bipp.codebook.schema.metadata import MetadataSchemaV0, metadata_fields_v0
from lib.bipp.codebook.schema.metadata import ResourceMetadata
from lib.bipp.codebook.schema.additional_info import additional_information_fields_v0, AdditionalInfoSchemaV0
from lib.bipp.codebook.schema.additional_info import AdditionalInformation
import numpy as np
from typing import Literal
# %%


def get_similar(name: str, candidates, score_cutoff=90, **kwargs):
    result = extractOne(name, candidates, score_cutoff=score_cutoff, **kwargs)
    return None if result is None else result[0]

# %%


def get_similar_or_itself(name: str, candidates, **kwargs):
    match = get_similar(name, candidates, **kwargs)
    return name if match is None else match


# %%
def find_titles_row_in_codebook(df: pd.DataFrame, candidate_rows=[0, 1, 2], titles=codebook_columns_v0):
    max_matches_row = None
    max_matches = 0
    for i in candidate_rows:
        matches = df.iloc[i].str.lower().str.strip().apply(
            partial(get_similar, candidates=titles)).apply(bool).value_counts()
        if True not in matches:
            continue
        num_matches = matches[True]
        if num_matches > max_matches:
            max_matches_row = i
            max_matches = num_matches
    return max_matches_row


# %%
def parse_codebook_headers(df: pd.DataFrame, titles_row: int, titles=codebook_columns_v0):
    df = df.copy()
    df.columns = df.iloc[titles_row].str.lower().str.strip().apply(
        partial(get_similar_or_itself, candidates=titles))
    for col in df.columns:
        df[col] = df[col].str.strip()
    return df.iloc[titles_row+1:].reset_index(drop=True)


# %%
def parse_variables(raw: pd.DataFrame):
    titles_row_idx = find_titles_row_in_codebook(raw)
    df = parse_codebook_headers(raw, titles_row_idx)
    df["variable type"] = df["variable type"].str.lower().replace(
        "categorical", "text")
    df = CodebookSchemaV0.validate(df)
    df = cast_codebook(df)
    return Variable.from_codebook(df)

# %%


def parse_metadata_fields(raw: pd.DataFrame, fields=metadata_fields_v0):
    if raw.shape[1] != 2:
        raise Exception(
            "Metadata should contain only two columns where the first column contains the field names and the second column contains their corresponding values.")

    # drop the first row as it is the title "Metadata Information"
    df = raw[1:]
    df.iloc[:, 0] = df.iloc[:, 0].str.strip().str.lower()
    return pd.DataFrame({
        get_similar_or_itself(df.iloc[i, 0], candidates=metadata_fields_v0): [df.iloc[i, 1]]
        for i in range(0, df.shape[0])
    })


# %%

def parse_metadata(raw: pd.DataFrame):
    df = parse_metadata_fields(raw)
    df = MetadataSchemaV0.validate(df)
    return ResourceMetadata.from_codebook(df)


def parse_additional_info_fields(raw: pd.DataFrame, fields=additional_information_fields_v0):
    if raw.shape[1] != 2:
        raise Exception(
            "Additional Information should contain only two columns where the first column contains the field names and the second column contains their corresponding values.")

    # drop the first row as it is the title "Metadata Information"
    df = raw[1:]
    df.iloc[:, 0] = df.iloc[:, 0].str.strip().str.lower()
    return pd.DataFrame({
        get_similar_or_itself(df.iloc[i, 0], candidates=fields): [df.iloc[i, 1]]
        for i in range(0, df.shape[0])
    })


# %%

def parse_additional_info(raw: pd.DataFrame):
    df = parse_additional_info_fields(raw)
    df.replace(np.nan, None)
    df = AdditionalInfoSchemaV0.validate(df)
    return AdditionalInformation.from_codebook(df)


def get_similar_sheet_name(name: Literal["code", "meta", "addi"], sheets: list[str]):
    return list(filter(lambda x: name in x.lower(), sheets))[0]


# %%
def parse_codebook(file: pd.ExcelFile):
    get_sheet = partial(get_similar_sheet_name, sheets=file.sheet_names)
    raw_variables = file.parse(sheet_name=get_sheet("code"), header=None)
    raw_metadata = file.parse(sheet_name=get_sheet("meta"), header=None)
    raw_additional_info = file.parse(
        sheet_name=get_sheet("addi"), header=None)
    file.close()
    variables = parse_variables(raw_variables)
    metadata = parse_metadata(raw_metadata)
    additional_info = parse_additional_info(raw_additional_info)

    return {
        "variables": list(map(lambda v: v.dict(), variables)),
        "metadata": metadata.dict(),
        "additional_information": additional_info.dict()
    }
