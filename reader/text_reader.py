from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import os
import uuid

from autotask.document.base import Document
from autotask.document.reader.file_reader import FileReader
from autotask.document.reader.reader_registry import ReaderRegistry
from autotask.utils.log import logger

# 导入 RecursiveChunker
try:
    from chonkie import RecursiveChunker, RecursiveRules
    CHONKIE_AVAILABLE = True
except ImportError:
    logger.warning("Chonkie 库未安装，智能分块功能不可用。请使用 pip install chonkie 安装")
    CHONKIE_AVAILABLE = False


@ReaderRegistry.register_reader([".txt", ".md", ".csv", ".json", ".xml", ".html", ".log"])
class TextReader(FileReader):
    """
    通用文本文件读取器
    
    支持多种文本文件格式，如 .txt, .md, .csv, .json, .xml, .html, .log 等
    默认使用 RecursiveChunker 对文本进行智能分块
    """
    
    # 支持的文件格式列表
    FILE_FORMATS = [".txt", ".md", ".csv", ".json", ".xml", ".html", ".log"]
    
    # 额外参数定义
    PARAMS = {
        "encoding": {
            "label": "文件编码",
            "description": "读取文件的编码格式",
            "type": "STRING",
            "default": "utf-8"
        },
        "skip_empty_lines": {
            "label": "跳过空行",
            "description": "是否跳过空行",
            "type": "BOOLEAN",
            "default": True
        },
        "max_length": {
            "label": "最大长度",
            "description": "读取文件的最大字符数，0表示不限制",
            "type": "INTEGER",
            "default": 0
        },
        "extract_metadata": {
            "label": "提取元数据",
            "description": "是否从文件中提取元数据信息",
            "type": "BOOLEAN",
            "default": True
        },
        "chunk_size": {
            "label": "分块大小",
            "description": "每个分块的最大token数量",
            "type": "INTEGER",
            "default": 1024
        }
    }
    
    def read_file(self, file_path: Path, params: Dict[str, Any]) -> List[Document]:
        """
        读取文本文件并返回Document列表
        
        默认使用 RecursiveChunker 对文本进行智能分块
        
        Args:
            file_path: 文件路径
            params: 参数字典
            
        Returns:
            List[Document]: 包含文本内容的文档列表
            
        Raises:
            UnicodeDecodeError: 编码错误
            IOError: 文件读取错误
        """
        # 从参数获取配置
        encoding = params.get("encoding", "utf-8")
        skip_empty_lines = params.get("skip_empty_lines", True)
        max_length = params.get("max_length", 0)
        extract_metadata = params.get("extract_metadata", True)
        chunk_size = params.get("chunk_size", 1024)
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            # 限制最大长度
            if max_length > 0 and len(content) > max_length:
                content = content[:max_length]
                logger.warning(f"文件 {file_path} 内容被截断至 {max_length} 字符")
                
            # 处理空行
            if skip_empty_lines:
                content = "\n".join(line for line in content.split("\n") if line.strip())
            
            # 提取元数据
            metadata = {}
            if extract_metadata:
                metadata = {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "extension": file_path.suffix,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                }
            
            # 检查内容长度，对小文本不做分块处理
            if len(content) < 1000 or not CHONKIE_AVAILABLE:
                # 对于短内容，直接创建单个Document对象
                document = Document(
                    id=str(file_path),
                    name=file_path.stem,
                    content=content,
                    meta_data=metadata
                )
                return [document]
            
            # 对于长内容，进行智能分块处理
            try:
                logger.info(f"对文件 {file_path} 进行智能分块")
                
                # 创建分块器
                chunker = RecursiveChunker(
                    tokenizer_or_token_counter="gpt2",  # Initialize with the gpt2 tokenizer
                    chunk_size=chunk_size,                     # Maximum tokens per chunk
                    rules=RecursiveRules(),             # Default rules
                    min_characters_per_chunk=12,        # Minimum number of characters per chunk
                    return_type="chunks"                # Return type of the chunker; "chunks" or "texts"
                )
                
                # 执行分块
                chunks = chunker(content)
                logger.info(f"文件 {file_path} 被分成 {len(chunks)} 个块")
                
                # 为每个块创建Document对象
                documents = []
                for i, chunk in enumerate(chunks):
                    # 复制元数据并添加分块信息
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_id": i + 1,
                    })
                    
                    # 创建分块文档
                    chunk_doc = Document(
                        id=f"{str(file_path)}_{i+1}",
                        name=f"{file_path.stem}_chunk_{i+1}",
                        content=chunk.text,
                        meta_data=chunk_metadata
                    )
                    documents.append(chunk_doc)
                
                return documents
                
            except Exception as chunk_error:
                logger.error(f"智能分块过程中出错：{str(chunk_error)}，将返回完整文档")
                # 分块失败时，创建单个Document对象
                document = Document(
                    id=str(file_path),
                    name=file_path.stem,
                    content=content,
                    meta_data=metadata
                )
                return [document]
            
        except UnicodeDecodeError as e:
            logger.error(f"读取 {file_path} 时编码错误: {str(e)}")
            # 尝试使用替代编码
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                logger.warning(f"对 {file_path} 回退到 latin-1 编码")
                
                document = Document(
                    id=str(file_path),
                    name=file_path.stem,
                    content=content,
                    meta_data={"source": str(file_path), "encoding_fallback": True}
                )
                return [document]
            except Exception as e2:
                logger.error(f"使用回退编码读取文件失败: {str(e2)}")
                raise
                
        except Exception as e:
            logger.error(f"读取文本文件 {file_path} 时出错: {str(e)}")
            raise


# 可以添加更多特定类型的文本读取器，如CSV特定处理
@ReaderRegistry.register_reader([".csv"])
class CSVReader(TextReader):
    """CSV文件特定读取器，处理CSV特有的格式需求"""
    
    FILE_FORMATS = [".csv"]
    
    PARAMS = {
        "encoding": {
            "label": "文件编码",
            "description": "读取文件的编码格式",
            "type": "STRING", 
            "default": "utf-8"
        },
        "delimiter": {
            "label": "分隔符",
            "description": "CSV字段分隔符",
            "type": "STRING",
            "default": ","
        },
        "has_header": {
            "label": "包含表头",
            "description": "CSV文件是否包含表头行",
            "type": "BOOLEAN",
            "default": True
        },
        "chunk_size": {
            "label": "分块大小",
            "description": "每个分块的最大token数量",
            "type": "INTEGER",
            "default": 1024
        }
    }
    
    def read_file(self, file_path: Path, params: Dict[str, Any]) -> List[Document]:
        """读取CSV文件并进行专门处理"""
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
                
                # 将CSV数据转换为格式化文本
                if has_header and header:
                    content = delimiter.join(header) + "\n"
                    content += "\n".join(delimiter.join(row) for row in data_rows)
                else:
                    content = "\n".join(delimiter.join(row) for row in data_rows)
                
                # 创建基本元数据
                metadata = {
                    "source": str(file_path),
                    "file_type": "csv",
                    "row_count": len(data_rows),
                    "column_count": len(header) if header else (len(data_rows[0]) if data_rows else 0)
                }
                                
                # 对于长内容，进行智能分块处理
                try:
                    logger.info(f"对文件 {file_path} 进行智能分块")
                    
                    # 创建分块器
                    chunker = RecursiveChunker(
                        tokenizer_or_token_counter="gpt2",  # Initialize with the gpt2 tokenizer
                        chunk_size=chunk_size,                     # Maximum tokens per chunk
                        rules=RecursiveRules(),             # Default rules
                        min_characters_per_chunk=12,        # Minimum number of characters per chunk
                        return_type="chunks"                # Return type of the chunker; "chunks" or "texts"
                    )
                    
                    # 执行分块
                    chunks = chunker(content)
                    logger.info(f"文件 {file_path} 被分成 {len(chunks)} 个块")
                    
                    # 为每个块创建Document对象
                    documents = []
                    for i, chunk in enumerate(chunks):
                        # 复制元数据并添加分块信息
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            "chunk_id": i + 1,
                        })
                        
                        # 创建分块文档
                        chunk_doc = Document(
                            id=f"{str(file_path)}_{i+1}",
                            name=f"{file_path.stem}_chunk_{i+1}",
                            content=chunk.text,
                            meta_data=chunk_metadata
                        )
                        documents.append(chunk_doc)
                    
                    # 为每个分块添加CSV特定元数据
                    for doc in documents:
                        doc.meta_data.update(metadata)
                    
                    logger.info(f"成功读取并分块CSV文件: {file_path}，共 {len(documents)} 个块")
                    return documents
                    
                except Exception as chunk_error:
                    logger.error(f"智能分块过程中出错：{str(chunk_error)}，将返回完整文档")
                    # 分块失败时，创建单个Document对象
                    document = Document(
                        id=str(file_path),
                        name=file_path.stem,
                        content=content,
                        meta_data=metadata
                    )
                    return [document]
                
        except Exception as e:
            logger.error(f"读取CSV文件 {file_path} 时出错: {str(e)}")
            # 如果CSV特定处理失败，回退到普通文本处理
            return super().read_file(file_path, params)