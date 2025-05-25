from langgraph.graph import StateGraph, START, END
import logging
from typing import Dict, Set

from autotask.assistant.graph_assistant import GraphAssistant
from autotask.assistant.assistant_registry import AssistantRegistry
from autotask.assistant.graph_manager import get_graph
from autotask.assistant.assistant_config import assistant_config_manager
from .types import State
import traceback
try:
    from .nodes import (
        coordinator_node,
        background_investigation_node,
        planner_node,
        human_feedback_node,
        research_team_node,
        reporter_node,
    )
except Exception as e:
    traceback.print_exc()

logger = logging.getLogger(__name__)

@AssistantRegistry.register(
    name="ResearchAssistant",
    description="A research assistant that can handle most tasks"
)
class ResearchAssistant(GraphAssistant):
    CONFIG = {
        "max_plan_iterations": {
            "type": "INT",
            "description": "Maximum number of plan iterations",
            "required": True,
            "default": 1,
            "label": "最大迭代次数"
        },
        "max_step_num": {
            "type": "INT",
            "description": "Maximum number of steps in a plan",
            "required": True,
            "default": 3,
            "label": "最大步骤数"
        },
        "max_search_results": {
            "type": "INT",
            "description": "Maximum number of search results",
            "required": True,
            "default": 3,
            "label": "最大搜索结果数"
        }
    }

    def build(self):
        """Build the research assistant workflow graph."""
        builder = StateGraph(State)
        
        # Add edge from START to coordinator first
        builder.add_edge(START, "coordinator")
        
        # Add core nodes
        builder.add_node("coordinator", coordinator_node)
        builder.add_node("background_investigator", background_investigation_node)
        builder.add_node("planner", planner_node)
        builder.add_node("reporter", reporter_node)
        builder.add_node("research_team", research_team_node)
        builder.add_node("human_feedback", human_feedback_node)
        
        # Add team members and collect their types
        team_members = {}
        step_types = set()
        for member in self.team:
            graph = get_graph(member)
            assistant_config = assistant_config_manager().get_assistant_config(member)
            assistant_name = assistant_config.name
            member_type = assistant_config.type or "research"  # Default to research if type not specified
            team_members[assistant_name] = member_type
            step_types.add(member_type)
            builder.add_node(assistant_name, graph)
            
        # Add edge to END
        builder.add_edge("reporter", END)
        
        # Update initial state with team members, step types and LLMs
        initial_state = {
            "team_members": team_members,
            "step_types": step_types,
            "main_llm": self.main_llm,  # Add main LLM to state
            "reasoning_llm": self.reasoning_llm  # Add reasoning LLM to state
        }
        
        return builder.compile(initial_state=initial_state)


