try:
    from autotask.nodes import Node, register_node
    from autotask.api_keys import get_api_key
except ImportError:
    from stub import Node, register_node, get_api_key

import json
from typing import Dict, Any, Optional, List
import time
from loguru import logger as default_logger
import inspect

try:
    from exa_py import Exa
    from exa_py.api import SearchResponse
except ImportError:
    raise ImportError("`exa_py` not installed. Please install using `pip install exa_py`")


# 添加调试信息
default_logger.info("[DEBUG-EXA] 准备获取API密钥")
    

    
    
EXA_API_KEY = get_api_key(provider="exa.ai", key_name="EXA_API_KEY")


@register_node
class ExaSearchNode(Node):
    """
    Perform Exa search and return results
    
    Uses the Exa API to search web content and return formatted results. Exa is a powerful search engine 
    focused on providing high-quality, structured search results. This node supports various filtering 
    options, including category filtering and domain inclusion/exclusion. Search results include title, 
    URL, content summary, and other metadata.
    
    Use cases:
    - Obtaining the latest information from the web
    - Researching specific topics or fields
    - Filtering specific types of content (such as academic papers, news, company information, etc.)
    - Limiting search scope to specific websites
    
    Notes:
    - Search result quality depends on the precision of query terms
    - Category filtering can significantly improve relevance
    - For content from specific websites, use the include_domains parameter
    """
    NAME = "Exa Search"
    DESCRIPTION = "Search the web using Exa search engine for high-quality, relevant results with filtering capabilities."

    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "The query to search for",
            "type": "STRING",
            "required": True,
        },
        "num_results": {
            "label": "Number of Results",
            "description": "The number of results to return",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "category": {
            "label": "Category",
            "description": "Filter results by category (e.g., 'company', 'research paper', 'news', 'pdf', 'github')",
            "type": "STRING",
            "default": "",
            "required": False,
        },
        "include_domains": {
            "label": "Include Domains",
            "description": "Restrict results to these domains (comma separated)",
            "type": "STRING",
            "default": "",
            "required": False,
        },
        "exclude_domains": {
            "label": "Exclude Domains",
            "description": "Exclude results from these domains (comma separated)",
            "type": "STRING",
            "default": "",
            "required": False,
        }
    }

    OUTPUTS = {
        "search_results": {
            "label": "Search Results",
            "description": "The results from Exa search",
            "type": "LIST",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            query = node_inputs.get("query", "")
            num_results = node_inputs.get("num_results", 5)
            category = node_inputs.get("category", "")
            
            include_domains_str = node_inputs.get("include_domains", "")
            exclude_domains_str = node_inputs.get("exclude_domains", "")
            
            include_domains = [d.strip() for d in include_domains_str.split(",")] if include_domains_str else None
            exclude_domains = [d.strip() for d in exclude_domains_str.split(",")] if exclude_domains_str else None
            
            # 记录开始搜索
            logger.info(f"Starting Exa search for: '{query}'")
            start_time = time.time()
            
            # 创建Exa客户端
            exa_client = Exa(EXA_API_KEY)
            
            # 执行搜索
            search_kwargs = {
                "num_results": num_results,
                "text": True,
                "highlights": True,
                "text_length_limit": 1000,
            }
            
            if category:
                search_kwargs["category"] = category
            if include_domains:
                search_kwargs["include_domains"] = include_domains
            if exclude_domains:
                search_kwargs["exclude_domains"] = exclude_domains
                
            exa_results = exa_client.search_and_contents(query, **search_kwargs)
            
            # 格式化结果
            formatted_results = self._format_search_results(exa_results)
            
            elapsed = time.time() - start_time
            logger.info(f"Search completed in {elapsed:.2f}s, found {len(formatted_results)} results")
            
            return {
                "success": True,
                "search_results": formatted_results
            }

        except Exception as e:
            logger.error(f"Exa search failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False, 
                "error_message": str(e)
            }
    
    def _format_search_results(self, exa_results: SearchResponse) -> List[Dict[str, Any]]:
        """格式化Exa搜索结果"""
        formatted_results = []
        for result in exa_results.results:
            result_dict = {
                "title": result.title if result.title else "No title",
                "url": result.url,
                "text": result.text[:1000] if result.text else "No content",
                "source": "Exa"
            }
            
            if result.author and result.author != "":
                result_dict["author"] = result.author
                
            if result.published_date:
                result_dict["published_date"] = result.published_date
                
            if hasattr(result, 'highlights') and result.highlights:
                result_dict["highlights"] = result.highlights
                
            formatted_results.append(result_dict)
            
        return formatted_results


@register_node
class ExaNewsNode(Node):
    """
    Use Exa search engine to get news results
    
    Searches specifically for news content through the Exa API and returns formatted results. This node 
    is optimized for news content, retrieving the latest news reports, articles, and analyses. Supports 
    filtering by time range to ensure recently published content is obtained.
    
    Use cases:
    - Getting the latest news on specific topics
    - Monitoring industry developments and market trends
    - Tracking event developments and current affairs updates
    - Collecting news reports from multiple sources for analysis
    
    Features:
    - Time-based filtering (news from recent days)
    - Automatic categorization as news content
    - Returns formatted news results, including title, description, URL, and publication date
    - Source information identification to help evaluate news reliability
    
    Notes:
    - Specific query terms are recommended for more relevant news
    - The days_ago parameter controls the timeliness of news, default is 30 days
    """
    NAME = "Exa News"
    DESCRIPTION = "Search for latest news articles and reports using Exa search engine with time-based filtering."

    INPUTS = {
        "query": {
            "label": "News Query",
            "description": "The news topic to search for",
            "type": "STRING",
            "required": True,
        },
        "num_results": {
            "label": "Number of Results",
            "description": "The number of news articles to return",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "days_ago": {
            "label": "Days Ago",
            "description": "Only return news from this many days ago to now",
            "type": "INT",
            "default": 30,
            "required": False,
        }
    }

    OUTPUTS = {
        "news_results": {
            "label": "News Results",
            "description": "The news results from Exa",
            "type": "LIST",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            query = node_inputs.get("query", "")
            num_results = node_inputs.get("num_results", 5)
            days_ago = node_inputs.get("days_ago", 30)
            
            # 记录开始搜索
            logger.info(f"Starting Exa news search for: '{query}'")
            start_time = time.time()
            
            # 创建日期范围
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_ago)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            # 创建Exa客户端
            exa_client = Exa(EXA_API_KEY)
            
            # 执行搜索，使用news类别和日期过滤
            search_kwargs = {
                "num_results": num_results,
                "text": True,
                "highlights": True,
                "text_length_limit": 1000,
                "category": "news",
                "start_published_date": start_date_str
            }
                
            exa_results = exa_client.search_and_contents(query, **search_kwargs)
            
            # 格式化结果
            formatted_results = self._format_news_results(exa_results)
            
            elapsed = time.time() - start_time
            logger.info(f"News search completed in {elapsed:.2f}s, found {len(formatted_results)} news articles")
            
            return {
                "success": True,
                "news_results": formatted_results
            }

        except Exception as e:
            logger.error(f"Exa news search failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False, 
                "error_message": str(e)
            }
    
    def _format_news_results(self, exa_results: SearchResponse) -> List[Dict[str, Any]]:
        """格式化Exa新闻搜索结果"""
        formatted_results = []
        for result in exa_results.results:
            result_dict = {
                "title": result.title if result.title else "无标题",
                "description": result.text[:300] if result.text else "无描述",
                "url": result.url,
                "date_published": result.published_date if result.published_date else "",
                "provider": result.author if result.author else "Unknown Source"
            }
            
            formatted_results.append(result_dict)
            
        return formatted_results


@register_node
class ExaAnswerNode(Node):
    """
    Use Exa's intelligent answer feature to provide answers to questions
    
    Obtains LLM answers based on web search results through the Exa API. This node not only performs 
    searches but also uses large language models to analyze search results and generate coherent, 
    informative answers. It automatically cites sources, ensuring the reliability and traceability 
    of answers.
    
    Use cases:
    - Answering fact-based questions
    - Getting overviews and summaries of specific topics
    - Research queries requiring source citations
    - Comprehensive analysis of the latest information
    
    Supported models:
    - exa: Standard model suitable for most queries
    - exa-pro: Advanced model providing more detailed and comprehensive answers
    
    Features:
    - Intelligent synthesis of information from multiple sources
    - Automatic citation of information sources
    - Option to include complete reference text
    - Returns structured answers and source lists
    
    Notes:
    - Queries should be clear and specific for best results
    - For complex questions, the exa-pro model performs better
    - Source citations help verify the accuracy of answers
    """
    NAME = "Exa Answer"
    DESCRIPTION = "Get comprehensive, source-backed answers to questions using Exa's LLM capabilities with automatic citation."

    INPUTS = {
        "query": {
            "label": "Question",
            "description": "The question to answer",
            "type": "STRING",
            "required": True,
        },
        "model": {
            "label": "Model",
            "description": "The model to use (exa or exa-pro)",
            "type": "STRING",
            "default": "exa",
            "required": False,
        },
        "include_text": {
            "label": "Include Full Text",
            "description": "Include full text from citation sources",
            "type": "BOOL",
            "default": False,
            "required": False,
        }
    }

    OUTPUTS = {
        "answer": {
            "label": "Answer",
            "description": "The answer to the question",
            "type": "STRING",
        },
        "sources": {
            "label": "Sources",
            "description": "The sources used to generate the answer",
            "type": "LIST",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            query = node_inputs.get("query", "")
            model = node_inputs.get("model", "exa")
            include_text = node_inputs.get("include_text", False)
            
            # 验证模型参数
            if model not in ["exa", "exa-pro"]:
                logger.warning(f"Invalid model {model}, defaulting to 'exa'")
                model = "exa"
            
            # 记录开始查询
            logger.info(f"Getting Exa answer for question: '{query}'")
            start_time = time.time()
            
            # 创建Exa客户端
            exa_client = Exa(EXA_API_KEY)
            
            # 执行查询
            answer_kwargs = {
                "model": model,
                "text": include_text
            }
                
            answer = exa_client.answer(query=query, **answer_kwargs)
            
            # 格式化结果
            answer_text = answer.answer if hasattr(answer, 'answer') else "No answer found"
            
            sources = []
            if hasattr(answer, 'citations'):
                for citation in answer.citations:
                    source = {
                        "title": citation.title if citation.title else "No title",
                        "url": citation.url,
                        "id": citation.id
                    }
                    
                    if citation.published_date:
                        source["published_date"] = citation.published_date
                        
                    if citation.author:
                        source["author"] = citation.author
                        
                    if include_text and citation.text:
                        source["text"] = citation.text
                        
                    sources.append(source)
            
            elapsed = time.time() - start_time
            logger.info(f"Answer generated in {elapsed:.2f}s with {len(sources)} sources")
            
            return {
                "success": True,
                "answer": answer_text,
                "sources": sources
            }

        except Exception as e:
            logger.error(f"Exa answer generation failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False, 
                "error_message": str(e)
            }
