from langgraph.graph import StateGraph, START, END
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Literal, Union, TypedDict, cast
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from langgraph.types import Command
from typing_extensions import TypedDict


from autotask.assistant.graph_assistant import GraphAssistant
from autotask.assistant.assistant_registry import AssistantRegistry
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)


    
@AssistantRegistry.register(
    name="ReActAssistant",
    description="A reAct assistant that can handle most tasks"
)
class ReActAssistant(GraphAssistant):
    

    def build(self):
        return create_react_agent(
            self.main_llm,
            tools=list(self.tools.values()),
            prompt=self.main_agent_config.system_message
        )


