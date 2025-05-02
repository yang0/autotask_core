from typing import Dict, List

class TeamGraphBuilder(BaseGraphBuilder):
    def __init__(self, assistant):
        super().__init__(assistant)
        self.tools_nodes: Dict[str, str] = {}  # 存储 member_name -> tools_node_name 的映射
    
    def get_team_members(self) -> List:
        from autotask.assistant.graph_assistant import GraphAssistant
        from autotask.assistant.assistant_registry import AssistantRegistry
        assistant_registry = AssistantRegistry.get_instance()
        return [self.assistant] + [assistant_registry.get_assistant(mid) for mid in self.assistant.team]
    
    def get_tools_node_name(self, member_name: str) -> str:
        return f"tools_{member_name}"
    
    async def team_supervisor_node(self, state):
        from langgraph.types import Command
        from langchain_core.messages import SystemMessage
        # ... existing code ...
    async def team_member_node(self, member_name: str, state):
        from langgraph.types import Command
        from langchain_core.messages import HumanMessage
        # ... existing code ...
    def add_nodes(self, graph_builder):
        from langgraph.prebuilt import ToolNode
        # ... existing code ...
    def add_edges(self, graph_builder):
        from langgraph.graph import START, END
        from langgraph.prebuilt import tools_condition
        # ... existing code ... 