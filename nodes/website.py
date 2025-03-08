try:
    from autotask.nodes import Node, register_node
    from autotask.document import Document
    from autotask.knowledge.website import WebsiteKnowledgeBase
    from autotask.document.reader.website_reader import WebsiteReader
    import json
except ImportError:
    # Mock for development environment
    from stub import Node, register_node
    
    class Document:
        def __init__(self, name="", content=""):
            self.name = name
            self.content = content
        
        def to_dict(self):
            return {"name": self.name, "content": self.content}
    
    class WebsiteKnowledgeBase:
        def __init__(self):
            self.urls = []
        
        def load(self, recreate=False):
            pass
        
        def search(self, query=""):
            return [Document(name=query, content=f"Mock content for {query}")]
    
    class WebsiteReader:
        def read(self, url=""):
            return [Document(name=url, content=f"Mock content from {url}")]

from typing import Dict, Any, List, Optional


@register_node
class WebsiteReaderNode(Node):
    """Node for reading content from a website URL"""
    NAME = "Website Reader"
    DESCRIPTION = "Reads content from a website URL and returns it as structured document data"
    CATEGORY = "Web"
    ICON = "globe"
    
    INPUTS = {
        "url": {
            "label": "Website URL",
            "description": "The URL of the website to read (must start with http:// or https://)",
            "type": "STRING",
            "required": True,
        },
        "max_depth": {
            "label": "Maximum Depth",
            "description": "Maximum depth of links to follow when crawling the website",
            "type": "INT",
            "default": 1,
            "required": False,
        },
        "timeout": {
            "label": "Timeout",
            "description": "Timeout in seconds for the HTTP request",
            "type": "INT",
            "default": 30,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "content": {
            "label": "Website Content",
            "description": "Text content extracted from the website",
            "type": "STRING",
        },
        "documents": {
            "label": "Documents",
            "description": "JSON representation of the documents extracted from the website",
            "type": "STRING",
        },
        "document_count": {
            "label": "Document Count",
            "description": "Number of documents extracted from the website",
            "type": "INT",
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
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs.get("url", "")
            max_depth = node_inputs.get("max_depth", 1)
            timeout = node_inputs.get("timeout", 30)
            
            if not url:
                workflow_logger.error("No URL provided")
                return {
                    "success": "false",
                    "error_message": "No URL provided",
                    "content": "",
                    "documents": "[]",
                    "document_count": 0
                }
            
            # Validate URL format
            if not (url.startswith("http://") or url.startswith("https://")):
                error_msg = "URL must start with http:// or https://"
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "error_message": error_msg,
                    "content": "",
                    "documents": "[]",
                    "document_count": 0
                }
            
            workflow_logger.info(f"Reading website: {url}")
            
            # Create a WebsiteReader instance and read the URL
            reader = WebsiteReader()
            
            try:
                # For this mock implementation, we're ignoring max_depth and timeout
                # In a real implementation, these would be passed as parameters
                documents = reader.read(url=url)
                
                # Extract content from documents
                all_content = ""
                doc_dicts = []
                
                for doc in documents:
                    doc_dict = doc.to_dict()
                    doc_dicts.append(doc_dict)
                    if 'content' in doc_dict:
                        all_content += doc_dict['content'] + "\n\n"
                
                workflow_logger.info(f"Successfully read {len(documents)} documents from {url}")
                
                return {
                    "success": "true",
                    "content": all_content.strip(),
                    "documents": json.dumps(doc_dicts, indent=2),
                    "document_count": len(documents),
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error reading website: {str(e)}"
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "error_message": error_msg,
                    "content": "",
                    "documents": "[]",
                    "document_count": 0
                }
            
        except Exception as e:
            error_msg = f"Error processing website: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "content": "",
                "documents": "[]",
                "document_count": 0
            }


@register_node
class WebsiteKnowledgeBaseNode(Node):
    """Node for adding website content to a knowledge base and searching for information"""
    NAME = "Website Knowledge Base"
    DESCRIPTION = "Adds website content to a knowledge base and allows searching for information"
    CATEGORY = "Web"
    ICON = "database"
    
    INPUTS = {
        "action": {
            "label": "Action",
            "description": "Action to perform: 'add' to add a website, 'search' to search the knowledge base",
            "type": "STRING",
            "options": ["add", "search"],
            "default": "add",
            "required": True,
        },
        "url": {
            "label": "Website URL",
            "description": "The URL of the website to add (required for 'add' action)",
            "type": "STRING",
            "required": False,
        },
        "query": {
            "label": "Search Query",
            "description": "The query to search for in the knowledge base (required for 'search' action)",
            "type": "STRING",
            "required": False,
        },
        "recreate_kb": {
            "label": "Recreate Knowledge Base",
            "description": "Whether to recreate the knowledge base from scratch",
            "type": "STRING",
            "default": "false",
            "required": False,
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "Maximum number of results to return from search",
            "type": "INT",
            "default": 5,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Operation Result",
            "description": "Result of the operation (success message or search results)",
            "type": "STRING",
        },
        "kb_urls": {
            "label": "Knowledge Base URLs",
            "description": "List of URLs currently in the knowledge base",
            "type": "STRING",
        },
        "documents": {
            "label": "Documents",
            "description": "JSON representation of the documents found in search",
            "type": "STRING",
        },
        "document_count": {
            "label": "Document Count",
            "description": "Number of documents found in search",
            "type": "INT",
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
        self.knowledge_base = WebsiteKnowledgeBase()
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            action = node_inputs.get("action", "add")
            url = node_inputs.get("url", "")
            query = node_inputs.get("query", "")
            recreate_kb_str = node_inputs.get("recreate_kb", "false")
            max_results = node_inputs.get("max_results", 5)
            
            # Convert string input to boolean
            recreate_kb = recreate_kb_str.lower() == "true"
            
            # Validate action
            if action not in ["add", "search"]:
                error_msg = f"Invalid action: {action}. Must be 'add' or 'search'."
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "error_message": error_msg,
                    "result": "",
                    "kb_urls": json.dumps(self.knowledge_base.urls),
                    "documents": "[]",
                    "document_count": 0
                }
            
            # Perform the requested action
            if action == "add":
                # Add a website to the knowledge base
                if not url:
                    error_msg = "URL is required for 'add' action"
                    workflow_logger.error(error_msg)
                    return {
                        "success": "false",
                        "error_message": error_msg,
                        "result": "",
                        "kb_urls": json.dumps(self.knowledge_base.urls),
                        "documents": "[]",
                        "document_count": 0
                    }
                
                # Validate URL format
                if not (url.startswith("http://") or url.startswith("https://")):
                    error_msg = "URL must start with http:// or https://"
                    workflow_logger.error(error_msg)
                    return {
                        "success": "false",
                        "error_message": error_msg,
                        "result": "",
                        "kb_urls": json.dumps(self.knowledge_base.urls),
                        "documents": "[]",
                        "document_count": 0
                    }
                
                workflow_logger.info(f"Adding to knowledge base: {url}")
                
                # Add the URL to the knowledge base
                self.knowledge_base.urls.append(url)
                
                # Load or recreate the knowledge base
                workflow_logger.info(f"Loading knowledge base (recreate={recreate_kb})")
                self.knowledge_base.load(recreate=recreate_kb)
                
                return {
                    "success": "true",
                    "result": "Website successfully added to knowledge base",
                    "kb_urls": json.dumps(self.knowledge_base.urls),
                    "documents": "[]",
                    "document_count": 0,
                    "error_message": ""
                }
                
            else:  # action == "search"
                # Search the knowledge base
                if not query:
                    error_msg = "Query is required for 'search' action"
                    workflow_logger.error(error_msg)
                    return {
                        "success": "false",
                        "error_message": error_msg,
                        "result": "",
                        "kb_urls": json.dumps(self.knowledge_base.urls),
                        "documents": "[]",
                        "document_count": 0
                    }
                
                workflow_logger.info(f"Searching knowledge base for: {query}")
                
                # Search the knowledge base
                relevant_docs = self.knowledge_base.search(query=query)
                
                # Limit results if needed
                if max_results > 0 and len(relevant_docs) > max_results:
                    relevant_docs = relevant_docs[:max_results]
                
                # Convert documents to dictionary format
                doc_dicts = [doc.to_dict() for doc in relevant_docs]
                
                workflow_logger.info(f"Found {len(doc_dicts)} relevant documents")
                
                return {
                    "success": "true",
                    "result": f"Found {len(doc_dicts)} documents",
                    "kb_urls": json.dumps(self.knowledge_base.urls),
                    "documents": json.dumps(doc_dicts, indent=2),
                    "document_count": len(doc_dicts),
                    "error_message": ""
                }
            
        except Exception as e:
            error_msg = f"Error with website knowledge base: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "result": "",
                "kb_urls": json.dumps(self.knowledge_base.urls if hasattr(self, "knowledge_base") else []),
                "documents": "[]",
                "document_count": 0
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test WebsiteReaderNode
    print("\nTesting WebsiteReaderNode:")
    node1 = WebsiteReaderNode()
    result = asyncio.run(node1.execute({"url": "https://example.com"}, logger))
    print(f"Success: {result['success']}")
    print(f"Document count: {result['document_count']}")
    content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
    print(f"Content preview: {content_preview}")
    
    # Test WebsiteKnowledgeBaseNode (add action)
    print("\nTesting WebsiteKnowledgeBaseNode (add action):")
    node2 = WebsiteKnowledgeBaseNode()
    result = asyncio.run(node2.execute({"action": "add", "url": "https://example.com"}, logger))
    print(f"Success: {result['success']}")
    print(f"Result: {result['result']}")
    print(f"KB URLs: {result['kb_urls']}")
    
    # Test WebsiteKnowledgeBaseNode (search action)
    print("\nTesting WebsiteKnowledgeBaseNode (search action):")
    result = asyncio.run(node2.execute({"action": "search", "query": "example"}, logger))
    print(f"Success: {result['success']}")
    print(f"Result: {result['result']}")
    print(f"Document count: {result['document_count']}") 