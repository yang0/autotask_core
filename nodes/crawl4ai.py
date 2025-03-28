import traceback
try:
    from autotask.nodes import Node, GeneratorNode, register_node
    from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
except ImportError:
    traceback.print_exc()
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
from typing import Dict, Any, Generator, List, Optional, AsyncGenerator


JS_CODE="""
        function scrollPage() {
            window.scrollTo(0, document.body.scrollHeight);
            return {
                height: document.body.scrollHeight,
                scrolled: true
            };
        }
        return scrollPage();
    """


class BaseCrawlerNode:
    """Base class for all crawler nodes"""
    _crawler_instance = None
    _crawler_lock = asyncio.Lock()
    _current_config = None

    @classmethod
    async def get_crawler(cls, cookie_file=None, headless=True):
        """获取或创建 AsyncWebCrawler 实例"""
        async with cls._crawler_lock:
            # 检查是否需要重新创建实例（配置发生变化）
            new_config = (cookie_file, headless)
            if cls._crawler_instance is None or cls._current_config != new_config:
                # 创建浏览器配置
                browser_config = None
                if cookie_file or headless is not None:
                    from crawl4ai import BrowserConfig
                    import json

                    # 加载 cookies
                    cookies = None
                    if cookie_file:
                        try:
                            with open(cookie_file, 'r') as f:
                                cookie_data = json.load(f)
                                # 处理两种格式的 cookie 文件
                                if isinstance(cookie_data, list):
                                    cookies = cookie_data
                                elif isinstance(cookie_data, dict) and 'cookies' in cookie_data:
                                    cookies = cookie_data['cookies']
                        except Exception as e:
                            print(f"Failed to load cookies from file: {str(e)}")

                    browser_config = BrowserConfig(
                        cookies=cookies,
                        headless=headless
                    )

                # 创建新的 crawler 实例
                if cls._crawler_instance:
                    await cls._crawler_instance.close()
                cls._crawler_instance = AsyncWebCrawler(config=browser_config, thread_safe=True)
                
                await cls._crawler_instance.start()
                cls._current_config = new_config

            return cls._crawler_instance

@register_node
class WebCrawlerNode(Node, BaseCrawlerNode):
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
        },
        "cookie_file": {
            "label": "Cookie File",
            "description": "Path to a JSON file containing cookies to load",
            "type": "STRING",
            "required": False,
        },
        "headless": {
            "label": "Headless Mode",
            "description": "Whether to run the browser in headless mode (no GUI)",
            "type": "BOOLEAN",
            "default": True,
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

    def __init__(self):
        Node.__init__(self)
        BaseCrawlerNode.__init__(self)
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        global JS_CODE
        try:
            url = node_inputs.get("url")
            max_length = node_inputs.get("max_length")
            use_cache = node_inputs.get("use_cache", False)
            cookie_file = node_inputs.get("cookie_file")
            headless = node_inputs.get("headless", True)
            
            if not url:
                workflow_logger.error("No URL provided")
                return {
                    "success": False,
                    "error_message": "No URL provided",
                    "content": ""
                }
            
            workflow_logger.info(f"Starting web crawling for: {url}")
            
            # 获取配置好的 crawler 实例
            crawler = await self.get_crawler(cookie_file=cookie_file, headless=headless)
            crawler_config = CrawlerRunConfig(
                    wait_until="load",  # 等待网络请求完成
                    # 可选值:
                    # - "domcontentloaded": 等待 DOMContentLoaded 事件
                    # - "load": 等待 load 事件
                    # - "networkidle": 等待网络请求完成（最严格）
                    # - "commit": 等待页面开始接收响应
                    # js_code=JS_CODE,
                    # js_only=False,
                    scan_full_page=True,  # 自动滚动页面以加载懒加载内容
                    scroll_delay=0.5,  # 滚动间隔时间
                    page_timeout=30000,
                    verbose=True
                )
            result = await crawler.arun(
                url=url, 
                cache_mode=CacheMode.BYPASS if not use_cache else None,
                config=crawler_config
                )
            
            if not result.markdown:
                workflow_logger.warning(f"No content found for {url}")
                return {
                    "success": True,
                    "content": "",
                    "error_message": "No content found"
                }
            
            content = result.markdown
            if max_length:
                content = content[:max_length]
            
            return {
                "success": True,
                "content": content,
                "error_message": ""
            }
                
        except Exception as e:
            traceback.print_exc()
            error_msg = f"Web crawling failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
                "content": ""
            }


@register_node
class MultiWebCrawlerNode(GeneratorNode, BaseCrawlerNode):
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
        },
        "cookie_file": {
            "label": "Cookie File",
            "description": "Path to a JSON file containing cookies to load",
            "type": "STRING",
            "required": False,
        },
        "headless": {
            "label": "Headless Mode",
            "description": "Whether to run the browser in headless mode (no GUI)",
            "type": "BOOLEAN",
            "default": True,
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

    def __init__(self):
        GeneratorNode.__init__(self)
        BaseCrawlerNode.__init__(self)
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            urls_input = node_inputs.get("urls", "")
            max_length = node_inputs.get("max_length_per_url")
            use_cache = node_inputs.get("use_cache", False)
            cookie_file = node_inputs.get("cookie_file")
            headless = node_inputs.get("headless", True)
            
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
            
            # 获取配置好的 crawler 实例
            crawler = await self.get_crawler(cookie_file=cookie_file, headless=headless)
            
            # Determine cache mode
            cache_mode = CacheMode.BYPASS if not use_cache else None
            
            # Process each URL
            for url in urls:
                workflow_logger.info(f"Crawling URL: {url}")
                try:
                    content = await self._crawl_url(url, max_length, cache_mode)
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
        crawler = await self.get_crawler()
        result = await crawler.arun(url=url, cache_mode=cache_mode)
        
        if not result.markdown:
            return ""
        
        # Process the content
        content = result.markdown
        if max_length:
            content = content[:max_length]
            
        return content



@register_node
class SearchEngineCrawlerNode(Node, BaseCrawlerNode):
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

    def __init__(self):
        Node.__init__(self)
        BaseCrawlerNode.__init__(self)
    
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
            

            crawler = await self.get_crawler()
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
