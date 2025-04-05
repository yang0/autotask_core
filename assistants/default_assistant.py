from langgraph.graph import StateGraph, START, END
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Literal, Union, TypedDict, cast
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from langgraph.types import Command
from typing_extensions import TypedDict

from .graph_state import State

from autotask.assistant.graph_assistant import GraphAssistant
from autotask.assistant.assistant_registry import AssistantRegistry

logger = logging.getLogger(__name__)

class TeamRouter(TypedDict):
    """团队路由决策，决定下一步路由到哪个团队成员或结束"""
    next: str  # 这里应该用Literal但需要动态成员列表
    
@AssistantRegistry.register(
    name="DefaultAssistant",
    description="A default assistant that can handle most tasks"
)
class DefaultAssistant(GraphAssistant):
    
    def __init__(self,
                 id: str,
                 name: str,
                 description: str,
                 main_agent_config: Dict[str, Any],  # 修改为字典类型
                 reasoning_agent_config: Optional[Dict[str, Any]] = None,  # 修改为字典类型
                 enable_reasoning: bool = True,
                 max_steps: int = 5,
                 team: List[str] = None,
                 config: Dict[str, Any] = None,
                 class_path: str = "",
                 knowledge_bases: Optional[List[Dict[str, Any]]] = None):
        super().__init__(id, name, description, main_agent_config, reasoning_agent_config, 
                        enable_reasoning, max_steps, team, config, class_path, knowledge_bases)
        
        # 初始化LLM配置
        self.main_llm_config = main_agent_config
        self.reasoning_llm_config = reasoning_agent_config
        
    async def main_agent_node(self, state: State):
        """主agent节点处理函数"""
        if state.should_stop:
            return {"messages": [AIMessage(content="task is stopped by user")]}
        messages = [SystemMessage(content=self.main_agent_config.system_message)] + state.messages
        messages = self.trunc_messages(messages)  # 添加这行来截断消息        
        response = await self.main_llm.ainvoke(messages)
        return {"messages": [response]}
        
    async def reasoning_agent_node(self, state: State):
        """推理agent节点处理函数"""
        if state.should_stop:
            return {"messages": [AIMessage(content="task is stopped by user")]}
        messages = [SystemMessage(content=self.reasoning_agent_config.system_message)] + state.messages
        messages = self.trunc_messages(messages)  # 添加这行来截断消息        
        response = await self.reasoning_llm.ainvoke(messages)
        return {"messages": [response]}

    def build(self):
        """构建工作流图"""
        from .builders.basic_graph_builder import BasicGraphBuilder
        from .builders.team_graph_builder import TeamGraphBuilder
        
        if self.team and len(self.team) > 0:
            builder = TeamGraphBuilder(self)
        else:
            builder = BasicGraphBuilder(self)
        
        return builder.build()


