from fastapi import APIRouter, UploadFile, File
from typing import List
from src.schema import FileProcessResponse

reader_router = APIRouter(
    prefix=["api/v1.0"],
    tags=["reading-company-contracts"]
)


@reader_router.post("/process-contracts", response_model=FileProcessResponse)
async def process_contracts(request:List[UploadFile]=File(...)):
    pass