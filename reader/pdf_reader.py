from pathlib import Path
from typing import Dict, Any, List, Union
import os
import pypdf

from autotask.document.base import Document
from autotask.document.reader.file_reader import FileReader
from autotask.document.reader.reader_registry import ReaderRegistry
from autotask.utils.log import logger

try:
    from chonkie import RecursiveChunker, RecursiveRules
    CHONKIE_AVAILABLE = True
except ImportError:
    logger.warning("Chonkie library not installed. Smart chunking will be disabled. Install with: pip install chonkie")
    CHONKIE_AVAILABLE = False


@ReaderRegistry.register_reader([".pdf"])
class PDFReader(FileReader):
    """
    PDF file reader with smart text chunking support
    """
    
    FILE_FORMATS = [".pdf"]
    
    PARAMS = {
        "chunk_size": {
            "label": "Chunk Size",
            "description": "Maximum tokens per chunk",
            "type": "INTEGER",
            "default": 1024
        },
        "extract_metadata": {
            "label": "Extract Metadata",
            "description": "Whether to extract PDF metadata",
            "type": "BOOLEAN",
            "default": True
        }
    }
    
    def read_file(self, file_path: Path, params: Dict[str, Any]) -> List[Document]:
        """
        Read PDF file and return list of Document objects
        
        Args:
            file_path: Path to PDF file
            params: Reader parameters
            
        Returns:
            List[Document]: List of documents with PDF content
        """
        chunk_size = params.get("chunk_size", 1024)
        extract_metadata = params.get("extract_metadata", True)
        
        try:
            # Read PDF file
            with open(file_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)
                
                # Extract text from all pages
                content = ""
                for page in pdf.pages:
                    content += page.extract_text() + "\n\n"
                
                # Create metadata
                metadata = {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "extension": file_path.suffix,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path),
                    "page_count": len(pdf.pages)
                }
                
                # Add PDF-specific metadata if requested
                if extract_metadata and pdf.metadata:
                    metadata.update({
                        "title": pdf.metadata.get("/Title", ""),
                        "author": pdf.metadata.get("/Author", ""),
                        "subject": pdf.metadata.get("/Subject", ""),
                        "creator": pdf.metadata.get("/Creator", ""),
                        "producer": pdf.metadata.get("/Producer", ""),
                        "creation_date": pdf.metadata.get("/CreationDate", ""),
                        "modification_date": pdf.metadata.get("/ModDate", "")
                    })
                
                # For short content, return single document
                if len(content) < 1000 or not CHONKIE_AVAILABLE:
                    document = Document(
                        id=str(file_path),
                        name=file_path.stem,
                        content=content,
                        meta_data=metadata
                    )
                    return [document]
                
                # For longer content, use smart chunking
                try:
                    logger.info(f"Applying smart chunking to PDF: {file_path}")
                    
                    chunker = RecursiveChunker(
                        tokenizer_or_token_counter="gpt2",
                        chunk_size=chunk_size,
                        rules=RecursiveRules(),
                        min_characters_per_chunk=12,
                        return_type="chunks"
                    )
                    
                    chunks = chunker(content)
                    logger.info(f"Split PDF into {len(chunks)} chunks")
                    
                    documents = []
                    for i, chunk in enumerate(chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata["chunk_id"] = i + 1
                        
                        chunk_doc = Document(
                            id=f"{str(file_path)}_{i+1}",
                            name=f"{file_path.stem}_chunk_{i+1}",
                            content=chunk.text,
                            meta_data=chunk_metadata
                        )
                        documents.append(chunk_doc)
                    
                    return documents
                    
                except Exception as chunk_error:
                    logger.error(f"Smart chunking failed: {str(chunk_error)}, returning full document")
                    document = Document(
                        id=str(file_path),
                        name=file_path.stem,
                        content=content,
                        meta_data=metadata
                    )
                    return [document]
                    
        except Exception as e:
            logger.error(f"Failed to read PDF file {file_path}: {str(e)}")
            raise
