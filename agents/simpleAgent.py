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
    LLM_NAME = "deepseek-chat"
    TAGS = ["text", "llm", "basic"]
    
    def client(self):
        """获取客户端实例"""
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=self.get_api_key(),
            base_url=self.get_api_url()
        )

    async def query(self, messages: List[Dict[str, str]]) -> Any:
        """执行单次查询"""
        return await self.client().chat.completions.create(
            model=self.get_llm_name(),
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            stream=False
        )

    async def stream(self, messages: List[Dict[str, str]]):
        """执行流式查询"""
        logger.info(f"Stream query: {messages}")
        return await self.client().chat.completions.create(
            model=self.get_llm_name(),
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            stream=True
        )