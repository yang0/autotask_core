from typing import Any, Dict, List, Union,AsyncIterator, BinaryIO
from pathlib import Path
import json
import aiofiles


from autotask.knowledge.documentManager import DocumentLoader
from autotask.knowledge.documentManager import register_loader


@register_loader(['jsonl', 'json'])
class JSONLinesLoader(DocumentLoader):
    """JSONL文件加载器"""
    
    async def load(self, source: Union[str, Path, BinaryIO]) -> AsyncIterator[Dict[str, Any]]:
        """流式加载JSONL文件"""
        
        if isinstance(source, (str, Path)):
            async with aiofiles.open(source, 'r') as file:
                line_number = 0
                async for line in file:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield {
                                'content': data,
                                'metadata': {
                                    'source': str(source),
                                    'line': line_number,
                                    'type': 'jsonl'
                                }
                            }
                        except json.JSONDecodeError as e:
                            # 记录错误但继续处理
                            print(f"Error parsing line {line_number}: {e}")
                    line_number += 1
        else:
            for i, line in enumerate(source):
                if line.strip():
                    try:
                        data = json.loads(line)
                        yield {
                            'content': data,
                            'metadata': {
                                'line': i,
                                'type': 'jsonl'
                            }
                        }
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {i}: {e}")
    