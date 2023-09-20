from lib.bipp.codebook.schema.variables import Variable
from lib.bipp.codebook.schema.additional_info import AdditionalInformation
from lib.bipp.codebook.schema.metadata import ResourceMetadata
from pydantic import BaseModel


class Codebook(BaseModel):
    variables: list[Variable]
    metadata: ResourceMetadata
    additional_information: AdditionalInformation
