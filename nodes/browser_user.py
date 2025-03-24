import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"

try:
    from autotask.nodes import Node, register_node
    from autotask.api_keys import get_api_key
except ImportError:
    from stub import Node, register_node, get_api_key

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio




@register_node
class BrowserUserNode(Node):
    NAME = "Browser User"
    DESCRIPTION = "Execute browser automation tasks using LLM agent"

    INPUTS = {
        "task": {
            "label": "Task Description",
            "description": "The task to be performed by the browser agent",
            "type": "STRING",
            "required": True,
        },
        "model": {
            "label": "LLM Model",
            "description": "The language model to use (e.g. gpt-4, gpt-3.5-turbo)",
            "type": "STRING",
            "default": "deepseek-chat",
            "required": True,
        },
        "base_url": {
            "label": "API Base URL",
            "description": "The base URL for API requests",
            "type": "STRING",
            "default": "https://api.deepseek.com/v1",
            "required": True,
        },
        "api_key": {
            "label": "API Key",
            "description": "The API key for authentication",
            "type": "STRING",
            "required": True,
        },
        "temperature": {
            "label": "Temperature",
            "description": "Sampling temperature for the LLM",
            "type": "FLOAT",
            "default": 0.7,
            "required": False,
        }
    }

    OUTPUTS = {
        "result": {
            "label": "Task Result",
            "description": "The result of the browser automation task",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the task was completed successfully",
            "type": "BOOLEAN",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            # Get input parameters
            task = node_inputs["task"]
            model = node_inputs.get("model", "deepseek-chat")
            base_url = node_inputs.get("base_url", "https://api.deepseek.com/v1")
            api_key = node_inputs.get("api_key", "sk-21cd4714e35c4528aeb413834f72401d")
            temperature = node_inputs.get("temperature", 0.7)

            workflow_logger.info(f"Starting browser task: {task}")
            workflow_logger.info(f"Using model: {model}")

            # Create LLM instance
            llm = ChatOpenAI(
                api_key=api_key,
                model=model,
                temperature=temperature,
                base_url=base_url
            )

            # 创建并运行代理
            agent = Agent(
                task=task,
                llm=llm,
                use_vision=False
            )

            # 执行任务
            response = await agent.run()

            workflow_logger.info("Browser task completed successfully")
            
            

            return {
                "success": True,
                "result": response.final_result()
            }

        except Exception as e:
            error_msg = f"Browser task failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }

    def cleanup(self):
        """清理资源"""
        try:
            # 在这里添加任何需要的清理代码
            pass
        except Exception as e:
            self.workflow_logger.error(f"Cleanup failed: {str(e)}")