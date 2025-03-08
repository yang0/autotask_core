try:
    from autotask.nodes import Node, register_node
    from autotask.document import Document
    from autotask.knowledge.wikipedia import WikipediaKnowledgeBase
    import wikipedia
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
    
    class WikipediaKnowledgeBase:
        def __init__(self):
            self.topics = []
        
        def load(self, recreate=False):
            pass
        
        def search(self, query=""):
            return [Document(name=query, content=f"Mock content for {query}")]
    
    # Mock wikipedia module
    class wikipedia:
        @staticmethod
        def summary(query, sentences=0, chars=0, auto_suggest=True, redirect=True):
            return f"Mock Wikipedia summary for {query}"
        
        @staticmethod
        def search(query, results=10, suggestion=False):
            return [f"{query} result {i}" for i in range(1, results + 1)]
        
        @staticmethod
        def page(title):
            class MockPage:
                def __init__(self, title):
                    self.title = title
                    self.content = f"Mock content for {title}"
                    self.summary = f"Mock summary for {title}"
                    self.url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            
            return MockPage(title)

from typing import Dict, Any, List, Optional


@register_node
class WikipediaSearchNode(Node):
    """Node for searching Wikipedia and retrieving article summaries"""
    NAME = "Wikipedia Search"
    DESCRIPTION = "Searches Wikipedia for a query and returns article summaries"
    CATEGORY = "Research"
    ICON = "wikipedia-w"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The topic to search for on Wikipedia",
            "type": "STRING",
            "required": True,
        },
        "sentences": {
            "label": "Number of Sentences",
            "description": "Maximum number of sentences to include in the summary (0 for default)",
            "type": "INT",
            "default": 0,
            "required": False,
        },
        "full_article": {
            "label": "Full Article",
            "description": "Whether to retrieve the full article content or just the summary",
            "type": "STRING",
            "default": "false",
            "required": False,
        },
        "related_topics": {
            "label": "Get Related Topics",
            "description": "Whether to retrieve related search topics",
            "type": "STRING",
            "default": "false",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "summary": {
            "label": "Article Summary",
            "description": "Summary content of the Wikipedia article",
            "type": "STRING",
        },
        "title": {
            "label": "Article Title",
            "description": "Title of the Wikipedia article",
            "type": "STRING",
        },
        "url": {
            "label": "Article URL",
            "description": "URL to the full Wikipedia article",
            "type": "STRING",
        },
        "full_content": {
            "label": "Full Content",
            "description": "Full content of the Wikipedia article (if requested)",
            "type": "STRING",
        },
        "related_topics": {
            "label": "Related Topics",
            "description": "List of related topics found in Wikipedia search",
            "type": "STRING",
        },
        "article_json": {
            "label": "Article JSON",
            "description": "JSON representation of the article data",
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
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            query = node_inputs.get("query", "")
            sentences = node_inputs.get("sentences", 0)
            full_article_str = node_inputs.get("full_article", "false")
            related_topics_str = node_inputs.get("related_topics", "false")
            
            # Convert string inputs to booleans
            full_article = full_article_str.lower() == "true"
            get_related_topics = related_topics_str.lower() == "true"
            
            if not query:
                workflow_logger.error("No search query provided")
                return {
                    "success": "false",
                    "error_message": "No search query provided",
                    "summary": "",
                    "title": "",
                    "url": "",
                    "full_content": "",
                    "related_topics": "[]",
                    "article_json": "{}"
                }
            
            workflow_logger.info(f"Searching Wikipedia for: {query}")
            
            # Get related topics if requested
            related_topics_list = []
            if get_related_topics:
                try:
                    related_topics_list = wikipedia.search(query)
                    workflow_logger.info(f"Found {len(related_topics_list)} related topics")
                except Exception as e:
                    workflow_logger.warning(f"Error getting related topics: {str(e)}")
            
            try:
                # Get article summary
                if sentences > 0:
                    summary_text = wikipedia.summary(query, sentences=sentences)
                else:
                    summary_text = wikipedia.summary(query)
                
                # Get full page data if requested
                title = query
                url = ""
                full_content = ""
                
                if full_article:
                    try:
                        page = wikipedia.page(query)
                        title = page.title
                        url = page.url
                        full_content = page.content
                        workflow_logger.info(f"Retrieved full article: {title}")
                    except Exception as e:
                        workflow_logger.warning(f"Error retrieving full article: {str(e)}")
                
                # Prepare article data for JSON output
                article_data = {
                    "title": title,
                    "summary": summary_text,
                    "url": url
                }
                
                if full_article:
                    article_data["full_content"] = full_content
                
                if get_related_topics:
                    article_data["related_topics"] = related_topics_list
                
                workflow_logger.info(f"Successfully retrieved Wikipedia content for: {query}")
                
                return {
                    "success": "true",
                    "summary": summary_text,
                    "title": title,
                    "url": url,
                    "full_content": full_content,
                    "related_topics": json.dumps(related_topics_list),
                    "article_json": json.dumps(article_data, indent=2),
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error retrieving Wikipedia content: {str(e)}"
                workflow_logger.error(error_msg)
                
                # If the main query fails, try to suggest alternatives
                suggestions = []
                try:
                    suggestions = wikipedia.search(query, results=5)
                    suggestions_msg = f"Did you mean: {', '.join(suggestions[:5])}?" if suggestions else ""
                except:
                    suggestions_msg = ""
                
                return {
                    "success": "false",
                    "error_message": f"{error_msg}\n{suggestions_msg}",
                    "summary": "",
                    "title": "",
                    "url": "",
                    "full_content": "",
                    "related_topics": json.dumps(suggestions),
                    "article_json": "{}"
                }
            
        except Exception as e:
            error_msg = f"Error searching Wikipedia: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "summary": "",
                "title": "",
                "url": "",
                "full_content": "",
                "related_topics": "[]",
                "article_json": "{}"
            }


@register_node
class WikipediaKnowledgeBaseNode(Node):
    """Node for interacting with a Wikipedia knowledge base"""
    NAME = "Wikipedia Knowledge Base"
    DESCRIPTION = "Searches Wikipedia and updates a knowledge base with the results"
    CATEGORY = "Research"
    ICON = "database"
    
    INPUTS = {
        "topic": {
            "label": "Search Topic",
            "description": "The topic to search for and add to the knowledge base",
            "type": "STRING",
            "required": True,
        },
        "recreate_knowledge_base": {
            "label": "Recreate Knowledge Base",
            "description": "Whether to recreate the knowledge base from scratch",
            "type": "STRING",
            "default": "false",
            "required": False,
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "Maximum number of documents to return from the knowledge base",
            "type": "INT",
            "default": 5,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "documents": {
            "label": "Documents",
            "description": "JSON representation of the relevant documents from the knowledge base",
            "type": "STRING",
        },
        "topic_count": {
            "label": "Topic Count",
            "description": "Number of topics in the knowledge base after the operation",
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
        self.knowledge_base = WikipediaKnowledgeBase()
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            topic = node_inputs.get("topic", "")
            recreate_kb_str = node_inputs.get("recreate_knowledge_base", "false")
            max_results = node_inputs.get("max_results", 5)
            
            # Convert string input to boolean
            recreate_kb = recreate_kb_str.lower() == "true"
            
            if not topic:
                workflow_logger.error("No topic provided")
                return {
                    "success": "false",
                    "error_message": "No topic provided",
                    "documents": "[]",
                    "topic_count": len(self.knowledge_base.topics)
                }
            
            workflow_logger.info(f"Adding to knowledge base: {topic}")
            
            # Add the topic to the knowledge base
            self.knowledge_base.topics.append(topic)
            
            # Load or recreate the knowledge base
            workflow_logger.info(f"Loading knowledge base (recreate={recreate_kb})")
            self.knowledge_base.load(recreate=recreate_kb)
            
            # Search the knowledge base for relevant documents
            workflow_logger.info(f"Searching knowledge base for: {topic}")
            relevant_docs = self.knowledge_base.search(query=topic)
            
            # Limit results if needed
            if max_results > 0 and len(relevant_docs) > max_results:
                relevant_docs = relevant_docs[:max_results]
            
            # Convert documents to dictionary format
            doc_dicts = [doc.to_dict() for doc in relevant_docs]
            
            workflow_logger.info(f"Found {len(doc_dicts)} relevant documents")
            
            return {
                "success": "true",
                "documents": json.dumps(doc_dicts, indent=2),
                "topic_count": len(self.knowledge_base.topics),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error with Wikipedia knowledge base: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "documents": "[]",
                "topic_count": len(self.knowledge_base.topics) if hasattr(self, "knowledge_base") else 0
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test WikipediaSearchNode
    print("\nTesting WikipediaSearchNode:")
    node1 = WikipediaSearchNode()
    result = asyncio.run(node1.execute({"query": "Python programming language"}, logger))
    print(f"Success: {result['success']}")
    print(f"Title: {result['title']}")
    summary_preview = result['summary'][:100] + "..." if len(result['summary']) > 100 else result['summary']
    print(f"Summary preview: {summary_preview}")
    
    # Test WikipediaKnowledgeBaseNode
    print("\nTesting WikipediaKnowledgeBaseNode:")
    node2 = WikipediaKnowledgeBaseNode()
    result = asyncio.run(node2.execute({"topic": "Python programming language"}, logger))
    print(f"Success: {result['success']}")
    print(f"Topic count: {result['topic_count']}")
    docs_preview = result['documents'][:100] + "..." if len(result['documents']) > 100 else result['documents']
    print(f"Documents preview: {docs_preview}") 