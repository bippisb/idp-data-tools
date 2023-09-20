import pandera as pa
from pydantic import BaseModel
import pandas as pd

additional_information_fields_v0 = [
    "years covered",
    "number of state(s) / union territories",
    "additional information",
    "number of district(s)",
    "number of tehsil(s)",
    "number of gp",
    "number of villages",
    "number of indicators",
]

AdditionalInfoSchemaV0 = pa.DataFrameSchema({
    "years covered": pa.Column(str, nullable=True, coerce=True),
    "number of state(s) / union territories": pa.Column(object, nullable=True, coerce=True),
    "additional information": pa.Column(str, nullable=True),
    "number of district(s)": pa.Column(object, nullable=True, coerce=True),
    "number of tehsil(s)": pa.Column(object, nullable=True, coerce=True),
    "number of gp": pa.Column(object, nullable=True, coerce=True),
    "number of villages": pa.Column(object, nullable=True, coerce=True),
    "number of indicators": pa.Column(object, coerce=True),
})

field_mapping_v0_to_json = {
    "years covered": "years_covered",
    "number of state(s) / union territories": "no_of_states",
    "additional information": "notes",
    "number of district(s)": "no_of_districts",
    "number of tehsil(s)": "no_of_tehsils",
    "number of gp": "no_of_gps",
    "number of villages": "no_of_villages",
    "number of indicators": "no_of_indicators",
}


class AdditionalInformation(BaseModel):
    years_covered: str
    notes: str = None
    no_of_states: int = None
    no_of_districts: int = None
    no_of_tehsils: int = None
    no_of_villages: int = None
    no_of_gps: int = None
    no_of_indicators: int

    @classmethod
    @pa.check_input(AdditionalInfoSchemaV0)
    def from_codebook(cls, df: pd.DataFrame):
        df = df.rename(columns=field_mapping_v0_to_json)
        record = df.to_dict(orient="records")[0]
        numerical_fields = [
            "no_of_states",
            "no_of_districts",
            "no_of_tehsils",
            "no_of_villages",
            "no_of_gps",
            "no_of_indicators",
        ]
        for key in numerical_fields:
            val = record[key]
            record[key] = int(val) if not pd.isna(val) else None
        return AdditionalInformation(**record)

    def to_excel_codebook(self):
        addi = self.dict()
        json_to_v0 = {
            v: k
            for k, v in field_mapping_v0_to_json.items()
        }
        df = pd.DataFrame({
            "key": [json_to_v0[k].title() for k in addi.keys()],
            "value": addi.values()
        })
        df = df.replace("nan", None)
        df.loc[max(df.index)+1, :] = None
        df = df.shift()
        df.iloc[0, 0] = "Additional Information"
        return df
