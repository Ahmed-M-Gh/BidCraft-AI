from pydantic import BaseModel, Field
from typing import List

class FileDetail(BaseModel):
    filename:str
    chunks:int
    status:str


class FileProcessResponse(BaseModel):
    file_processed:int
    total_chunk_created:int
    vector_db_collection:str
    details:List[FileDetail]