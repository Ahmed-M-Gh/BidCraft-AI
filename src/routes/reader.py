from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from src.schema import FileProcessResponse, FileDetail
from src.services import FileProcess
import logging
logger = logging.getLogger(__name__)
from collections import Counter
from src.config import get_settings
settings = get_settings()

reader_router = APIRouter(
    prefix="/api/v1.0/documents",
    tags=["rKnowledge Base"]
)


@reader_router.post("/process-company-knowledge", response_model=FileProcessResponse)
async def process_contracts(background_tasks:BackgroundTasks, request:List[UploadFile]=File(...)):
    """
    Path to receive data and store it in ChromaDB
    """
    if not request:
        raise HTTPException(status_code=400, detail="NO FILE UPLOAD.")
    
    processor = FileProcess()
    saved_paths = []
    
    try:
        # Save files temporarily in hard drive
        saved_paths = processor.save_uploaded_files_temp(request)
        
        # Parsing text
        parsed_docs = processor.parse_documents(saved_paths)
        
        # get check if all files failed
        valid_docs = [
            doc for doc in parsed_docs
            if doc.get("content")
        ]
        if not valid_docs:
            logger.error("Failed To Extract text form all Files")
            raise HTTPException(status_code=422, detail="Failed to Extract text from all provided files.")
        
        # chunking text
        chunks = processor.chunk_document(valid_docs)
        if not chunks:
            logger.error("Failed to chunk")
            raise HTTPException(status_code=422, detail="No Valid chunks generated.")
            
        collection_name = processor.vectorize_and_store(chunks, db_batch_size=settings.DB_BATCH_SIZE)
        
        # cleaning temporarily file_paths in Background
        background_tasks.add_task(processor.cleanup_temp_files, saved_paths)
        
        # Response Schema
        chunk_counts = Counter(chunk["metadata"].get("file_name") for chunk in chunks)
        
        details = []
        for doc in parsed_docs:
            filename = doc.get("file_name", "unknown")
            
            # Determine the file status and count of chunks
            if doc.get("error") or not doc.get("content"):
                status = "failed"
                c_count = 0
            else:
                status = "success"
                c_count = chunk_counts.get(filename, 0)
            
            details.append(FileDetail(filename=filename, chunks=c_count, status=status))
            
        # Return final Response
        
        return FileProcessResponse(
            file_processed=len(valid_docs),
            total_chunk_created=len(chunks),
            vector_db_collection=collection_name,
            details=details
        )
        
    except Exception as e:
        logger.error(f"Error Processing files: {e}")
        
        if saved_paths:
            processor.cleanup_temp_files(saved_paths)
        raise HTTPException(status_code=500, detail=str(e))