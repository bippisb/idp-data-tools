from typing import List
import pandera as pa
from pydantic import BaseModel
import pandas as pd

metadata_fields_v0 = [
    "domain",
    "dataset name",
    "granularity level",
    "frequency",
    "source name",
    "source link",
    "data retrieval date",
    "data last updated",
    "data extraction page",
    "about",
    "methodology",
    "resource",
    "data insights",
    "tags",
    "similar datasets",
]

MetadataSchemaV0 = pa.DataFrameSchema({
    "domain": pa.Column(str),
    "dataset name": pa.Column(str),
    "granularity level": pa.Column(str),
    "frequency": pa.Column(str),
    "source name": pa.Column(str),
    "source link": pa.Column(str, nullable=True),
    "data retrieval date": pa.Column(str, coerce=True),
    "data last updated": pa.Column(str, nullable=True, coerce=True),
    "data extraction page": pa.Column(str, nullable=True),
    "about": pa.Column(str, nullable=True),
    "methodology": pa.Column(str, nullable=True),
    "resource": pa.Column(str),
    "data insights": pa.Column(str, nullable=True),
    "tags": pa.Column(str),
    "similar datasets": pa.Column(str, nullable=True),
}, strict="filter")


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
    # name of the resource in ckan"
    resource: str
    # what insights does the dataset provide
    data_insights: str
    # SEO tags
    tags: List[str]
    # similar resources
    similar_datasets: List[str]

    @classmethod
    @pa.check_input(MetadataSchemaV0)
    def from_codebook(cls, df: pd.DataFrame):
        df.columns = df.columns.str.replace(" ", "_")
        df = df.rename(columns={"domain": "domains"})
        record = df.to_dict(orient="records")[0]
        record.update({
            key: list(filter(lambda s: s != "", map(
                str.strip, record[key].split(",")))) if type(record[key]) == str else []
            for key in ["domains", "tags", "similar_datasets"]
        })
        return ResourceMetadata(**record)

    def to_excel_codebook(self):
        m = {
            k.replace("_", " ").title(): ", ".join(v) if type(v) == list else v
            for k, v in self.dict().items()
        }
        df = pd.DataFrame({
            "key": m.keys(),
            "value": m.values()
        })
        df = df.replace("nan", None)

        df.loc[max(df.index)+1, :] = None
        df = df.shift()
        df.iloc[0, 0] = "Metadata Information"
        return df
