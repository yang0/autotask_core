try:
    from autotask.nodes import Node, GeneratorNode, register_node
    from googlesearch import search
    import json
    import pycountry
except ImportError:
    # Mock for development environment
    from stub import Node, GeneratorNode, register_node
    # Mock classes
    class search:
        @staticmethod
        def search(query, num_results=10, lang="en", proxy=None, advanced=True):
            class MockResult:
                def __init__(self, idx):
                    self.title = f"Result {idx} for {query}"
                    self.url = f"https://example.com/result{idx}"
                    self.description = f"This is a mock description for search result {idx} about {query}"
            
            return [MockResult(i) for i in range(1, num_results + 1)]
    
    class pycountry:
        class languages:
            @staticmethod
            def lookup(lang_name):
                class Language:
                    def __init__(self, name, code):
                        self.name = name
                        self.alpha_2 = code
                
                language_map = {
                    "english": "en",
                    "spanish": "es",
                    "french": "fr",
                    "german": "de",
                    "chinese": "zh"
                }
                
                if lang_name.lower() in language_map:
                    return Language(lang_name, language_map[lang_name.lower()])
                return None

from typing import Dict, Any, List, Optional


@register_node
class GoogleSearchNode(Node):
    """Node for searching Google and retrieving search results"""
    NAME = "Google Search"
    DESCRIPTION = "Searches Google for a query and returns the search results"
    CATEGORY = "Search"
    ICON = "google"
    
    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The query to search for on Google",
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
        "language": {
            "label": "Language",
            "description": "The language code (e.g., 'en', 'es') or language name for the search results",
            "type": "STRING",
            "default": "en",
            "required": False,
        },
        "proxy": {
            "label": "Proxy",
            "description": "Optional proxy server to use for the search (e.g., 'http://user:pass@proxy:port')",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "results": {
            "label": "Search Results",
            "description": "JSON representation of the Google search results",
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
            language = node_inputs.get("language", "en")
            proxy = node_inputs.get("proxy", None)
            
            if not query:
                workflow_logger.error("No search query provided")
                return {
                    "success": "false",
                    "error_message": "No search query provided",
                    "results": "[]",
                    "results_count": 0
                }
            
            # Resolve language to ISO 639-1 code if needed
            if len(language) != 2:
                try:
                    lang_obj = pycountry.languages.lookup(language)
                    if lang_obj:
                        language = lang_obj.alpha_2
                    else:
                        language = "en"
                        workflow_logger.warning(f"Language '{language}' not recognized, defaulting to English (en)")
                except Exception as e:
                    language = "en"
                    workflow_logger.warning(f"Error resolving language: {str(e)}, defaulting to English (en)")
            
            workflow_logger.info(f"Searching Google [{language}] for: {query}")
            
            try:
                # Perform Google search
                search_results = list(search(query, num_results=max_results, lang=language, proxy=proxy, advanced=True))
                
                # Process the search results
                results = []
                for result in search_results:
                    results.append({
                        "title": result.title,
                        "url": result.url,
                        "description": result.description
                    })
                
                workflow_logger.info(f"Found {len(results)} search results for: {query}")
                
                return {
                    "success": "true",
                    "results": json.dumps(results, indent=2),
                    "results_count": len(results),
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error performing Google search: {str(e)}"
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "error_message": error_msg,
                    "results": "[]",
                    "results_count": 0
                }
            
        except Exception as e:
            error_msg = f"Error with Google search: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "results": "[]",
                "results_count": 0
            }


@register_node
class GoogleMultiSearchNode(GeneratorNode):
    """Generator node for performing multiple Google searches sequentially"""
    NAME = "Google Multi-Search"
    DESCRIPTION = "Performs multiple Google searches sequentially and yields results for each query"
    CATEGORY = "Search"
    ICON = "google"
    
    INPUTS = {
        "queries": {
            "label": "Search Queries",
            "description": "List of queries to search for (comma-separated)",
            "type": "STRING",
            "required": True,
        },
        "max_results_per_query": {
            "label": "Max Results Per Query",
            "description": "The maximum number of search results to return for each query",
            "type": "INT",
            "default": 3,
            "required": False,
        },
        "language": {
            "label": "Language",
            "description": "The language code (e.g., 'en', 'es') or language name for the search results",
            "type": "STRING",
            "default": "en",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "query": {
            "label": "Current Query",
            "description": "The current search query being processed",
            "type": "STRING",
        },
        "results": {
            "label": "Search Results",
            "description": "JSON representation of the Google search results for the current query",
            "type": "STRING",
        },
        "results_count": {
            "label": "Results Count",
            "description": "Number of search results returned for the current query",
            "type": "INT",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful for the current query",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed for the current query",
            "type": "STRING",
        }
    }
    
    def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Any:
        try:
            queries_input = node_inputs.get("queries", "")
            max_results = node_inputs.get("max_results_per_query", 3)
            language = node_inputs.get("language", "en")
            
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
                    "results_count": 0,
                    "success": "false",
                    "error_message": "No valid search queries provided"
                }
                return
            
            # Resolve language to ISO 639-1 code if needed
            if len(language) != 2:
                try:
                    lang_obj = pycountry.languages.lookup(language)
                    if lang_obj:
                        language = lang_obj.alpha_2
                    else:
                        language = "en"
                        workflow_logger.warning(f"Language '{language}' not recognized, defaulting to English (en)")
                except Exception as e:
                    language = "en"
                    workflow_logger.warning(f"Error resolving language: {str(e)}, defaulting to English (en)")
            
            workflow_logger.info(f"Processing {len(queries)} search queries")
            
            # Process each query
            for query in queries:
                workflow_logger.info(f"Searching Google [{language}] for: {query}")
                
                try:
                    # Perform Google search
                    search_results = list(search(query, num_results=max_results, lang=language, advanced=True))
                    
                    # Process the search results
                    results = []
                    for result in search_results:
                        results.append({
                            "title": result.title,
                            "url": result.url,
                            "description": result.description
                        })
                    
                    workflow_logger.info(f"Found {len(results)} search results for: {query}")
                    
                    yield {
                        "query": query,
                        "results": json.dumps(results, indent=2),
                        "results_count": len(results),
                        "success": "true",
                        "error_message": ""
                    }
                    
                except Exception as e:
                    error_msg = f"Error searching for '{query}': {str(e)}"
                    workflow_logger.error(error_msg)
                    
                    yield {
                        "query": query,
                        "results": "[]",
                        "results_count": 0,
                        "success": "false",
                        "error_message": error_msg
                    }
            
        except Exception as e:
            error_msg = f"Error with Google multi-search: {str(e)}"
            workflow_logger.error(error_msg)
            
            yield {
                "query": "",
                "results": "[]",
                "results_count": 0,
                "success": "false",
                "error_message": error_msg
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test GoogleSearchNode
    print("\nTesting GoogleSearchNode:")
    node1 = GoogleSearchNode()
    result = asyncio.run(node1.execute({"query": "Python programming"}, logger))
    print(f"Success: {result['success']}")
    print(f"Results count: {result['results_count']}")
    
    # Preview the first result
    if result['results_count'] > 0:
        results = json.loads(result['results'])
        print(f"First result title: {results[0]['title']}")
        print(f"First result URL: {results[0]['url']}")
    
    # Test GoogleMultiSearchNode
    print("\nTesting GoogleMultiSearchNode:")
    node2 = GoogleMultiSearchNode()
    queries = "Python,Machine Learning"
    result_count = 0
    
    for result in node2.execute({"queries": queries, "max_results_per_query": 2}, logger):
        result_count += 1
        print(f"Query '{result['query']}' returned {result['results_count']} results")
    
    print(f"Total queries processed: {result_count}") 