import io
import pandas as pd
from lib.bipp.codebook.schema.additional_info import AdditionalInformation
from lib.bipp.codebook.schema.metadata import ResourceMetadata
from lib.bipp.codebook.schema.variables import Variable


def to_excel_codebook(cb: dict):
    """Converts a json codebook to an Excel Workbook"""

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, mode="x") as writer:
        # encode variables / codebook sheet
        v = [Variable(**v) for v in cb["variables"]]
        v = Variable.to_excel_codebook(v)
        v.to_excel(writer, sheet_name="codebook", index=None, header=None)
        del v

        # encode metadata
        meta = ResourceMetadata(**cb["metadata"])
        meta = ResourceMetadata.to_excel_codebook(meta)
        meta.to_excel(writer, sheet_name="metadata information",
                      index=None, header=None)
        del meta

        # encode additional information
        addi = AdditionalInformation(**cb["additional_information"])
        addi = AdditionalInformation.to_excel_codebook(addi)
        addi.to_excel(writer, sheet_name="additional information",
                      index=None, header=None)
        del addi

    return buffer
