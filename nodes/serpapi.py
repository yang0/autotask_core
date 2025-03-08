import json
import time
import traceback
from typing import Dict, Any, List, Optional
from os import getenv

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger

try:
    from serpapi import GoogleSearch
except ImportError:
    raise ImportError("`google-search-results` not installed. Please install using `pip install google-search-results`")


@register_node
class SerpApiGoogleSearchNode(Node):
    """
    使用 SerpAPI 进行 Google 搜索
    
    这个节点使用 SerpAPI 执行 Google 搜索并返回结构化结果。SerpAPI 是一个强大的搜索 API，
    能够提供与 Google 搜索页面相同的结果，包括自然搜索结果、知识图谱、相关问题、购物结果等。
    这个节点适用于需要高质量搜索结果的工作流，特别是涉及数据收集、市场研究或内容聚合的场景。
    
    使用场景:
    - 市场研究和竞争分析
    - 数据聚合和信息收集
    - 内容生成和研究
    - 跟踪搜索趋势和相关查询
    
    特点:
    - 获取完整的 Google 搜索结果
    - 支持筛选不同类型的结果（有机结果、购物、知识图谱等）
    - 支持区域和语言本地化
    - 返回结构化的 JSON 格式结果
    
    注意:
    - 需要 SerpAPI 密钥
    - API 调用受到速率限制和配额限制
    - 搜索结果可能因地区、设备类型和时间而异
    """
    NAME = "SerpAPI Google 搜索"
    DESCRIPTION = "使用 SerpAPI 执行 Google 搜索并返回结构化结果"
    CATEGORY = "Search"
    ICON = "google"

    INPUTS = {
        "query": {
            "label": "搜索查询",
            "description": "要在 Google 上搜索的查询",
            "type": "STRING",
            "required": True,
        },
        "num_results": {
            "label": "结果数量",
            "description": "要返回的搜索结果数量",
            "type": "INT",
            "default": 10,
            "required": False,
        },
        "include_knowledge_graph": {
            "label": "包含知识图谱",
            "description": "是否在结果中包含知识图谱数据",
            "type": "BOOL",
            "default": True,
            "required": False,
        },
        "include_related_questions": {
            "label": "包含相关问题",
            "description": "是否在结果中包含相关问题",
            "type": "BOOL",
            "default": True,
            "required": False,
        },
        "include_shopping_results": {
            "label": "包含购物结果",
            "description": "是否在结果中包含购物结果",
            "type": "BOOL",
            "default": False,
            "required": False,
        },
        "gl": {
            "label": "地理位置",
            "description": "两字母国家代码，例如 'us'（美国）、'uk'（英国）、'cn'（中国）",
            "type": "STRING",
            "default": "us",
            "required": False,
        },
        "hl": {
            "label": "语言",
            "description": "搜索界面的语言代码，例如 'en'（英文）、'zh-cn'（简体中文）",
            "type": "STRING",
            "default": "en",
            "required": False,
        },
        "api_key": {
            "label": "API 密钥",
            "description": "SerpAPI 密钥（如未提供则使用环境变量）",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "organic_results": {
            "label": "有机搜索结果",
            "description": "Google 有机搜索结果列表",
            "type": "STRING",
        },
        "knowledge_graph": {
            "label": "知识图谱",
            "description": "知识图谱数据（如果可用且已启用）",
            "type": "STRING",
        },
        "related_questions": {
            "label": "相关问题",
            "description": "Google 相关问题列表（如果已启用）",
            "type": "STRING",
        },
        "shopping_results": {
            "label": "购物结果",
            "description": "购物结果列表（如果可用且已启用）",
            "type": "STRING",
        },
        "success": {
            "label": "成功状态",
            "description": "操作是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果操作失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            query = node_inputs.get("query", "")
            num_results = node_inputs.get("num_results", 10)
            include_knowledge_graph = node_inputs.get("include_knowledge_graph", True)
            include_related_questions = node_inputs.get("include_related_questions", True)
            include_shopping_results = node_inputs.get("include_shopping_results", False)
            gl = node_inputs.get("gl", "us")
            hl = node_inputs.get("hl", "en")
            api_key = node_inputs.get("api_key", None) or getenv("SERP_API_KEY")
            
            # 验证必填参数
            if not query:
                logger.error("No search query provided")
                return {
                    "success": False,
                    "error_message": "No search query provided",
                    "organic_results": "[]",
                    "knowledge_graph": "{}",
                    "related_questions": "[]",
                    "shopping_results": "[]"
                }
            
            if not api_key:
                logger.error("No SerpAPI key provided (neither in inputs nor as environment variable)")
                return {
                    "success": False,
                    "error_message": "No SerpAPI key provided",
                    "organic_results": "[]",
                    "knowledge_graph": "{}",
                    "related_questions": "[]",
                    "shopping_results": "[]"
                }
            
            logger.info(f"Searching Google via SerpAPI for: {query}")
            start_time = time.time()
            
            # 准备搜索参数
            search_params = {
                "q": query,
                "num": num_results,
                "gl": gl,
                "hl": hl,
                "api_key": api_key
            }
            
            # 执行搜索
            try:
                search = GoogleSearch(search_params)
                search_results = search.get_dict()
                
                # 提取和处理结果
                organic_results = search_results.get("organic_results", [])
                knowledge_graph = search_results.get("knowledge_graph", {})
                related_questions = search_results.get("related_questions", [])
                shopping_results = search_results.get("shopping_results", [])
                
                # 过滤不需要的结果
                if not include_knowledge_graph:
                    knowledge_graph = {}
                
                if not include_related_questions:
                    related_questions = []
                
                if not include_shopping_results:
                    shopping_results = []
                
                # 转换为JSON字符串
                organic_results_json = json.dumps(organic_results, ensure_ascii=False, indent=2)
                knowledge_graph_json = json.dumps(knowledge_graph, ensure_ascii=False, indent=2)
                related_questions_json = json.dumps(related_questions, ensure_ascii=False, indent=2)
                shopping_results_json = json.dumps(shopping_results, ensure_ascii=False, indent=2)
                
                elapsed = time.time() - start_time
                result_count = len(organic_results)
                logger.info(f"Found {result_count} organic results in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "organic_results": organic_results_json,
                    "knowledge_graph": knowledge_graph_json,
                    "related_questions": related_questions_json,
                    "shopping_results": shopping_results_json,
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error searching Google via SerpAPI: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "organic_results": "[]",
                    "knowledge_graph": "{}",
                    "related_questions": "[]",
                    "shopping_results": "[]"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in SerpAPI Google Search node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "organic_results": "[]",
                "knowledge_graph": "{}",
                "related_questions": "[]",
                "shopping_results": "[]"
            }


# Test code (runs when this file is executed directly)
if __name__ == "__main__":
    import asyncio
    import os
    
    # Create a simple logger for testing
    class SimpleLogger:
        @staticmethod
        def info(msg): print(f"INFO: {msg}")
        @staticmethod
        def error(msg): print(f"ERROR: {msg}")
        @staticmethod
        def warning(msg): print(f"WARNING: {msg}")
        @staticmethod
        def debug(msg): print(f"DEBUG: {msg}")
    
    logger = SimpleLogger()
    
    # Test SerpApiGoogleSearchNode
    print("\nTesting SerpApiGoogleSearchNode:")
    node = SerpApiGoogleSearchNode()
    
    # Note: This would make an actual API call, so we'll just print example output
    print("Example output would be:")
    print("{\n  \"success\": true,\n  \"organic_results\": \"[...]\"\n}")
    
    # Uncomment to test with your API key
    # api_key = os.environ.get("SERP_API_KEY", "")
    # if api_key:
    #     result = asyncio.run(node.execute({
    #         "query": "Python programming",
    #         "num_results": 5,
    #         "include_knowledge_graph": True,
    #         "api_key": api_key
    #     }, logger))
    #     print(f"Success: {result['success']}")
    #     print(f"Organic results: {result['organic_results'][:100]}...")
    # else:
    #     print("SERP_API_KEY not found in environment variables") 