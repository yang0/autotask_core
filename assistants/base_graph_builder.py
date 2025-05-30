from abc import ABC, abstractmethod
import traceback
from ..logger import logger

class BaseGraphBuilder(ABC):
    def __init__(self, assistant):
        self.assistant = assistant        

    @abstractmethod
    def add_nodes(self, graph_builder):
        """添加节点到图中"""
        pass
        
    @abstractmethod
    def add_edges(self, graph_builder):
        """添加边到图中"""
        pass
        
    def build(self):
        """构建并返回工作流图"""
        try:
            from ..graph_state import State
            from langgraph.graph import StateGraph
            from langgraph.checkpoint.memory import MemorySaver
            graph_builder = StateGraph(State)
            # 添加节点
            self.add_nodes(graph_builder)
            # 添加边
            self.add_edges(graph_builder)
            # 创建记忆管理器并编译图
            memory = MemorySaver()
            graph = graph_builder.compile(checkpointer=memory)
            return graph
        except Exception as e:
            logger.error(f"构建图失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise 