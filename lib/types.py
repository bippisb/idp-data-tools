import re
from pydantic import BaseModel, validator
from typing import Literal, Dict, List


def alphanumeric_name(string: str):
    return "".join(re.findall(r"[\w\d ]", string.strip().lower())).replace(" ", "_")


PostgresDType = Literal["NUMERIC", "BOOLEAN", "TEXT", "DATE", "TIMESTAMP"]
polars_dtype_to_postgres_dtype_mapping: Dict[str, PostgresDType] = {
    "UInt8": "NUMERIC",
    "UInt16": "NUMERIC",
    "UInt32": "NUMERIC",
    "UInt64": "NUMERIC",
    "Int8": "NUMERIC",
    "Int16": "NUMERIC",
    "Int32": "NUMERIC",
    "Int64": "NUMERIC",
    "Float32": "NUMERIC",
    "Float64": "NUMERIC",
    "Boolean": "BOOLEAN",
    "Utf8": "TEXT",
    "Categorical": "TEXT",
    "Date": "DATE",
    "Datetime": "TIMESTAMP",
}


class Variable(BaseModel):
    # postgres friendly name with no special characters
    name: str
    # name of the column is assumed to be the variable description
    description: str
    # postgres datatype
    data_type: PostgresDType
    measurement_unit: str | None = None
    formula: str | None = None
    # variable category (variable selection / parent variable)
    category: str | None = None
    unit_conversion: str | None = None
    # variable parent (is used by some other variable)
    dependent_variable: str | None = None
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


Sectors = Literal[
    "Fisheries and Animal Husbandry",
    "Agriculture",
    "Culture and Tourism",
    "Consumer Affairs",
    "Communications",
    "Economy",
    "COVID-19",
    "Education",
    "Financial Inclusion",
    "General",
    "Health",
    "Human Resource Development",
    "Housing",
    "Industries",
    "Natural Resources",
    "Rural Development",
    "Socio Economic",
    "Youth Affairs",
    "Other"
]

GranularityLevel = Literal[
    "All India",
    "State",
    "District",
    "Sub-District",
    "Block",
    "Village",
    "Assembly Constituency",
    "Parliamentary Constituency",
    "Gram Panchayat",
    "Other",
]

Frequency = Literal[
    "Daily",
    "Weekly",
    "Fortnightly",
    "Monthly",
    "Quarterly",
    "Yearly",
    "Quinquennially",
    "Other"
]


class ResourceMetadata(BaseModel):
    # domains are referred to as sectors in ckan
    domains: List[str]
    # dataset name is equivalent to package name in ckan
    dataset_name: str
    # Lowest level for which the data is available
    granularity_level: str
    # frequency at which the data is released
    frequency: str
    source_name: str
    source_link: str
    # when was the data last retrieved by us
    data_retrieval_date: str
    # when was the latest data last released on source
    data_last_updated: str
    data_extraction_page: str
    # dataset description
    about: str
    # data collection methodology used by the source
    methodology: str
    # name of the resource in ckan
    resource: str
    # what insights does the dataset provide
    data_insights: str
    # SEO tags
    tags: List[str]
    # similar resources
    similar_datasets: List[str]


class AdditionalInformation(BaseModel):
    years_covered: str | None
    notes: str | None
    no_of_states: int | None
    no_of_districts: int | None
    no_of_tehsils: int | None
    no_of_villages: int | None
    no_of_gps: int | None
    no_of_indicators: int
