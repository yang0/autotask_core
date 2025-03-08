try:
    from autotask.nodes import Node, GeneratorNode, register_node
    import arxiv
    from pypdf import PdfReader
except ImportError:
    # Mock for development environment
    from stub import Node, GeneratorNode, register_node
    class arxiv:
        class Client:
            def results(self, search):
                return []
        class Search:
            def __init__(self, query=None, max_results=None, sort_by=None, sort_order=None, id_list=None):
                pass
        class SortCriterion:
            Relevance = "relevance"
        class SortOrder:
            Descending = "descending"

import json
import asyncio
from typing import Dict, Any, Generator, List, Optional
from pathlib import Path


@register_node
class ArxivSearchNode(Node):
    """Node for searching arXiv for academic papers"""
    NAME = "arXiv Search"
    DESCRIPTION = "Searches arXiv for academic papers based on a query"
    CATEGORY = "Research"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The query to search arXiv for",
            "type": "STRING",
            "required": True,
        },
        "num_articles": {
            "label": "Number of Articles",
            "description": "The maximum number of articles to return",
            "type": "INT",
            "default": 10,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "articles": {
            "label": "Articles",
            "description": "JSON representation of articles found on arXiv",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the search operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if search failed",
            "type": "STRING",
        }
    }
    
    def __init__(self):
        super().__init__()
        self.client = arxiv.Client()
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            query = node_inputs.get("query")
            num_articles = node_inputs.get("num_articles", 10)
            
            if not query:
                workflow_logger.error("No search query provided")
                return {
                    "success": "false",
                    "error_message": "No search query provided",
                    "articles": "[]"
                }
            
            workflow_logger.info(f"Searching arXiv for: {query}")
            
            # Use arxiv library to search
            articles = []
            for result in self.client.results(
                search=arxiv.Search(
                    query=query,
                    max_results=num_articles,
                    sort_by=arxiv.SortCriterion.Relevance,
                    sort_order=arxiv.SortOrder.Descending,
                )
            ):
                try:
                    article = {
                        "title": result.title,
                        "id": result.get_short_id(),
                        "entry_id": result.entry_id,
                        "authors": [author.name for author in result.authors],
                        "primary_category": result.primary_category,
                        "categories": result.categories,
                        "published": result.published.isoformat() if result.published else None,
                        "pdf_url": result.pdf_url,
                        "links": [link.href for link in result.links],
                        "summary": result.summary,
                        "comment": result.comment,
                    }
                    articles.append(article)
                except Exception as e:
                    workflow_logger.error(f"Error processing article: {e}")
            
            workflow_logger.info(f"Found {len(articles)} articles for query: {query}")
            
            return {
                "success": "true",
                "articles": json.dumps(articles, indent=4),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"arXiv search failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "articles": "[]"
            }


@register_node
class ArxivReaderNode(Node):
    """Node for reading arXiv papers based on their IDs"""
    NAME = "arXiv Paper Reader"
    DESCRIPTION = "Downloads and reads content from arXiv papers based on their IDs"
    CATEGORY = "Research"
    ICON = "book"
    
    INPUTS = {
        "paper_ids": {
            "label": "Paper IDs",
            "description": "List of arXiv paper IDs (comma-separated)",
            "type": "STRING",
            "required": True,
        },
        "pages_to_read": {
            "label": "Pages to Read",
            "description": "Number of pages to read from each paper (0 for all pages)",
            "type": "INT",
            "default": 0,
            "required": False,
        },
        "download_dir": {
            "label": "Download Directory",
            "description": "Directory to download papers to (leave empty for default)",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "papers": {
            "label": "Papers",
            "description": "JSON representation of papers with their content",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed",
            "type": "STRING",
        }
    }
    
    def __init__(self):
        super().__init__()
        self.client = arxiv.Client()
        # Default download directory
        self.download_dir = Path(__file__).parent.parent.joinpath("data/arxiv_pdfs")
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            paper_ids_input = node_inputs.get("paper_ids", "")
            pages_to_read = node_inputs.get("pages_to_read", 0)
            download_dir = node_inputs.get("download_dir", "")
            
            # Parse paper IDs
            if isinstance(paper_ids_input, str):
                paper_ids = [id.strip() for id in paper_ids_input.split(",") if id.strip()]
            elif isinstance(paper_ids_input, list):
                paper_ids = [id for id in paper_ids_input if id]
            else:
                paper_ids = []
            
            if not paper_ids:
                workflow_logger.error("No valid paper IDs provided")
                return {
                    "success": "false",
                    "error_message": "No valid paper IDs provided",
                    "papers": "[]"
                }
            
            # Set download directory
            if download_dir:
                self.download_dir = Path(download_dir)
            self.download_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_logger.info(f"Reading {len(paper_ids)} arXiv papers")
            
            # Download and read papers
            articles = []
            for result in self.client.results(search=arxiv.Search(id_list=paper_ids)):
                try:
                    article = {
                        "title": result.title,
                        "id": result.get_short_id(),
                        "entry_id": result.entry_id,
                        "authors": [author.name for author in result.authors],
                        "primary_category": result.primary_category,
                        "categories": result.categories,
                        "published": result.published.isoformat() if result.published else None,
                        "pdf_url": result.pdf_url,
                        "links": [link.href for link in result.links],
                        "summary": result.summary,
                        "comment": result.comment,
                    }
                    
                    if result.pdf_url:
                        workflow_logger.info(f"Downloading paper: {result.pdf_url}")
                        pdf_path = result.download_pdf(dirpath=str(self.download_dir))
                        workflow_logger.info(f"Downloaded to: {pdf_path}")
                        
                        pdf_reader = PdfReader(pdf_path)
                        article["content"] = []
                        
                        # Read pages
                        total_pages = len(pdf_reader.pages)
                        pages_count = total_pages if pages_to_read <= 0 else min(pages_to_read, total_pages)
                        
                        for page_number in range(pages_count):
                            content = {
                                "page": page_number + 1,
                                "text": pdf_reader.pages[page_number].extract_text()
                            }
                            article["content"].append(content)
                        
                        workflow_logger.info(f"Read {pages_count} pages from paper: {result.get_short_id()}")
                    
                    articles.append(article)
                except Exception as e:
                    workflow_logger.error(f"Error processing paper {result.get_short_id()}: {e}")
            
            return {
                "success": "true",
                "papers": json.dumps(articles, indent=4),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"arXiv reader failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "papers": "[]"
            }


@register_node
class ArxivPaperGeneratorNode(GeneratorNode):
    """Generator node for processing multiple arXiv papers sequentially"""
    NAME = "arXiv Paper Generator"
    DESCRIPTION = "Processes multiple arXiv papers and yields each paper's content sequentially"
    CATEGORY = "Research"
    ICON = "book-open"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The query to search arXiv for (leave empty if using paper_ids)",
            "type": "STRING",
            "required": False,
        },
        "paper_ids": {
            "label": "Paper IDs",
            "description": "List of specific arXiv paper IDs (comma-separated)",
            "type": "STRING",
            "required": False,
        },
        "max_papers": {
            "label": "Maximum Papers",
            "description": "Maximum number of papers to process",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "pages_per_paper": {
            "label": "Pages Per Paper",
            "description": "Number of pages to read from each paper (0 for all pages)",
            "type": "INT",
            "default": 0,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "title": {
            "label": "Paper Title",
            "description": "Title of the current paper",
            "type": "STRING",
        },
        "id": {
            "label": "Paper ID",
            "description": "arXiv ID of the current paper",
            "type": "STRING",
        },
        "authors": {
            "label": "Authors",
            "description": "List of authors of the current paper",
            "type": "STRING",
        },
        "content": {
            "label": "Paper Content",
            "description": "Extracted content from the current paper",
            "type": "STRING",
        },
        "summary": {
            "label": "Summary",
            "description": "Summary of the current paper",
            "type": "STRING",
        },
        "page_count": {
            "label": "Page Count",
            "description": "Number of pages in the current paper",
            "type": "INT",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether processing this paper was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if processing failed",
            "type": "STRING",
        }
    }
    
    def __init__(self):
        super().__init__()
        self.client = arxiv.Client()
        self.download_dir = Path(__file__).parent.parent.joinpath("data/arxiv_pdfs")
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Generator:
        try:
            query = node_inputs.get("query", "")
            paper_ids_input = node_inputs.get("paper_ids", "")
            max_papers = node_inputs.get("max_papers", 5)
            pages_per_paper = node_inputs.get("pages_per_paper", 0)
            
            # Process paper IDs if provided
            paper_ids = []
            if paper_ids_input:
                if isinstance(paper_ids_input, str):
                    paper_ids = [id.strip() for id in paper_ids_input.split(",") if id.strip()]
                elif isinstance(paper_ids_input, list):
                    paper_ids = [id for id in paper_ids_input if id]
            
            # Create search object
            if paper_ids:
                workflow_logger.info(f"Searching for {len(paper_ids)} specific papers")
                search = arxiv.Search(id_list=paper_ids)
            elif query:
                workflow_logger.info(f"Searching papers with query: {query}")
                search = arxiv.Search(
                    query=query,
                    max_results=max_papers,
                    sort_by=arxiv.SortCriterion.Relevance,
                    sort_order=arxiv.SortOrder.Descending
                )
            else:
                workflow_logger.error("Neither query nor paper IDs provided")
                yield {
                    "title": "",
                    "id": "",
                    "authors": "",
                    "content": "",
                    "summary": "",
                    "page_count": 0,
                    "success": "false",
                    "error_message": "Neither query nor paper IDs provided"
                }
                return
            
            # Get results and process each paper
            count = 0
            for result in self.client.results(search):
                if count >= max_papers:
                    break
                    
                try:
                    paper_id = result.get_short_id()
                    workflow_logger.info(f"Processing paper {count+1}/{max_papers}: {paper_id}")
                    
                    # Extract basic information
                    authors_str = ", ".join([author.name for author in result.authors])
                    
                    # Initialize output
                    output = {
                        "title": result.title,
                        "id": paper_id,
                        "authors": authors_str,
                        "summary": result.summary,
                        "content": "",
                        "page_count": 0,
                        "success": "true",
                        "error_message": ""
                    }
                    
                    # Download and read the PDF if available
                    if result.pdf_url:
                        try:
                            workflow_logger.info(f"Downloading paper: {paper_id}")
                            pdf_path = result.download_pdf(dirpath=str(self.download_dir))
                            
                            # Read PDF content
                            pdf_reader = PdfReader(pdf_path)
                            content_text = []
                            
                            # Determine how many pages to read
                            total_pages = len(pdf_reader.pages)
                            pages_count = total_pages if pages_per_paper <= 0 else min(pages_per_paper, total_pages)
                            
                            for page_number in range(pages_count):
                                page_text = pdf_reader.pages[page_number].extract_text()
                                content_text.append(f"--- Page {page_number + 1} ---\n{page_text}")
                            
                            output["content"] = "\n\n".join(content_text)
                            output["page_count"] = total_pages
                            
                            workflow_logger.info(f"Read {pages_count} pages from paper: {paper_id}")
                            
                        except Exception as e:
                            pdf_error = f"Error reading PDF for {paper_id}: {str(e)}"
                            workflow_logger.error(pdf_error)
                            output["error_message"] = pdf_error
                    else:
                        output["error_message"] = "No PDF available for this paper"
                        
                    yield output
                    count += 1
                    
                except Exception as e:
                    error_msg = f"Error processing paper: {str(e)}"
                    workflow_logger.error(error_msg)
                    
                    yield {
                        "title": result.title if hasattr(result, 'title') else "Unknown",
                        "id": result.get_short_id() if hasattr(result, 'get_short_id') else "Unknown",
                        "authors": ", ".join([author.name for author in result.authors]) if hasattr(result, 'authors') else "",
                        "content": "",
                        "summary": result.summary if hasattr(result, 'summary') else "",
                        "page_count": 0,
                        "success": "false",
                        "error_message": error_msg
                    }
                    count += 1
            
        except Exception as e:
            error_msg = f"arXiv generator failed: {str(e)}"
            workflow_logger.error(error_msg)
            
            yield {
                "title": "",
                "id": "",
                "authors": "",
                "content": "",
                "summary": "",
                "page_count": 0,
                "success": "false",
                "error_message": error_msg
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test ArxivSearchNode
    print("\nTesting ArxivSearchNode:")
    node1 = ArxivSearchNode()
    result = asyncio.run(node1.execute({"query": "machine learning", "num_articles": 2}, logger))
    print(f"Search results found: {len(json.loads(result['articles']))}")
    
    # Test ArxivReaderNode
    print("\nTesting ArxivReaderNode:")
    node2 = ArxivReaderNode()
    result = asyncio.run(node2.execute({"paper_ids": "1706.03762", "pages_to_read": 1}, logger))
    if result['success'] == "true":
        print(f"Successfully read paper content")
    else:
        print(f"Failed to read paper: {result['error_message']}") 