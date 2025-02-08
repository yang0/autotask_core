from typing import Dict, Any, Optional, List
from loguru import logger
from autotask.agent.agentRegistry import AgentRegistry
from autotask.agent.agentType import (
    BaseAgent, 
    AgentContext
)
from openai import AsyncOpenAI

@AgentRegistry.register_agent
class SimpleTextAgent(BaseAgent):
    """简单文本处理Agent"""
    NAME = "Simple Text Agent"
    DESCRIPTION = "处理基本的文本交互，支持多种LLM模型"

    
    def client(self):
        """获取客户端实例"""
        return AsyncOpenAI(
            api_key=self.get_api_key(),
            base_url=self.get_api_url()
        )

    async def query(self, messages: List[Dict[str, str]], is_stream: bool = False, functions: List[Dict[str, Any]] = None) -> Any:
        """执行查询"""
        functions = self.get_tools_as_functions()
        
        response = await self.client().chat.completions.create(
            model=self.get_llm_name(),
            messages=messages,
            functions=functions,
            function_call="auto" if functions else None,
            temperature=0.7,
            max_tokens=1000,
            stream=is_stream
        )
        
        if is_stream:
            return response  # 返回异步生成器
        return response     # 返回完整响应
