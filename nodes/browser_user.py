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

API_KEY = get_api_key(provider="browser_use", key_name="API_KEY")
MODEL = get_api_key(provider="browser_use", key_name="MODEL")
BASE_URL = get_api_key(provider="browser_use", key_name="BASE_URL")


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
        "use_vision": {
            "label": "Use Vision",
            "description": "Whether to use vision",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
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
            temperature = node_inputs.get("temperature", 0.7)
            use_vision = node_inputs.get("use_vision", False)

            workflow_logger.info(f"Starting browser task: {task}")

            # Create LLM instance
            llm = ChatOpenAI(
                api_key=API_KEY,
                model=MODEL,
                temperature=temperature,
                base_url=BASE_URL
            )

            # 创建并运行代理
            agent = Agent(
                task=task,
                llm=llm,
                use_vision=use_vision
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
                "result": error_msg
            }

    def cleanup(self):
        """清理资源"""
        try:
            # 在这里添加任何需要的清理代码
            pass
        except Exception as e:
            self.workflow_logger.error(f"Cleanup failed: {str(e)}")