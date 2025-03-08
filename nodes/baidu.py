try:
    from autotask.nodes import Node, GeneratorNode, register_node
    from baidusearch.baidusearch import search
    import pycountry
except ImportError:
    # Mock for development environment
    from stub import Node, GeneratorNode, register_node
    # Mock classes for development
    def search(**kwargs):
        return [
            {"title": "Mock result", "url": "https://example.com", "abstract": "This is a mock search result"}
        ]
    
    class pycountry:
        class languages:
            @staticmethod
            def lookup(lang):
                class Lang:
                    alpha_2 = "zh"
                return Lang()

import json
import asyncio
from typing import Dict, Any, Generator, List, Optional


@register_node
class BaiduSearchNode(Node):
    """Node for performing searches using Baidu search engine"""
    NAME = "Baidu Search"
    DESCRIPTION = "Searches Baidu for given query and returns the results"
    CATEGORY = "Search"
    ICON = "search"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The query to search for on Baidu",
            "type": "STRING",
            "required": True,
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "The maximum number of results to return",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "language": {
            "label": "Language",
            "description": "Search language (e.g., 'zh' for Chinese, 'en' for English)",
            "type": "STRING",
            "default": "zh",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "results": {
            "label": "Search Results",
            "description": "JSON representation of search results from Baidu",
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
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            query = node_inputs.get("query")
            max_results = node_inputs.get("max_results", 5)
            language = node_inputs.get("language", "zh")
            
            if not query:
                workflow_logger.error("No search query provided")
                return {
                    "success": "false",
                    "error_message": "No search query provided",
                    "results": "[]"
                }
            
            # Convert language code if needed
            if len(language) != 2:
                try:
                    language = pycountry.languages.lookup(language).alpha_2
                except LookupError:
                    language = "zh"
                    workflow_logger.warning(f"Language not recognized, defaulting to Chinese (zh)")
            
            workflow_logger.info(f"Searching Baidu for: {query} in {language}, max results: {max_results}")
            
            # Perform the search
            search_results = search(keyword=query, num_results=max_results)
            
            # Format the results
            results = []
            for idx, item in enumerate(search_results, 1):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "abstract": item.get("abstract", ""),
                    "rank": str(idx),
                })
            
            workflow_logger.info(f"Found {len(results)} results for query: {query}")
            
            return {
                "success": "true",
                "results": json.dumps(results, indent=2),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Baidu search failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "results": "[]"
            }


@register_node
class BaiduMultiSearchNode(GeneratorNode):
    """Generator node for performing multiple Baidu searches sequentially"""
    NAME = "Baidu Multi-Query Search"
    DESCRIPTION = "Searches Baidu for multiple queries and yields results for each query"
    CATEGORY = "Search"
    ICON = "search-multiple"
    
    INPUTS = {
        "queries": {
            "label": "Search Queries",
            "description": "List of queries to search for (comma-separated)",
            "type": "STRING",
            "required": True,
        },
        "max_results_per_query": {
            "label": "Maximum Results Per Query",
            "description": "The maximum number of results to return for each query",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "language": {
            "label": "Language",
            "description": "Search language (e.g., 'zh' for Chinese, 'en' for English)",
            "type": "STRING",
            "default": "zh",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "query": {
            "label": "Current Query",
            "description": "The query that was searched for",
            "type": "STRING",
        },
        "results": {
            "label": "Search Results",
            "description": "JSON representation of search results from Baidu for the current query",
            "type": "STRING",
        },
        "result_count": {
            "label": "Result Count",
            "description": "Number of results found for the current query",
            "type": "INT",
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
    
    def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Generator:
        try:
            queries_input = node_inputs.get("queries", "")
            max_results = node_inputs.get("max_results_per_query", 5)
            language = node_inputs.get("language", "zh")
            
            # Parse queries
            if isinstance(queries_input, str):
                queries = [q.strip() for q in queries_input.split(",") if q.strip()]
            elif isinstance(queries_input, list):
                queries = [q for q in queries_input if q]
            else:
                queries = []
            
            if not queries:
                workflow_logger.error("No valid search queries provided")
                yield {
                    "query": "",
                    "results": "[]",
                    "result_count": 0,
                    "success": "false",
                    "error_message": "No valid search queries provided"
                }
                return
            
            # Convert language code if needed
            if len(language) != 2:
                try:
                    language = pycountry.languages.lookup(language).alpha_2
                except LookupError:
                    language = "zh"
                    workflow_logger.warning(f"Language not recognized, defaulting to Chinese (zh)")
            
            workflow_logger.info(f"Processing {len(queries)} Baidu search queries in {language}")
            
            # Process each query
            for query in queries:
                workflow_logger.info(f"Searching Baidu for: {query}")
                try:
                    # Perform the search
                    search_results = search(keyword=query, num_results=max_results)
                    
                    # Format the results
                    results = []
                    for idx, item in enumerate(search_results, 1):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "abstract": item.get("abstract", ""),
                            "rank": str(idx),
                        })
                    
                    result_count = len(results)
                    workflow_logger.info(f"Found {result_count} results for query: {query}")
                    
                    yield {
                        "query": query,
                        "results": json.dumps(results, indent=2),
                        "result_count": result_count,
                        "success": "true",
                        "error_message": ""
                    }
                    
                except Exception as e:
                    error_msg = f"Failed to search for '{query}': {str(e)}"
                    workflow_logger.error(error_msg)
                    
                    yield {
                        "query": query,
                        "results": "[]",
                        "result_count": 0,
                        "success": "false",
                        "error_message": error_msg
                    }
            
        except Exception as e:
            error_msg = f"Baidu multi-search failed: {str(e)}"
            workflow_logger.error(error_msg)
            
            yield {
                "query": "",
                "results": "[]",
                "result_count": 0,
                "success": "false",
                "error_message": error_msg
            }


@register_node
class BaiduResultFilterNode(Node):
    """Node for filtering and processing Baidu search results"""
    NAME = "Baidu Result Filter"
    DESCRIPTION = "Filters and processes Baidu search results based on specified criteria"
    CATEGORY = "Search"
    ICON = "filter"
    
    INPUTS = {
        "results_json": {
            "label": "Search Results JSON",
            "description": "JSON string of Baidu search results to filter",
            "type": "STRING",
            "required": True,
        },
        "keyword_filter": {
            "label": "Keyword Filter",
            "description": "Filter results that contain this keyword in title or abstract (leave empty for no filter)",
            "type": "STRING",
            "required": False,
        },
        "exclude_domains": {
            "label": "Exclude Domains",
            "description": "Comma-separated list of domains to exclude from results",
            "type": "STRING",
            "required": False,
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "Maximum number of results to return after filtering",
            "type": "INT",
            "default": 10,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "filtered_results": {
            "label": "Filtered Results",
            "description": "JSON representation of filtered search results",
            "type": "STRING",
        },
        "result_count": {
            "label": "Result Count",
            "description": "Number of results after filtering",
            "type": "INT",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the filtering operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if filtering failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            results_json = node_inputs.get("results_json", "[]")
            keyword_filter = node_inputs.get("keyword_filter", "").lower()
            exclude_domains_input = node_inputs.get("exclude_domains", "")
            max_results = node_inputs.get("max_results", 10)
            
            # Parse exclude domains
            exclude_domains = []
            if exclude_domains_input:
                exclude_domains = [domain.strip().lower() for domain in exclude_domains_input.split(",") if domain.strip()]
            
            # Parse results JSON
            try:
                results = json.loads(results_json)
                if not isinstance(results, list):
                    return {
                        "success": "false",
                        "error_message": "Invalid results JSON format, expected a list",
                        "filtered_results": "[]",
                        "result_count": 0
                    }
            except json.JSONDecodeError:
                return {
                    "success": "false",
                    "error_message": "Invalid JSON provided",
                    "filtered_results": "[]",
                    "result_count": 0
                }
            
            workflow_logger.info(f"Filtering {len(results)} Baidu search results")
            
            # Apply filters
            filtered_results = []
            for result in results:
                title = result.get("title", "").lower()
                abstract = result.get("abstract", "").lower()
                url = result.get("url", "").lower()
                
                # Check keyword filter
                if keyword_filter and keyword_filter not in title and keyword_filter not in abstract:
                    continue
                
                # Check domain exclusions
                domain_excluded = False
                for domain in exclude_domains:
                    if domain in url:
                        domain_excluded = True
                        break
                
                if domain_excluded:
                    continue
                
                filtered_results.append(result)
                
                # Check max results
                if len(filtered_results) >= max_results:
                    break
            
            workflow_logger.info(f"Filtered results: {len(filtered_results)} (from original {len(results)})")
            
            return {
                "success": "true",
                "filtered_results": json.dumps(filtered_results, indent=2),
                "result_count": len(filtered_results),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Baidu result filtering failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "filtered_results": "[]",
                "result_count": 0
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test BaiduSearchNode
    print("\nTesting BaiduSearchNode:")
    node1 = BaiduSearchNode()
    result = asyncio.run(node1.execute({"query": "Python programming", "max_results": 3}, logger))
    print(f"Search results found: {len(json.loads(result['results']))}")
    
    # Test BaiduMultiSearchNode
    print("\nTesting BaiduMultiSearchNode:")
    node2 = BaiduMultiSearchNode()
    queries = "Python,Machine Learning"
    result_count = 0
    for result in node2.execute({"queries": queries, "max_results_per_query": 2}, logger):
        result_count += 1
        print(f"Query '{result['query']}' returned {result['result_count']} results")
    print(f"Total queries processed: {result_count}")
    
    # Test BaiduResultFilterNode
    print("\nTesting BaiduResultFilterNode:")
    sample_results = [
        {"title": "Python Programming Guide", "url": "https://example.com/python", "abstract": "Learn Python programming"},
        {"title": "Java Tutorial", "url": "https://example.com/java", "abstract": "Java programming tutorials"},
        {"title": "Python vs Java", "url": "https://blog.com/compare", "abstract": "Comparing Python and Java languages"}
    ]
    node3 = BaiduResultFilterNode()
    result = asyncio.run(node3.execute({
        "results_json": json.dumps(sample_results),
        "keyword_filter": "python",
        "exclude_domains": "blog.com"
    }, logger))
    print(f"Filtered results: {result['result_count']}") 