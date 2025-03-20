from typing import Dict, Any, Optional, List
from loguru import logger
from autotask.agent.agentRegistry import AgentRegistry
from autotask.agent.agentType import (
    BaseAgent, 
)
from autotask.models.message import Message
from openai import AsyncOpenAI

@AgentRegistry.register_agent
class SimpleTextAgent(BaseAgent):
    """简单文本处理Agent"""
    NAME = "Simple Agent"
    DESCRIPTION = "处理基本的文本交互，支持多种LLM模型"

    async def query(self, messages: List[Message], stream: bool = False) -> Any:
        """执行查询
        
        Args:
            messages: 消息列表
            stream: 是否使用流式响应
            
        Returns:
            流式模式: AsyncGenerator yielding response chunks
            非流式模式: Complete response
        """        
        
        # 根据stream参数选择合适的调用方式
        if stream:
            return self.main_llm.aresponse_stream(messages)
        else:
            return self.main_llm.aresponse(messages)

    # 确保调用父类的process_model_response_stream方法
    async def process_model_response_stream(self, response_stream, assistant_message, check_interrupt=None, full_response=""):
        """调用父类的流式响应处理方法"""
        async for chunk in super().process_model_response_stream(
            response_stream=response_stream,
            assistant_message=assistant_message,
            check_interrupt=check_interrupt,
            full_response=full_response
        ):
            yield chunk

