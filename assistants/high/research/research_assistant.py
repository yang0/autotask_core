from langgraph.graph import StateGraph, START, END
import logging
from typing import Dict, Set
from langgraph.checkpoint.memory import MemorySaver

from autotask.assistant.graph_assistant import GraphAssistant
from autotask.assistant.assistant_registry import AssistantRegistry
from autotask.assistant.graph_manager import get_graph
from autotask.assistant.assistant_config import assistant_config_manager
from .types import State
import traceback
try:
    from .nodes import (
        create_coordinator_node,
        create_planner_node,
        create_reporter_node,
        background_investigation_node,
        human_feedback_node,
        research_team_node,
        _execute_agent_step,
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
        
        # Create node functions with injected dependencies
        coordinator = create_coordinator_node(self.main_llm)
        planner = create_planner_node(self.main_llm, self.reasoning_llm)
        reporter = create_reporter_node(self.main_llm)
        
        # Add core nodes
        builder.add_node("coordinator", coordinator)
        builder.add_node("background_investigator", background_investigation_node)
        builder.add_node("planner", planner)
        builder.add_node("reporter", reporter)
        builder.add_node("research_team", research_team_node)
        builder.add_node("human_feedback", human_feedback_node)
        
        # Add team members and collect their types
        for member in self.team:
            graph = get_graph(member)
            assistant_config = assistant_config_manager().get_assistant_config(member)
            assistant_name = assistant_config.name
            
            # Create a wrapper function that uses _execute_agent_step
            def create_agent_node(agent=graph, agent_name=assistant_name):
                async def agent_node(state: State):
                    return await _execute_agent_step(state, agent, agent_name)
                return agent_node
            builder.add_node(assistant_name, create_agent_node())
                       
        # Add edge to END
        builder.add_edge("reporter", END)
        
        memory = MemorySaver()
        
        return builder.compile(checkpointer=memory)


