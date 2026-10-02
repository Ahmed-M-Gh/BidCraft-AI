import os 
from src.config import get_settings
from typing import List
from fastapi import UploadFile
from pathlib import Path
import uuid
import shutil
import logging
logger = logging.getLogger(__name__)
from unstructured.partition.pdf import partition_pdf
from langchain_text_splitters import MarkdownHeaderTextSplitter
from .get_clients import get_chroma_client, get_embedding_model

class FileProcess:
    def __init__(self):
        self.settings = get_settings()
        self.temp_dir = Path(self.settings.TEMP_DIR)
        self.chroma_client = get_chroma_client()
        self.embedding_model = get_embedding_model()
        
    def save_uploaded_files_temp(self, files:List[UploadFile]):
        """
        it saves the uploaded files in a temporary folder on the hard drive using streaming to prevent the RAM from getting full.
        """
        # make sure the folder is exist and create it if it's not
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files_paths = []
        for file in files:
            # creating File names to prevent same name conflict
            unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
            file_path = self.temp_dir/unique_filename
            
            # Write file with Streaming mode
            with open(file_path, "wb") as Buffer:
                shutil.copyfileobj(file.file, Buffer)
                
            saved_files_paths.append(str(file_path))
            
        return saved_files_paths
    
    @staticmethod
    def cleanup_temp_files(file_paths: List[str]):
        """
        Cleaning files after preprocessing
        """
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    
            except Exception as e:
                logger.error(f"Failed to delete temp file {path} : {e}")
                
    def parse_documents(self, file_paths:List[str]) -> List[dict]:
        """
        Iterates over the saved temporary files, parses tem,
        and extracts the text (preferably as Markdown).
        Returns a list of dictionaries containing the parsed text and metadata.
        """
        parsed_documents = []
        
        for path in file_paths:
            logger.info(f"Starting to parse:{path}")
            
            try:
                # Extract tables precisely
                elements = partition_pdf(
                    filename=path,
                    strategy=self.settings.PARTITION_STRATEGY,
                    infer_table_structure=True,
                )
                
                # Collecting elements in a one text
                markdown_content = ""
                for el in elements:
                    category = el.category
                    
                    if category == "Title":
                        markdown_content += f"\n## {el.text}\n\n"
                    elif category == "Table":
                        html_table = getattr(el.metadata, "text_as_html", el.text)
                        markdown_content += f"\n{html_table}\n\n"
                    elif category == "ListItem":
                        markdown_content += f"- {el.text}\n"
                    else: # the rest of normal text
                        markdown_content += f"{el.text}\n\n"
                
                parsed_documents.append({
                    "file_name" : Path(path).name.split("_", 1)[-1], # removing uuid from the name
                    "content" : markdown_content.strip()
                })
                
                logger.info(f"Successfully parsed : {path}")
            
            
            except Exception as e:
                logger.error(f"Failed to parse {path}. Error: {e}")
                
                parsed_documents.append({
                    "file_name" : Path(path).name.split("_", 1)[-1],
                    "content" : "",
                    "error" : str(e)
                })
        return parsed_documents
    
    def chunk_document(self, parsed_documents: List[dict]) -> List[dict]:
        """
        Splits the markdown content into smaller chunks based on headers.
        Attaches the file_name and header structured as metadata to each chunk.
        """
        
        # Specify the headers we will chunk in
        header_to_split_on = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3"),
        ]
        
        # chunks setting
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=header_to_split_on,
            strip_headers=False
        )
        
        all_chunks = []
        
        for doc in parsed_documents:
            file_name = doc.get("file_name")
            content = doc.get("content")
            
            # skip files that failed to extract
            if not content:
                logger.error(f"failed to Chunk document : {file_name}")
                continue
            
            logger.info(f"Chunking document : {file_name}")
            
            splits = markdown_splitter.split_text(content)
            
            for split in splits:
                # merge document metadata with the file name
                chunk_metadata = split.metadata
                chunk_metadata["file_name"] = file_name
                
                all_chunks.append({
                    "content" : split.page_content,
                    "metadata" : chunk_metadata
                })
                
        logger.info(f"Total chunks created from all documents: {len(all_chunks)}")
        return all_chunks
    
    def generate_embeddings(self, chunks: List[dict], batch_size:int) -> List[dict]:
        """
        Take chunks and embedding it 
        """
        if not chunks:
            return []
        
        texts = [chunk.get("content") for chunk in chunks]
        logger.info(f"Generating embeddings for {len(texts)} chunks in batches of {batch_size}...")
        
        # convert chunks to vectors
        vectors = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i+batch_size]
            
            batch_vectors = self.embedding_model.encode(batch_texts).tolist()
            vectors.extend(batch_vectors)
        
        processed_chunks = []
        for chunk, vector in zip(chunks, vectors):
            chunk_with_embedding = chunk.copy()
            chunk_with_embedding["embedding"] = vector
            processed_chunks.append(chunk_with_embedding)
            
        return processed_chunks

        
    def vectorize_and_store(self, chunks: List[dict], db_batch_size:int) -> str:
        """
        Takes the text embeddings, and stores the in chromadb.
        Returns the name of the collection used.
        """
        embedding_chunks = self.generate_embeddings(chunks, batch_size=self.settings.BATCH_SIZE)
        if not embedding_chunks:
            logger.warning(f"No Chunks to store.")
            return self.settings.COLLECTION_NAME
        
        collection = self.chroma_client.get_or_create_collection(name=self.settings.COLLECTION_NAME)
        
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for i, chunk in enumerate(embedding_chunks):
            file_name = chunk["metadata"].get('file_name', 'unknown')
            chunk_id = f"{file_name}_chunk{i}_{uuid.uuid4().hex[:8]}"
            
            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append(chunk["metadata"])
            embeddings.append(chunk["embedding"])
        
        if documents:
            logger.info(f"Storing {len(documents)} chunks in ChromaDB collection: {self.settings.COLLECTION_NAME}")
            
            for i in range(0, len(ids), db_batch_size):
                batch_ids = ids[i:i + db_batch_size]
                batch_documents = documents[i:i+db_batch_size]
                batch_metadatas = metadatas[i:i+db_batch_size]
                batch_embeddings = embeddings[i:i+db_batch_size]
            
                collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    embeddings=batch_embeddings
                )
            
        return self.settings.COLLECTION_NAME
    