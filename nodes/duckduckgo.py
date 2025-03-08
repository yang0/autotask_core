try:
    from autotask.nodes import Node, register_node
    from duckduckgo_search import DDGS
    import json
except ImportError:
    # Mock for development environment
    from stub import Node, register_node
    
    # Mock DDGS class
    class DDGS:
        def __init__(self, headers=None, proxy=None, proxies=None, timeout=10, verify=True):
            self.headers = headers
            self.proxy = proxy
            self.proxies = proxies
            self.timeout = timeout
            self.verify = verify
        
        def text(self, keywords="", max_results=5):
            return [
                {
                    "title": f"Mock result 1 for {keywords}",
                    "href": f"https://example.com/result1?q={keywords}",
                    "body": f"This is a mock search result for {keywords}. It contains sample text that would be returned by DuckDuckGo."
                },
                {
                    "title": f"Mock result 2 for {keywords}",
                    "href": f"https://example.com/result2?q={keywords}",
                    "body": f"Another mock search result for {keywords}. This would contain content from a web page."
                }
            ][:max_results]
        
        def news(self, keywords="", max_results=5):
            return [
                {
                    "title": f"Mock news 1 about {keywords}",
                    "href": f"https://news.example.com/news1?q={keywords}",
                    "body": f"Breaking news about {keywords}. This is a mock news result.",
                    "date": "2023-07-15"
                },
                {
                    "title": f"Mock news 2 about {keywords}",
                    "href": f"https://news.example.com/news2?q={keywords}",
                    "body": f"Latest developments regarding {keywords}. Another mock news item.",
                    "date": "2023-07-14"
                }
            ][:max_results]

from typing import Dict, Any, Optional, List


@register_node
class DuckDuckGoSearchNode(Node):
    """Node for searching DuckDuckGo and retrieving search results"""
    NAME = "DuckDuckGo Search"
    DESCRIPTION = "Searches DuckDuckGo for a query and returns the search results"
    CATEGORY = "Search"
    ICON = "search"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The query to search for on DuckDuckGo",
            "type": "STRING",
            "required": True,
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "The maximum number of search results to return",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "modifier": {
            "label": "Search Modifier",
            "description": "Optional modifier to prepend to the search query (e.g., 'site:example.com')",
            "type": "STRING",
            "required": False,
        },
        "proxy": {
            "label": "Proxy",
            "description": "Optional proxy server to use for the search",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "results": {
            "label": "Search Results",
            "description": "JSON representation of the DuckDuckGo search results",
            "type": "STRING",
        },
        "results_count": {
            "label": "Results Count",
            "description": "Number of search results returned",
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
            query = node_inputs.get("query", "")
            max_results = node_inputs.get("max_results", 5)
            modifier = node_inputs.get("modifier", "")
            proxy = node_inputs.get("proxy", None)
            
            if not query:
                workflow_logger.error("No search query provided")
                return {
                    "success": "false",
                    "error_message": "No search query provided",
                    "results": "[]",
                    "results_count": 0
                }
            
            workflow_logger.info(f"Searching DuckDuckGo for: {query}")
            
            # Initialize DuckDuckGo search
            ddgs = DDGS(proxy=proxy, timeout=10)
            
            # Apply modifier if provided
            if modifier:
                search_query = f"{modifier} {query}"
                workflow_logger.info(f"Applied modifier. Final query: {search_query}")
            else:
                search_query = query
            
            # Perform search
            search_results = ddgs.text(keywords=search_query, max_results=max_results)
            
            # Process the search results
            results_count = len(search_results)
            workflow_logger.info(f"Found {results_count} search results for: {query}")
            
            return {
                "success": "true",
                "results": json.dumps(search_results, indent=2),
                "results_count": results_count,
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error searching DuckDuckGo: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "results": "[]",
                "results_count": 0
            }


@register_node
class DuckDuckGoNewsNode(Node):
    """Node for searching DuckDuckGo News for recent news articles"""
    NAME = "DuckDuckGo News"
    DESCRIPTION = "Searches DuckDuckGo News for recent articles about a topic"
    CATEGORY = "Search"
    ICON = "newspaper"
    
    INPUTS = {
        "query": {
            "label": "News Query",
            "description": "The topic to search for in news articles",
            "type": "STRING",
            "required": True,
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "The maximum number of news articles to return",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "proxy": {
            "label": "Proxy",
            "description": "Optional proxy server to use for the search",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "news_articles": {
            "label": "News Articles",
            "description": "JSON representation of the news articles",
            "type": "STRING",
        },
        "article_count": {
            "label": "Article Count",
            "description": "Number of news articles returned",
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
            query = node_inputs.get("query", "")
            max_results = node_inputs.get("max_results", 5)
            proxy = node_inputs.get("proxy", None)
            
            if not query:
                workflow_logger.error("No news query provided")
                return {
                    "success": "false",
                    "error_message": "No news query provided",
                    "news_articles": "[]",
                    "article_count": 0
                }
            
            workflow_logger.info(f"Searching DuckDuckGo News for: {query}")
            
            # Initialize DuckDuckGo search
            ddgs = DDGS(proxy=proxy, timeout=10)
            
            # Perform news search
            news_results = ddgs.news(keywords=query, max_results=max_results)
            
            # Process the news results
            article_count = len(news_results)
            workflow_logger.info(f"Found {article_count} news articles for: {query}")
            
            return {
                "success": "true",
                "news_articles": json.dumps(news_results, indent=2),
                "article_count": article_count,
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error searching DuckDuckGo News: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "news_articles": "[]",
                "article_count": 0
            }


@register_node
class DuckDuckGoMultiTopicNode(Node):
    """Node for searching multiple topics on DuckDuckGo and aggregating results"""
    NAME = "DuckDuckGo Multi-Topic Search"
    DESCRIPTION = "Searches multiple topics on DuckDuckGo and aggregates the results"
    CATEGORY = "Search"
    ICON = "layer-group"
    
    INPUTS = {
        "topics": {
            "label": "Search Topics",
            "description": "Comma-separated list of topics to search for",
            "type": "STRING",
            "required": True,
        },
        "max_results_per_topic": {
            "label": "Max Results Per Topic",
            "description": "Maximum number of results to return for each topic",
            "type": "INT",
            "default": 3,
            "required": False,
        },
        "include_news": {
            "label": "Include News",
            "description": "Whether to include news results in addition to web results",
            "type": "STRING",
            "default": "false",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "aggregated_results": {
            "label": "Aggregated Results",
            "description": "JSON representation of all search results, organized by topic",
            "type": "STRING",
        },
        "total_results_count": {
            "label": "Total Results Count",
            "description": "Total number of search results across all topics",
            "type": "INT",
        },
        "topic_count": {
            "label": "Topic Count",
            "description": "Number of topics that were searched",
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
            topics_input = node_inputs.get("topics", "")
            max_results = node_inputs.get("max_results_per_topic", 3)
            include_news_str = node_inputs.get("include_news", "false")
            
            # Parse topics
            if isinstance(topics_input, str):
                topics = [topic.strip() for topic in topics_input.split(",") if topic.strip()]
            elif isinstance(topics_input, list):
                topics = [topic for topic in topics_input if topic]
            else:
                topics = []
            
            if not topics:
                workflow_logger.error("No valid search topics provided")
                return {
                    "success": "false",
                    "error_message": "No valid search topics provided",
                    "aggregated_results": "{}",
                    "total_results_count": 0,
                    "topic_count": 0
                }
            
            # Convert string input to boolean
            include_news = include_news_str.lower() == "true"
            
            workflow_logger.info(f"Searching DuckDuckGo for {len(topics)} topics")
            
            # Initialize DuckDuckGo search
            ddgs = DDGS(timeout=10)
            
            # Initialize aggregated results
            aggregated_results = {}
            total_results_count = 0
            
            # Search each topic
            for topic in topics:
                try:
                    # Get web search results
                    web_results = ddgs.text(keywords=topic, max_results=max_results)
                    
                    # Get news results if requested
                    news_results = []
                    if include_news:
                        news_results = ddgs.news(keywords=topic, max_results=max_results)
                    
                    # Add to aggregated results
                    aggregated_results[topic] = {
                        "web_results": web_results,
                        "news_results": news_results if include_news else []
                    }
                    
                    # Update total count
                    total_results_count += len(web_results) + len(news_results)
                    
                    workflow_logger.info(f"Found {len(web_results)} web results and {len(news_results) if include_news else 0} news results for topic: {topic}")
                    
                except Exception as e:
                    workflow_logger.warning(f"Error searching for topic '{topic}': {str(e)}")
                    # Add empty results for this topic
                    aggregated_results[topic] = {
                        "web_results": [],
                        "news_results": [],
                        "error": str(e)
                    }
            
            workflow_logger.info(f"Completed search for {len(topics)} topics with {total_results_count} total results")
            
            return {
                "success": "true",
                "aggregated_results": json.dumps(aggregated_results, indent=2),
                "total_results_count": total_results_count,
                "topic_count": len(topics),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error with multi-topic search: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "aggregated_results": "{}",
                "total_results_count": 0,
                "topic_count": 0
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test DuckDuckGoSearchNode
    print("\nTesting DuckDuckGoSearchNode:")
    node1 = DuckDuckGoSearchNode()
    result = asyncio.run(node1.execute({"query": "Python programming"}, logger))
    print(f"Success: {result['success']}")
    print(f"Results count: {result['results_count']}")
    
    # Test DuckDuckGoNewsNode
    print("\nTesting DuckDuckGoNewsNode:")
    node2 = DuckDuckGoNewsNode()
    result = asyncio.run(node2.execute({"query": "artificial intelligence", "max_results": 3}, logger))
    print(f"Success: {result['success']}")
    print(f"Article count: {result['article_count']}")
    
    # Test DuckDuckGoMultiTopicNode
    print("\nTesting DuckDuckGoMultiTopicNode:")
    node3 = DuckDuckGoMultiTopicNode()
    result = asyncio.run(node3.execute({
        "topics": "Python,Machine Learning,Data Science",
        "max_results_per_topic": 2,
        "include_news": "true"
    }, logger))
    print(f"Success: {result['success']}")
    print(f"Topic count: {result['topic_count']}")
    print(f"Total results: {result['total_results_count']}")
