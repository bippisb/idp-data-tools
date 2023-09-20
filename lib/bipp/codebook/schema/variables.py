import pandera as pa
from typing import Literal
import pandas as pd
from pydantic import BaseModel, validator
from lib.bipp.codebook.schema.types import PostgresDType
import re
from typing import List

codebook_columns_v0 = [
    'variable name',
    'variable description',
    'variable type',
    'unit of measurement',
    'constant unit / changing unit',
    'formula',
    'unit reference',
    'parent variable',
    'unit conversion',
    'original / derived',
    'variable parent',
    'visual exclude'
]
VariableType = Literal[
    "text",
    "numeric",
    "date",
    "region",
    "categorical",
    "boolean",
]


CodebookSchemaV0 = pa.DataFrameSchema(
    {
        "variable name": pa.Column(str, unique=True, checks=[
            pa.Check.str_length(min_value=1, max_value=60),
            # TODO: refine the following regex
            pa.Check.str_matches(
                r'''^[^A-Z!@#$%^&*()+\-=\[\]{};':"\\|,.<>\/?]+$'''),
        ]),
        "variable description": pa.Column(str),
        "variable type": pa.Column(str, checks=[
            pa.Check.isin([
                *[v.upper() for v in VariableType.__args__],
                *VariableType.__args__
            ])
        ]),
        "unit of measurement": pa.Column(str, nullable=True, default=""),
        "constant unit / changing unit": pa.Column(str, nullable=True, default=""),
        "formula": pa.Column(str, nullable=True, default=""),
        "unit reference": pa.Column(str, nullable=True, default=""),
        "parent variable": pa.Column(str, nullable=True, default=""),
        "unit conversion": pa.Column(str, nullable=True, default=""),
        "original / derived": pa.Column(str, nullable=True, default=""),
        "variable parent": pa.Column(str, nullable=True, default=""),
        "visual exclude": pa.Column(bool, nullable=True, coerce=True, default=False, required=False),
    },
    strict="filter",
)

CodebookSchemaV1 = pa.DataFrameSchema(
    {
        "name": pa.Column(str, unique=True, checks=[
            pa.Check.str_length(min_value=1, max_value=60),
            # TODO: refine the following regex
            pa.Check.str_matches(
                r'''^[^A-Z!@#$%^&*()+\-=\[\]{};':"\\|,.<>\/?]+$'''),
        ]),
        "description": pa.Column(str),
        "data_type": pa.Column(str, checks=[
            pa.Check.isin(VariableType.__args__)
        ]),
        "measurement_unit": pa.Column(str, nullable=True, default=""),
        "formula": pa.Column(str, nullable=True, default=""),
        "category": pa.Column(str, nullable=True, default=""),
        "unit_conversion": pa.Column(str, nullable=True, default=""),
        "dependent_variable": pa.Column(str, nullable=True, default=""),
        "is_derived": pa.Column(bool, coerce=True, nullable=True, default=""),
        "unit_varies": pa.Column(bool, coerce=True, nullable=True, default=""),
        "visual_exclude": pa.Column(bool, nullable=True, coerce=True, default=False, required=False),
    },
    strict="filter",
)


@pa.check_io(df=CodebookSchemaV0, out=CodebookSchemaV1)
def cast_codebook(df: pd.DataFrame):
    return df \
        .drop("unit reference", axis=1) \
        .rename(columns={
            "variable name": "name",
            "variable description": "description",
            "variable type": "data_type",
            "unit of measurement": "measurement_unit",
            "constant unit / changing unit": "unit_varies",
            "formula": "formula",
            "parent variable": "category",
            "unit conversion": "unit_conversion",
            "original / derived": "is_derived",
            "variable parent": "dependent_variable",
            "visual exclude": "visual_exclude",
        })


class Variable(BaseModel):
    # postgres friendly name with no special characters
    name: str
    # name of the column is assumed to be the variable description
    description: str
    # postgres datatype
    data_type: PostgresDType
    measurement_unit: str | None = None
    formula: str | None  = None
    # variable category (variable selection / parent variable)
    category: str | None  = None
    unit_conversion: str | None  = None
    # variable parent (is used by some other variable)
    dependent_variable: str | None  = None
    # original / derived
    is_derived: bool = False
    # changing unit / constant unit
    unit_varies: bool = False
    visual_exclude: bool = False

    @validator("name", allow_reuse=True)
    def is_alphanumeric(cls, value):
        if not bool(re.search(r"[^a-z0-9_]", value)):
            return value
        raise ValueError(
            "can only contain lowercase alphanumeric characters and underscores")

    @validator("name", allow_reuse=True)
    def less_than_64_characters(cls, value):
        if not (len(value) > 64):
            return value
        raise ValueError("can not use more than 64 characters")

    @classmethod
    @pa.check_input(CodebookSchemaV1)
    def from_codebook(cls, df: pd.DataFrame):
        df["data_type"] = df["data_type"].str.upper()
        records = df.to_dict(orient="records")
        return [Variable(**r) for r in records]

    @classmethod
    def to_excel_codebook(cls, v: List):
        v = [i.dict() for i in v]
        def get_values(k): return [i[k] for i in v]
        def as_str(l): return [str(i) for i in l]
        df = pd.DataFrame({
            "variable name": get_values("name"),
            "variable description": get_values("description"),
            "variable type": get_values("data_type"),
            "unit of measurement": get_values("measurement_unit"),
            "constant unit / changing unit": as_str(get_values("unit_varies")),
            "formula": get_values("formula"),
            "unit reference": ["" for _ in range(len(v))],
            "parent variable": get_values("category"),
            "unit conversion": get_values("unit_conversion"),
            "original / derived": as_str(get_values("is_derived")),
            "variable parent": get_values("dependent_variable"),
            "visual exclude": get_values("visual_exclude"),
        })
        df = df.replace("nan", None)
        df.loc[max(df.index)+1,:] = None
        df = df.shift()
        df.iloc[0, :] = df.columns.str.title()
        df.loc[max(df.index)+1,:] = None
        df = df.shift()
        df.iloc[0, 0] = "Dataset Variables & Formulas Used"
        return df

