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
    LLM_NAME = "deepseek-chat"  # 默认使用 deepseek-chat 模型
    
    INPUTS = {
        "text": {
            "label": "输入文本",
            "description": "需要处理的文本内容",
            "type": "STRING",
            "required": True
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "处理结果",
            "description": "处理后的文本结果",
            "type": "STRING"
        },
        "tokens_used": {
            "label": "使用的Token数",
            "description": "处理过程中使用的token数量",
            "type": "INTEGER"
        }
    }
    
    TAGS = ["text", "llm", "basic"]
    
    
    async def initialize(self) -> None:
        """初始化Agent"""
        from openai import AsyncOpenAI
        
        logger.info(f"Initialized {self.NAME} with model: {self.llm_name}")
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.url
        )
    
    def _prepare_prompt(self, text: str) -> str:
        """准备提示文本"""
        return text
    
    async def process_input(self, 
                          text: str,
                          context: AgentContext,
                          is_conversation: bool = False) -> Dict[str, Any]:
        """处理输入"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        try:
            # 准备消息列表
            messages = []
            
            if is_conversation:
                # 添加历史对话记录
                history = self.memory.get_conversation_context(window_size=5)
                if history:
                    for msg in history:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # 添加当前用户输入
            messages.append({
                "role": "user",
                "content": self._prepare_prompt(text)
            })
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(
                model=self.llm_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            result = {
                "result": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens
            }
            
            if is_conversation:
                # 记录到对话历史
                await self.memory.conversation.add_interaction(text, result["result"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing input with {self.NAME}: {str(e)}")
            raise
