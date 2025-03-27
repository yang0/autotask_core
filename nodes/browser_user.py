import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"

try:
    from autotask.nodes import Node, register_node
    from autotask.api_keys import get_api_key
except ImportError:
    from stub import Node, register_node, get_api_key

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserContextConfig, Browser
from browser_use.browser.context import BrowserContext
import traceback
import json
import tempfile


API_KEY = get_api_key(provider="browser_use", key_name="API_KEY")
MODEL = get_api_key(provider="browser_use", key_name="MODEL")
BASE_URL = get_api_key(provider="browser_use", key_name="BASE_URL")


@register_node
class BrowserUserNode(Node):
    NAME = "Browser User"
    DESCRIPTION = "Execute browser automation tasks using LLM agent"

    # 添加类变量
    _agent = None
    _temp_cookie_file = None

    INPUTS = {
        "task": {
            "label": "Task Description",
            "description": "The task to be performed by the browser agent",
            "type": "STRING",
            "required": True,
        },
        "cookie_file": {
            "label": "Cookie File",
            "description": "Path to the cookie file for browser authentication",
            "type": "STRING",
            "required": False,
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

    def _process_cookie_file(self, cookie_file: str) -> str:
        """Process the cookie file and extract cookies if needed.
        
        Args:
            cookie_file: Path to the original cookie file
            
        Returns:
            str: Path to the processed cookie file
        """
        try:
            if not cookie_file or not os.path.exists(cookie_file):
                return None

            with open(cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict) or 'cookies' not in data:
                return cookie_file
                
            cookies_data = data['cookies']
            if not isinstance(cookies_data, list):
                return cookie_file

            # Create a temporary file for the cookies
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
            self._temp_cookie_file = temp_file.name
            
            # Write the cookies array directly to the temporary file
            with open(temp_file.name, 'w', encoding='utf-8') as f:
                json.dump(cookies_data, f, indent=2)
                
            return temp_file.name
                
        except Exception as e:
            self.workflow_logger.error(f"Error processing cookie file: {str(e)}")
            return cookie_file

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            # Get input parameters
            task = node_inputs["task"]
            cookie_file = node_inputs.get("cookie_file")
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
            
            config = BrowserContextConfig(
                        maximum_wait_page_load_time=15.0,
                    )
            
            if cookie_file and os.path.exists(cookie_file):
                workflow_logger.info(f"Using cookie file: {cookie_file}")
                # Process the cookie file
                processed_cookie_file = self._process_cookie_file(cookie_file)
                workflow_logger.info(f"Using processed cookie file: {processed_cookie_file}")
                
                if processed_cookie_file:
                    config = BrowserContextConfig(
                        maximum_wait_page_load_time=15.0,
                        cookies_file=processed_cookie_file,
                    )
                    
            context = BrowserContext(browser=Browser(), config=config)

            # 创建并运行代理
            BrowserUserNode._agent = Agent(
                task=task,
                llm=llm,
                use_vision=use_vision,
                browser_context=context
            )

            # 执行任务
            response = await BrowserUserNode._agent.run()

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
        finally:
            # Cleanup temporary cookie file if it exists
            if self._temp_cookie_file and os.path.exists(self._temp_cookie_file):
                try:
                    os.unlink(self._temp_cookie_file)
                    self._temp_cookie_file = None
                except Exception as e:
                    workflow_logger.error(f"Error cleaning up temporary cookie file: {str(e)}")

    async def stop(self) -> None:
        """Stop the browser agent when interrupted"""
        try:
            if BrowserUserNode._agent:
                BrowserUserNode._agent.stop()
        except Exception as e:
            traceback.print_exc()

    def cleanup(self):
        """清理资源"""
        try:
            # Clean up temporary cookie file if it exists
            if self._temp_cookie_file and os.path.exists(self._temp_cookie_file):
                os.unlink(self._temp_cookie_file)
                self._temp_cookie_file = None
            # 在这里添加任何需要的清理代码
            BrowserUserNode._agent = None
        except Exception as e:
            traceback.print_exc()