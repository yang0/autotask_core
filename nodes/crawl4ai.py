try:
    from autotask.nodes import Node, GeneratorNode, register_node
    from crawl4ai import AsyncWebCrawler, CacheMode
except ImportError:
    # Mock for development environment
    from stub import Node, GeneratorNode, register_node
    class AsyncWebCrawler:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def arun(self, url, cache_mode=None): 
            class MockResult:
                def __init__(self):
                    self.markdown = f"Crawled content from {url} (mock)"
            return MockResult()
    class CacheMode:
        BYPASS = "bypass"

import asyncio
from typing import Dict, Any, Generator, List, Optional




@register_node
class WebCrawlerNode(Node):
    """Node for crawling a single web page using crawl4ai library"""
    NAME = "Web Crawler"
    DESCRIPTION = "Crawls a website and extracts its content using crawl4ai"
    
    INPUTS = {
        "url": {
            "label": "URL",
            "description": "The URL of the website to crawl",
            "type": "STRING",
            "required": True,
        },
        "max_length": {
            "label": "Maximum Content Length",
            "description": "The maximum length of content to return (if empty, returns all content)",
            "type": "INT",
            "required": False,
        },
        "use_cache": {
            "label": "Use Cache",
            "description": "Whether to use cached results if available",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "content": {
            "label": "Crawled Content",
            "description": "The content extracted from the website",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the crawling operation was successful",
            "type": "BOOLEAN",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if crawling failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs.get("url")
            max_length = node_inputs.get("max_length")
            use_cache = node_inputs.get("use_cache", False)
            
            if not url:
                workflow_logger.error("No URL provided")
                return {
                    "success": False,
                    "error_message": "No URL provided",
                    "content": ""
                }
            
            workflow_logger.info(f"Starting web crawling for: {url}")
            
            # Determine cache mode
            cache_mode = CacheMode.BYPASS if not use_cache else None
            
            # Use AsyncWebCrawler directly
            async with AsyncWebCrawler(thread_safe=True) as crawler:
                result = await crawler.arun(url=url, cache_mode=cache_mode)
                
                if not result.markdown:
                    workflow_logger.warning(f"No content found for {url}")
                    return {
                        "success": True,
                        "content": "",
                        "error_message": "No content found"
                    }
                
                # Process the content
                content = result.markdown
                if max_length:
                    content = content[:max_length]
                
                workflow_logger.info(f"Successfully crawled {url}")
                
                return {
                    "success": True,
                    "content": content,
                    "error_message": ""
                }
            
        except Exception as e:
            error_msg = f"Web crawling failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
                "content": ""
            }


@register_node
class MultiWebCrawlerNode(GeneratorNode):
    """Generator node for crawling multiple web pages sequentially"""
    NAME = "Multi URL Crawler"
    DESCRIPTION = "Crawls multiple websites sequentially and yields their content one by one"
    
    INPUTS = {
        "urls": {
            "label": "URLs List",
            "description": "A list of URLs to crawl (comma-separated or as a list)",
            "type": "STRING",
            "required": True,
        },
        "max_length_per_url": {
            "label": "Maximum Content Length Per URL",
            "description": "The maximum length of content to return for each URL",
            "type": "INT",
            "required": False,
        },
        "use_cache": {
            "label": "Use Cache",
            "description": "Whether to use cached results if available",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "url": {
            "label": "Current URL",
            "description": "The URL being currently processed",
            "type": "STRING",
        },
        "content": {
            "label": "Crawled Content",
            "description": "The content extracted from the current website",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the crawling operation was successful",
            "type": "BOOLEAN",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if crawling failed",
            "type": "STRING",
        }
    }
    
    def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Generator:
        try:
            urls_input = node_inputs.get("urls", "")
            max_length = node_inputs.get("max_length_per_url")
            use_cache = node_inputs.get("use_cache", False)
            
            # Parse URLs (handle both comma-separated string or list)
            urls = []
            if isinstance(urls_input, str):
                urls = [url.strip() for url in urls_input.split(",") if url.strip()]
            elif isinstance(urls_input, list):
                urls = [url for url in urls_input if url]
            
            if not urls:
                workflow_logger.error("No valid URLs provided")
                yield {
                    "url": "",
                    "success": False,
                    "error_message": "No valid URLs provided",
                    "content": ""
                }
                return
            
            workflow_logger.info(f"Starting multi-URL crawling for {len(urls)} URLs")
            
            # Determine cache mode
            cache_mode = CacheMode.BYPASS if not use_cache else None
            
            # Process each URL
            for url in urls:
                workflow_logger.info(f"Crawling URL: {url}")
                try:
                    # Create a new event loop for async operation within sync context
                    content = asyncio.run(self._crawl_url(url, max_length, cache_mode))
                    workflow_logger.info(f"Successfully crawled {url}")
                    
                    yield {
                        "url": url,
                        "success": True,
                        "error_message": "",
                        "content": content
                    }
                    
                except Exception as e:
                    error_msg = f"Failed to crawl {url}: {str(e)}"
                    workflow_logger.error(error_msg)
                    
                    yield {
                        "url": url,
                        "success": False,
                        "error_message": error_msg,
                        "content": ""
                    }
            
        except Exception as e:
            error_msg = f"Multi-URL crawling process failed: {str(e)}"
            workflow_logger.error(error_msg)
            
            yield {
                "url": "",
                "success": False,
                "error_message": error_msg,
                "content": ""
            }
    
    async def _crawl_url(self, url: str, max_length: Optional[int], cache_mode) -> str:
        """Helper method to crawl a single URL asynchronously"""
        async with AsyncWebCrawler(thread_safe=True) as crawler:
            result = await crawler.arun(url=url, cache_mode=cache_mode)
            
            if not result.markdown:
                return ""
            
            # Process the content
            content = result.markdown
            if max_length:
                content = content[:max_length]
                
            return content


@register_node
class SearchEngineCrawlerNode(Node):
    """Node for searching and crawling search results"""
    NAME = "Search Engine Crawler"
    DESCRIPTION = "Performs a search query and crawls the top results"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The search query to perform",
            "type": "STRING",
            "required": True,
        },
        "num_results": {
            "label": "Number of Results",
            "description": "The maximum number of search results to crawl",
            "type": "INT",
            "default": 3,
            "required": False,
        },
        "max_length_per_result": {
            "label": "Maximum Content Length Per Result",
            "description": "The maximum length of content to return for each result",
            "type": "INT",
            "required": False,
        },
        "use_cache": {
            "label": "Use Cache",
            "description": "Whether to use cached results if available",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "results": {
            "label": "Search Results",
            "description": "A list of search results with their crawled content",
            "type": "LIST",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the search and crawling operation was successful",
            "type": "BOOLEAN",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if the operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            query = node_inputs.get("query")
            num_results = node_inputs.get("num_results", 3)
            max_length = node_inputs.get("max_length_per_result")
            use_cache = node_inputs.get("use_cache", False)
            
            if not query:
                workflow_logger.error("No search query provided")
                return {
                    "success": False,
                    "error_message": "No search query provided",
                    "results": []
                }
            
            workflow_logger.info(f"Starting search for query: {query}")
            
            # Construct search URL (this is a simple example, in a real implementation 
            # you might want to use a proper search API)
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            # Determine cache mode
            cache_mode = CacheMode.BYPASS if not use_cache else None
            
            # Use AsyncWebCrawler directly
            async with AsyncWebCrawler(thread_safe=True) as crawler:
                search_result = await crawler.arun(url=search_url, cache_mode=cache_mode)
                
                # In a real implementation, you would parse the search results 
                # and crawl each result URL
                search_content = ""
                if search_result.markdown:
                    search_content = search_result.markdown[:max_length] if max_length else search_result.markdown
                
                # Mock result for demonstration
                results = [{
                    "url": search_url,
                    "title": f"Search results for: {query}",
                    "content": search_content
                }]
                
                workflow_logger.info(f"Successfully performed search and crawling for query: {query}")
                
                return {
                    "success": True,
                    "results": results,
                    "error_message": ""
                }
            
        except Exception as e:
            error_msg = f"Search engine crawling failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
                "results": []
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test the WebCrawlerNode
    print("\nTesting WebCrawlerNode:")
    node1 = WebCrawlerNode()
    test_url = "https://example.com"
    result = asyncio.run(node1.execute({"url": test_url}, logger))
    print(f"Crawling result: {result['success']}")
    
    # Test the MultiWebCrawlerNode
    print("\nTesting MultiWebCrawlerNode:")
    node2 = MultiWebCrawlerNode()
    test_urls = "https://example.com,https://example.org"
    for result in node2.execute({"urls": test_urls}, logger):
        print(f"Crawled {result['url']}: {result['success']}")
    
    # Test the SearchEngineCrawlerNode
    print("\nTesting SearchEngineCrawlerNode:")
    node3 = SearchEngineCrawlerNode()
    test_query = "python web crawling"
    result = asyncio.run(node3.execute({"query": test_query}, logger))
    print(f"Search result: {result['success']}")
