import re
from pydantic import BaseModel, validator
from typing import Literal, Dict, List


def alphanumeric_name(string: str):
    return "".join(re.findall(r"[\w\d ]", string.strip().lower())).replace(" ", "_")


PostgresDType = Literal["NUMERIC", "BOOLEAN", "TEXT", "DATE", "TIMESTAMP", "CATEGORICAL"]
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
    "Categorical": "CATEGORICAL",
    "Date": "DATE",
    "Datetime": "TIMESTAMP",
}




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
    "Market Center",
]

Frequency = Literal[
    "Daily",
    "Weekly",
    "Fortnightly",
    "Monthly",
    "Quarterly",
    "Yearly",
    "Quinquennially"
]