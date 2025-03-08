import json
import time
import traceback
from typing import Dict, Any, List, Optional

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger

try:
    from tavily import TavilyClient
except ImportError:
    raise ImportError("`tavily-python` not installed. Please install using `pip install tavily-python`")


@register_node
class TavilySearchNode(Node):
    """
    高级网络搜索节点，使用 Tavily 搜索引擎
    
    这个节点利用 Tavily API 提供高质量的网络搜索结果。Tavily 是一个专为 AI 应用程序设计的
    搜索引擎，提供结构化、相关的搜索结果，并且可以通过各种参数进行精细控制。这个节点
    支持基本和高级搜索模式，可以根据需要返回纯文本结果或包含摘要的结构化数据。
    
    使用场景:
    - 获取最新的网络信息和新闻
    - 执行深入的研究查询
    - 为 AI 应用提供实时数据
    - 获取带有源引用的结构化信息
    
    特点:
    - 支持不同的搜索深度（基本/高级）
    - 可选择包含 AI 生成的搜索结果摘要
    - 控制返回结果的数量
    - 提供结构化的搜索结果包括标题、URL、内容片段等
    
    注意:
    - 需要 Tavily API 密钥
    - 搜索深度会影响响应时间和结果质量
    - 高级搜索模式提供更全面但可能较慢的结果
    """
    NAME = "Tavily 搜索"
    DESCRIPTION = "使用 Tavily API 进行高级网络搜索"
    CATEGORY = "Search"
    ICON = "search"

    INPUTS = {
        "query": {
            "label": "搜索查询",
            "description": "要搜索的查询内容",
            "type": "STRING",
            "required": True,
        },
        "search_depth": {
            "label": "搜索深度",
            "description": "搜索深度（basic 或 advanced）",
            "type": "STRING",
            "default": "advanced",
            "required": False,
        },
        "max_results": {
            "label": "最大结果数",
            "description": "返回的最大结果数",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "include_answer": {
            "label": "包含摘要",
            "description": "是否包含对搜索结果的 AI 生成摘要",
            "type": "BOOL",
            "default": True,
            "required": False,
        },
        "include_raw_content": {
            "label": "包含原始内容",
            "description": "是否在结果中包含网页的原始内容",
            "type": "BOOL",
            "default": False,
            "required": False,
        },
        "api_key": {
            "label": "API 密钥",
            "description": "Tavily API 密钥（如未提供则使用环境变量）",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "search_results": {
            "label": "搜索结果",
            "description": "从 Tavily 返回的搜索结果",
            "type": "STRING",
        },
        "result_count": {
            "label": "结果数量",
            "description": "找到的结果数量",
            "type": "INT",
        },
        "answer": {
            "label": "生成的摘要",
            "description": "基于搜索结果的 AI 生成摘要（如果已启用）",
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
            search_depth = node_inputs.get("search_depth", "advanced")
            max_results = node_inputs.get("max_results", 5)
            include_answer = node_inputs.get("include_answer", True)
            include_raw_content = node_inputs.get("include_raw_content", False)
            api_key = node_inputs.get("api_key", None)
            
            # 验证必填参数
            if not query:
                logger.error("No search query provided")
                return {
                    "success": False,
                    "error_message": "No search query provided",
                    "search_results": "[]",
                    "result_count": 0,
                    "answer": ""
                }
            
            # 验证搜索深度参数
            if search_depth not in ["basic", "advanced"]:
                logger.warning(f"Invalid search_depth '{search_depth}', defaulting to 'advanced'")
                search_depth = "advanced"
            
            logger.info(f"Searching Tavily for: {query} (depth: {search_depth})")
            start_time = time.time()
            
            # 初始化 Tavily 客户端
            try:
                client = TavilyClient(api_key=api_key)
            except Exception as e:
                error_msg = f"Failed to initialize Tavily client: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "search_results": "[]",
                    "result_count": 0,
                    "answer": ""
                }
            
            # 执行搜索
            try:
                search_result = client.search(
                    query=query,
                    search_depth=search_depth,
                    max_results=max_results,
                    include_answer=include_answer,
                    include_raw_content=include_raw_content
                )
                
                # 处理结果
                if isinstance(search_result, dict):
                    results = search_result.get("results", [])
                    answer = search_result.get("answer", "")
                    result_count = len(results)
                    
                    # 格式化结果
                    results_json = json.dumps(results, ensure_ascii=False, indent=2)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"Found {result_count} results in {elapsed:.2f}s")
                    
                    return {
                        "success": True,
                        "search_results": results_json,
                        "result_count": result_count,
                        "answer": answer if include_answer else "",
                        "error_message": ""
                    }
                else:
                    error_msg = "Unexpected response format from Tavily API"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error_message": error_msg,
                        "search_results": "[]",
                        "result_count": 0,
                        "answer": ""
                    }
                
            except Exception as e:
                error_msg = f"Error searching Tavily: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "search_results": "[]",
                    "result_count": 0,
                    "answer": ""
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Tavily Search node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "search_results": "[]",
                "result_count": 0,
                "answer": ""
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
    
    # Test TavilySearchNode
    print("\nTesting TavilySearchNode:")
    node = TavilySearchNode()
    
    # Note: This would make an actual API call, so we'll just print example output
    print("Example output would be:")
    print("{\n  \"success\": true,\n  \"result_count\": 5,\n  \"answer\": \"...\"\n}")
    
    # Uncomment to test with your API key
    # api_key = os.environ.get("TAVILY_API_KEY", "")
    # if api_key:
    #     result = asyncio.run(node.execute({
    #         "query": "Latest advancements in AI research",
    #         "search_depth": "basic",
    #         "max_results": 3,
    #         "include_answer": True,
    #         "api_key": api_key
    #     }, logger))
    #     print(f"Success: {result['success']}")
    #     print(f"Results count: {result['result_count']}")
    #     print(f"Answer: {result['answer'][:100]}...")
    # else:
    #     print("TAVILY_API_KEY not found in environment variables") 