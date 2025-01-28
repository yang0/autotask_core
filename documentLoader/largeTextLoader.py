from typing import Any, Dict, List, Union,AsyncIterator, BinaryIO
from pathlib import Path
import aiofiles

from autotask.knowledge.documentManager import register_loader
from autotask.knowledge.documentManager import DocumentLoader


@register_loader(['txt', 'md', 'csv', 'log', 'json', 'xml', 'html', 'markdown', 'rst', 'text', 'jsonl',  "yaml", "yml", "toml", "conf", "cfg", "config", "properties", "prop", "settings", "ini"])
class LargeTextLoader(DocumentLoader):
    """大文本文件加载器"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    async def load(self, source: Union[str, Path, BinaryIO]) -> AsyncIterator[Dict[str, Any]]:
        """流式加载大文本文件"""
        
        async def read_in_chunks(file_obj):
            chunk_number = 0
            while True:
                chunk = await file_obj.read(self.chunk_size)
                if not chunk:
                    break
                    
                yield {
                    'content': chunk,
                    'metadata': {
                        'source': str(source) if isinstance(source, (str, Path)) else None,
                        'chunk': chunk_number,
                        'type': 'text'
                    }
                }
                chunk_number += 1
        
        if isinstance(source, (str, Path)):
            async with aiofiles.open(source, 'r') as file:
                async for doc in read_in_chunks(file):
                    yield doc
        else:
            # 对于二进制流，需要适当处理
            content = source.read().decode('utf-8')
            for i in range(0, len(content), self.chunk_size):
                chunk = content[i:i + self.chunk_size]
                yield {
                    'content': chunk,
                    'metadata': {
                        'chunk': i // self.chunk_size,
                        'type': 'text'
                    }
                }