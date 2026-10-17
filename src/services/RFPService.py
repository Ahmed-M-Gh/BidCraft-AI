from config import get_settings
from pathlib import Path
from .get_clients import get_chroma_client, get_embedding_model
from fastapi import UploadFile
from src.schema import RFPReaderResponse, RetrievedEvidence
from uuid import uuid4
import logging 
logger = logging.getLogger(__name__)
from unstructured.partition.pdf import partition_pdf
from typing import List


class RFPService:
    def __init__(self):
        self.settings = get_settings()
        self.temp_dir = Path(self.settings.TEMP_DIR)
        self.chroma_client = get_chroma_client()
        self.embedding_model = get_embedding_model()
        
        
    def process_rfp_and_retrieved(self, file:UploadFile, client_name:str, tone:str) -> RFPReaderResponse:
        """
        Processes the incoming RFP file, extracts text, searches ChromaDB for matching Company knowledge,
        and returns the structure proposal foundation with advice
        """
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        unique_filename = f"{uuid4().hex}_{file.filename}"
        file_path = self.temp_dir/unique_filename
        
        try:
            # 1. Save RFP file temporarily
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())
            logger.info(f"Parsing RFP file: {file.filename}")
            
            # 2. Extract text using fast strategy
            elements = partition_pdf(
                filename=str(file_path),
                strategy=self.settings.PARTITION_STRATEGY,
                infer_table_structure=False
            )
            
            rfp_text = "\n".join([el.text for el in elements if el.text])
            if not rfp_text.strip():
                raise ValueError("Could not Extract any text from the provided RFP file.")
            
            # 3. Generating embeddings for the RFP text to search in database
            query_text = rfp_text[:2000]
            logger.info("Generating embedding for RFP query...")
            query_vector = self.embedding_model.encode(query_text).tolist()
            
            # 4. Query ChromaDB for top relevant company knowledge chunks
            collection = self.chroma_client.get_or_create_collection(name=self.settings.COLLECTION_NAME)
            
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            retrieved_evidence:List[RetrievedEvidence] = []
            
            if results and results["documents"]:
                docs = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]
                ids = results["ids"][0]
                
                for chunk_id, doc, meta, distance in zip(ids, docs, metadatas, distances):
                    # convert similarity distance to score
                    similarity = float(1.0/(1.0 + distance))
                    
                    retrieved_evidence.append(
                        RetrievedEvidence(
                            chunk_id=chunk_id,
                            source_file=meta.get("file_name", "unknown"),
                            similarity_score=round(similarity, 4),
                            content_snippet=doc[:300]+"..." if len(doc) > 300 else doc
                        )
                    )
                    
            # 5. Generating A draft for proposal
            evidence_summary = "\n".join([f"- From {ev.source_file} : {ev.content_snippet}" for ev in retrieved_evidence])
            
            generated_proposal = (
                f"# Proposal Draft for {client_name}\n"
                f"**Tone:** {tone}\n\n"
                f"## 1. Executive Summary\n"
                f"Based on the analysis of the RFP requirements, BidCraft AI is positioned to deliver an exceptional solution leveraging our proven core competencies.\n\n"
                f"## 2. Relevant Past Performance & Evidence\n"
                f"{evidence_summary}\n\n"
                f"## 3. Proposed Implementation Scope\n"
                f"Our local-first architecture ensures total data privacy, speed, and strict compliance with the requested technical parameters."
            )
            
            return RFPReaderResponse(
                file_name=file.filename,
                generated_proposal=generated_proposal,
                retrieved_evidence=retrieved_evidence
            )
            
        except Exception as e:
            logger.error(f"Error Parsing RFP: {str(e)}")
            raise e
        
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)