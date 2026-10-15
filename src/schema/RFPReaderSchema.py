from pydantic import BaseModel, Field
from typing import List

class RetrievedEvidence(BaseModel):
    chunk_id: str
    source_file: str
    similarity_score: float
    content_snippet: str
    
class RFPReaderResponse(BaseModel):
    file_name: str
    generated_proposal: str
    retrieved_evidence: List[RetrievedEvidence]