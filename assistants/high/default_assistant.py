from langgraph.graph import StateGraph, START, END
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Literal, Union, TypedDict, cast
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from langgraph.types import Command
from typing_extensions import TypedDict
from typing import List, Optional, Literal
from langchain_core.language_models.chat_models import BaseChatModel
import json
import re

from langgraph.graph import StateGraph, MessagesState, START, END
class State(MessagesState):
    next: str


from autotask.assistant.graph_assistant import GraphAssistant
from autotask.assistant.assistant_registry import AssistantRegistry
from autotask.assistant.graph_manager import get_graph
from autotask.assistant.assistant_config import assistant_config_manager


logger = logging.getLogger(__name__)


def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH.\n\n"
        "You must respond with a JSON object containing a single field 'next' "
        f"with one of these values: {options}. Example: {{\"next\": \"FINISH\"}}"
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the"
            f" following workers: {members}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished," 
            " respond with FINISH.\n\n"
            "You must respond with a JSON object containing a single field 'next' "
            f"with one of these values: {options}. Example: {{\"next\": \"FINISH\"}}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        
        try:
            # 尝试使用structured_output（如果模型支持）
            response = llm.with_structured_output(Router).invoke(messages)
            goto = response["next"]
        except:
            # 备选方案：直接调用模型并解析响应
            raw_response = llm.invoke(messages)
            content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            
            try:
                # 尝试从响应中提取JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    response_dict = json.loads(json_str)
                    goto = response_dict.get("next", "FINISH")
                else:
                    # 如果没找到JSON，检查是否直接提到了成员名或FINISH
                    for name in options:
                        if name in content:
                            goto = name
                            break
                    else:
                        logger.warning(f"无法从响应中解析出成员名称: {content}")
                        goto = "FINISH"
            except Exception as e:
                logger.error(f"解析响应失败: {str(e)}, 内容: {content}")
                goto = "FINISH"
        
        if goto == "FINISH":
            goto = END
            
        return Command(goto=goto, update={"next": goto})

    return supervisor_node


    
@AssistantRegistry.register(
    name="DefaultAssistant",
    description="A default assistant that can handle most tasks"
)
class DefaultAssistant(GraphAssistant):
       

    def build(self):
        graph_builder = StateGraph(State)
        member_names = []
        for member in self.team:
            graph = get_graph(member)
            assistant_config = assistant_config_manager().get_assistant_config(member)
            assistant_name = assistant_config.name
            member_names.append(assistant_name)
            graph_builder.add_node(assistant_name, graph)

        supervisor_node = make_supervisor_node(self.main_llm, member_names)
        graph_builder.add_node("supervisor", supervisor_node)

        graph_builder.add_edge(START, "supervisor")

        return graph_builder.compile()


