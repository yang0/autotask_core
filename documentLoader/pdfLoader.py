from typing import Any, Dict, List, Union,AsyncIterator, BinaryIO
from pathlib import Path
import pypdf

try:
    from autotask.knowledge.documentManager import register_loader
    from autotask.knowledge.documentManager import DocumentLoader
except ImportError:
    from ..stub import register_loader, DocumentLoader

@register_loader(['pdf'])
class PDFLoader(DocumentLoader):
    """PDF文档加载器"""
    
    async def load(self, source: Union[str, Path, BinaryIO]) -> AsyncIterator[Dict[str, Any]]:
        """流式加载PDF文档"""
        
        async def process_pdf(pdf_reader):
            for i, page in enumerate(pdf_reader.pages):
                yield {
                    'content': page.extract_text(),
                    'metadata': {
                        'source': str(source) if isinstance(source, (str, Path)) else None,
                        'page': i + 1,
                        'type': 'pdf'
                    }
                }
        
        if isinstance(source, (str, Path)):
            with open(source, 'rb') as file:
                pdf = pypdf.PdfReader(file)
                async for doc in process_pdf(pdf):
                    yield doc
        else:  # BinaryIO
            pdf = pypdf.PdfReader(source)
            async for doc in process_pdf(pdf):
                yield doc
    