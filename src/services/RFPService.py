from src.config import get_settings
from pathlib import Path
from .get_clients import get_chroma_client, get_embedding_model
from fastapi import UploadFile
from src.schema import RFPReaderResponse, RetrievedEvidence
from uuid import uuid4
import logging 
logger = logging.getLogger(__name__)
from unstructured.partition.pdf import partition_pdf
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

class RFPService:
    def __init__(self):
        self.settings = get_settings()
        self.temp_dir = Path(self.settings.TEMP_DIR)
        self.chroma_client = get_chroma_client()
        self.embedding_model = get_embedding_model()
        
        self.llm = ChatGroq(
            api_key=self.settings.GROQ_API_KEY,
            model_name=self.settings.GROQ_MODEL_NAME,
            temperature=self.settings.TEMPERATURE
        )
        
        
    def llm_support(self, client_name:str, tone:str, rfp_summary:str, retrieved_evidence:List[RetrievedEvidence]) -> str:
        """
        Takes the raw RFP summary and retrieved evidence list, passes them to Groq LLM,
        and generates a clean, professional B2B proposal draft in markdown format.
        """
        
        evidence_text = "\n\n".join([
            f"- Source ({ev.source_file}) : {ev.content_snippet}"
            for ev in retrieved_evidence
        ]) if retrieved_evidence else "No specific past experience evidence found."
        
        prompt_template = ChatPromptTemplate([
            ("system", (
                "You are an expert B2B Proposal Writer and solutions Architect At BidCraft AI. \n"
                "Your Task is to synthesize the client's RFP requirements along with our internal company evidence "
                "into a persuasive, professional, and well-structured proposal draft for the client '{client_name}'\n"
                "Tone requested: {tone}.\n\n"
                "STRICT RULES:\n"
                "1. Strictly base our technical capabilities and past performance on the provided evidence.\n"
                "2. Do NOT invent past projects or hallucinate capabilities not supported by evidence.\n"
                "3. Clean Up any raw formatting HTML tags, or broken texts from the evidence snippets.\n"
                "4. Structure the output into clear Markdown sections: Executive Summary, Technical Solution & Proven Experience, and Implementation Approach."
            )),
            ("human", (
                "### Client RFP Requirements / Summary:\n"
                "{rfp_summary}\n\n"
                "### Internal Company Knowledge & Evidence:\n"
                "{evidence_text}\n\n"
                "Please generate the complete professional proposal draft."
            ))
        ])
        
        chain = prompt_template | self.llm
        
        try:
            logger.info("Generating professional proposal via Groq LLM...")
            response=chain.invoke({
                "client_name":client_name,
                "tone":tone,
                "rfp_summary":rfp_summary,
                "evidence_text":evidence_text
            })
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error generating proposal via Groq LLM: {str(e)}")
            raise f"Error in LLM generating: {str(e)}"
        
    
    def process_rfp_and_retrieved(self, file: UploadFile, client_name: str, tone: str) -> RFPReaderResponse:
        """
        Processes the incoming RFP file, extracts text, searches ChromaDB for matching Company knowledge,
        and returns the structured proposal foundation with advice
        """
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        unique_filename = f"{uuid4().hex}_{file.filename}"
        file_path = self.temp_dir / unique_filename
        
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
            
            retrieved_evidence: List[RetrievedEvidence] = []
            
            if results and results["documents"]:
                docs = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]
                ids = results["ids"][0]
                
                for chunk_id, doc, meta, distance in zip(ids, docs, metadatas, distances):
                    # convert similarity distance to score
                    similarity = float(1.0 / (1.0 + distance))
                    
                    retrieved_evidence.append(
                        RetrievedEvidence(
                            chunk_id=chunk_id,
                            source_file=meta.get("file_name", "unknown"),
                            similarity_score=round(similarity, 4),
                            content_snippet=doc[:300] + "..." if len(doc) > 300 else doc
                        )
                    )
                    
            # 5. Generating A draft for proposal using Groq via llm_support
            generated_proposal = self.llm_support(
                client_name=client_name,
                tone=tone,
                rfp_summary=rfp_text[:3000],
                retrieved_evidence=retrieved_evidence
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