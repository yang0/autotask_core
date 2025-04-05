from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import os
import uuid

from autotask.document.base import Document
from autotask.document.reader.file_reader import FileReader
from autotask.document.reader.reader_registry import ReaderRegistry
from autotask.utils.log import logger

# Import RecursiveChunker
try:
    from chonkie import RecursiveChunker, RecursiveRules
    CHONKIE_AVAILABLE = True
except ImportError:
    logger.warning("Chonkie library not installed. Smart chunking will be disabled. Install with: pip install chonkie")
    CHONKIE_AVAILABLE = False


@ReaderRegistry.register_reader([".txt", ".md", ".csv", ".json", ".xml", ".html", ".log"])
class TextReader(FileReader):
    """
    General text file reader
    
    Supports various text file formats like .txt, .md, .csv, .json, .xml, .html, .log etc.
    Uses RecursiveChunker by default for smart text chunking
    """
    
    # Supported file formats
    FILE_FORMATS = [".txt", ".md", ".csv", ".json", ".xml", ".html", ".log"]
    
    # Parameter definitions
    PARAMS = {
        "encoding": {
            "label": "File Encoding",
            "description": "Encoding format for reading the file",
            "type": "STRING",
            "default": "utf-8"
        },
        "skip_empty_lines": {
            "label": "Skip Empty Lines",
            "description": "Whether to skip empty lines",
            "type": "BOOLEAN",
            "default": True
        },
        "max_length": {
            "label": "Maximum Length",
            "description": "Maximum number of characters to read, 0 means no limit",
            "type": "INTEGER",
            "default": 0
        },
        "extract_metadata": {
            "label": "Extract Metadata",
            "description": "Whether to extract metadata from the file",
            "type": "BOOLEAN",
            "default": True
        },
        "chunk_size": {
            "label": "Chunk Size",
            "description": "Maximum number of tokens per chunk",
            "type": "INTEGER",
            "default": 1024
        }
    }
    
    def read_file(self, file_path: Path, params: Dict[str, Any]) -> List[Document]:
        """
        Read text file and return list of Documents
        
        Uses RecursiveChunker by default for smart text chunking
        
        Args:
            file_path: Path to the file
            params: Parameter dictionary
            
        Returns:
            List[Document]: List of documents containing text content
            
        Raises:
            UnicodeDecodeError: Encoding error
            IOError: File reading error
        """
        # Get configurations from parameters
        encoding = params.get("encoding", "utf-8")
        skip_empty_lines = params.get("skip_empty_lines", True)
        max_length = params.get("max_length", 0)
        extract_metadata = params.get("extract_metadata", True)
        chunk_size = params.get("chunk_size", 1024)
        
        try:
            # Read file content
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            # Limit maximum length
            if max_length > 0 and len(content) > max_length:
                content = content[:max_length]
                logger.warning(f"File {file_path} content truncated to {max_length} characters")
                
            # Handle empty lines
            if skip_empty_lines:
                content = "\n".join(line for line in content.split("\n") if line.strip())
            
            # Extract metadata
            metadata = {}
            if extract_metadata:
                metadata = {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "extension": file_path.suffix,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                }
            
            # Check content length, don't chunk small texts
            if len(content) < 1000 or not CHONKIE_AVAILABLE:
                # For short content, create single Document object
                document = Document(
                    id=str(file_path),
                    name=file_path.stem,
                    content=content,
                    meta_data=metadata
                )
                return [document]
            
            # For long content, apply smart chunking
            try:
                logger.info(f"Applying smart chunking to file {file_path}")
                
                # Create chunker
                chunker = RecursiveChunker(
                    tokenizer_or_token_counter="gpt2",  # Initialize with the gpt2 tokenizer
                    chunk_size=chunk_size,              # Maximum tokens per chunk
                    rules=RecursiveRules(),            # Default rules
                    min_characters_per_chunk=12,       # Minimum number of characters per chunk
                    return_type="chunks"               # Return type of the chunker; "chunks" or "texts"
                )
                
                # Execute chunking
                chunks = chunker(content)
                logger.info(f"File {file_path} split into {len(chunks)} chunks")
                
                # Create Document objects for each chunk
                documents = []
                for i, chunk in enumerate(chunks):
                    # Copy metadata and add chunk information
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_id": i + 1,
                    })
                    
                    # Create chunk document
                    chunk_doc = Document(
                        id=f"{str(file_path)}_{i+1}",
                        name=f"{file_path.stem}_chunk_{i+1}",
                        content=chunk.text,
                        meta_data=chunk_metadata
                    )
                    documents.append(chunk_doc)
                
                return documents
                
            except Exception as chunk_error:
                logger.error(f"Error during smart chunking: {str(chunk_error)}, returning full document")
                # On chunking failure, create single Document object
                document = Document(
                    id=str(file_path),
                    name=file_path.stem,
                    content=content,
                    meta_data=metadata
                )
                return [document]
            
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error when reading {file_path}: {str(e)}")
            # Try alternative encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                logger.warning(f"Fallback to latin-1 encoding for {file_path}")
                
                document = Document(
                    id=str(file_path),
                    name=file_path.stem,
                    content=content,
                    meta_data={"source": str(file_path), "encoding_fallback": True}
                )
                return [document]
            except Exception as e2:
                logger.error(f"Failed to read file with fallback encoding: {str(e2)}")
                raise
                
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            raise


# Additional text readers can be added for specific types, like CSV-specific handling
@ReaderRegistry.register_reader([".csv"])
class CSVReader(TextReader):
    """CSV file specific reader for handling CSV-specific format requirements"""
    
    FILE_FORMATS = [".csv"]
    
    PARAMS = {
        "encoding": {
            "label": "File Encoding",
            "description": "Encoding format for reading the file",
            "type": "STRING", 
            "default": "utf-8"
        },
        "delimiter": {
            "label": "Delimiter",
            "description": "CSV field delimiter",
            "type": "STRING",
            "default": ","
        },
        "has_header": {
            "label": "Has Header",
            "description": "Whether CSV file contains a header row",
            "type": "BOOLEAN",
            "default": True
        },
        "chunk_size": {
            "label": "Chunk Size",
            "description": "Maximum number of tokens per chunk",
            "type": "INTEGER",
            "default": 1024
        }
    }
    
    def read_file(self, file_path: Path, params: Dict[str, Any]) -> List[Document]:
        """Read CSV file with specific handling"""
        import csv
        
        encoding = params.get("encoding", "utf-8")
        delimiter = params.get("delimiter", ",")
        has_header = params.get("has_header", True)
        chunk_size = params.get("chunk_size", 1024)
        
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                csv_reader = csv.reader(csvfile, delimiter=delimiter)
                
                rows = list(csv_reader)
                header = rows[0] if has_header and rows else []
                data_rows = rows[1:] if has_header and len(rows) > 1 else rows
                
                # Convert CSV data to formatted text
                if has_header and header:
                    content = delimiter.join(header) + "\n"
                    content += "\n".join(delimiter.join(row) for row in data_rows)
                else:
                    content = "\n".join(delimiter.join(row) for row in data_rows)
                
                # Create basic metadata
                metadata = {
                    "source": str(file_path),
                    "file_type": "csv",
                    "row_count": len(data_rows),
                    "column_count": len(header) if header else (len(data_rows[0]) if data_rows else 0)
                }
                                
                # For long content, apply smart chunking
                try:
                    logger.info(f"Applying smart chunking to file {file_path}")
                    
                    # Create chunker
                    chunker = RecursiveChunker(
                        tokenizer_or_token_counter="gpt2",  # Initialize with the gpt2 tokenizer
                        chunk_size=chunk_size,              # Maximum tokens per chunk
                        rules=RecursiveRules(),            # Default rules
                        min_characters_per_chunk=12,       # Minimum number of characters per chunk
                        return_type="chunks"               # Return type of the chunker; "chunks" or "texts"
                    )
                    
                    # Execute chunking
                    chunks = chunker(content)
                    logger.info(f"File {file_path} split into {len(chunks)} chunks")
                    
                    # Create Document objects for each chunk
                    documents = []
                    for i, chunk in enumerate(chunks):
                        # Copy metadata and add chunk information
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            "chunk_id": i + 1,
                        })
                        
                        # Create chunk document
                        chunk_doc = Document(
                            id=f"{str(file_path)}_{i+1}",
                            name=f"{file_path.stem}_chunk_{i+1}",
                            content=chunk.text,
                            meta_data=chunk_metadata
                        )
                        documents.append(chunk_doc)
                    
                    # Add CSV-specific metadata to each chunk
                    for doc in documents:
                        doc.meta_data.update(metadata)
                    
                    logger.info(f"Successfully read and chunked CSV file: {file_path}, total {len(documents)} chunks")
                    return documents
                    
                except Exception as chunk_error:
                    logger.error(f"Error during smart chunking: {str(chunk_error)}, returning full document")
                    # On chunking failure, create single Document object
                    document = Document(
                        id=str(file_path),
                        name=file_path.stem,
                        content=content,
                        meta_data=metadata
                    )
                    return [document]
                
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            # If CSV-specific handling fails, fallback to regular text processing
            return super().read_file(file_path, params)