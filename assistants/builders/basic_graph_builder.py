from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from .base_graph_builder import BaseGraphBuilder
from ..graph_state import State

class BasicGraphBuilder(BaseGraphBuilder):
        
    def add_nodes(self, graph_builder: StateGraph) -> None:
        # 添加主agent节点
        graph_builder.add_node("main_agent", self.assistant.main_agent_node)
        
        # 添加推理节点
        if self.assistant.reasoning_llm:
            graph_builder.add_node("reasoning_agent", self.assistant.reasoning_agent_node)
            
        # 添加工具节点
        if self.assistant.tools and len(self.assistant.tools) > 0:
            tools_node = ToolNode(tools=self.assistant.tools.values())
            graph_builder.add_node("tools", tools_node)
            
    def add_edges(self, graph_builder: StateGraph) -> None:
        # 添加起始边
        if self.assistant.reasoning_llm:
            graph_builder.add_edge(START, "reasoning_agent")
            graph_builder.add_edge("reasoning_agent", "main_agent")
        else:
            graph_builder.add_edge(START, "main_agent")
        
        # 添加工具相关边
        if self.assistant.tools and len(self.assistant.tools) > 0:
            graph_builder.add_edge("tools", "main_agent")
            graph_builder.add_conditional_edges(
                "main_agent",
                tools_condition
            )
        else:
            graph_builder.add_edge("main_agent", END) 