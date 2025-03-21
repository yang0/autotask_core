from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from .base_graph_builder import BaseGraphBuilder
from autotask.assistant.assistant_registry import AssistantRegistry
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, TypedDict, Dict
from ..graph_state import State
from loguru import logger
from autotask.assistant.graph_assistant import GraphAssistant

class TeamGraphBuilder(BaseGraphBuilder):
    def __init__(self, assistant):
        super().__init__(assistant)
        self.tools_nodes: Dict[str, str] = {}  # 存储 member_name -> tools_node_name 的映射
    
    def get_team_members(self) -> List[GraphAssistant]:
        """获取团队成员"""
        assistant_registry = AssistantRegistry.get_instance()
        return [self.assistant] + [assistant_registry.get_assistant(mid) for mid in self.assistant.team]
    
    def get_tools_node_name(self, member_name: str) -> str:
        """获取成员对应的工具节点名称"""
        return f"tools_{member_name}"
    
    # 定义Nodes
    async def team_supervisor_node(self, state: State):
        """团队主管节点，决定下一步路由到哪个团队成员或结束任务"""
        if state.should_stop:
            goto = "__end__"
            return Command(goto=goto, update={"next": goto})
        # 获取团队成员信息
        assistant_registry = AssistantRegistry.get_instance()
        team_info = []
        
        # 添加主agent作为团队成员
        first_line = self.assistant.main_agent_config.system_message.split(chr(10))[0]
        team_info.append(f"{self.assistant.name}: {first_line}")
        
        # 添加其他团队成员
        available_members = self.get_team_members()
        for member in available_members:
            if member:
                first_line = member.main_agent_config.system_message.split(chr(10))[0]
                team_info.append(f"{member.name}: {first_line}")
        member_names = [m.name for m in available_members]
        
        
        system_prompt = (
            "你是一个团队协调者，负责根据任务需求分配最合适的团队成员处理。\n"
            f"可用的团队成员: {', '.join(member_names)}。\n"
            "每个成员的专长如下:\n"
            f"{chr(10).join(team_info)}\n\n"  # 使用chr(10)替代直接的换行符
            "分析当前任务和对话状态，选择一个最合适的成员处理，或者如果任务已完成回复FINISH。"
            "始终选择最专业的成员来处理特定任务。"
            "请以JSON格式返回决策，必须包含next字段，例如：{\"next\": \"成员名称\"} 或 {\"next\": \"FINISH\"}"
        )
        
        system_message = SystemMessage(content=system_prompt)
        messages = [system_message] + state.messages.copy()
        
        # 定义通用的响应解析函数
        class DynamicRouter(TypedDict):
            next: str  # 成员名称或FINISH
        
        try:
            # 尝试使用structured_output（如果模型支持）
            response = await self.assistant.main_llm.with_structured_output(DynamicRouter).ainvoke(messages)
            selected_name = response["next"]
        except:
            # 备选方案：直接调用模型并解析JSON响应
            import json
            import re
            
            # 如果模型不支持structured_output，直接调用
            raw_response = await self.assistant.main_llm.ainvoke(messages)
            content = raw_response.content
            
            try:
                # 尝试从响应中提取JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    response_dict = json.loads(json_str)
                    selected_name = response_dict.get("next", "supervisor")
                else:
                    # 如果没找到JSON，检查是否直接提到了成员名或FINISH
                    for name in member_names + ["FINISH"]:
                        if name in content:
                            selected_name = name
                            break
                    else:
                        logger.warning(f"无法从响应中解析出成员名称: {content}")
                        selected_name = "supervisor"
            except Exception as e:
                logger.error(f"解析响应失败: {str(e)}, 内容: {content}")
                selected_name = "supervisor"
        
        if selected_name == "FINISH":
            goto = "__end__"
        else:
            # 通过名称查找对应的member_id
            for member_name in member_names:
                if member_name == selected_name:
                    goto = member_name
                    break
            else:
                logger.warning(f"无效的团队成员名称: {selected_name}，默认路由到supervisor")
                goto = "supervisor"
        
        return Command(goto=goto, update={"next": goto})


    async def team_member_node(self, member_name: str, state: State):
        """团队成员节点处理函数"""
        if state.should_stop:
            goto = "__end__"
            return Command(goto=goto, update={"next": goto})
        member = None
        for m in self.get_team_members():
            if m.name == member_name:
                member = m
                break
        
        if not member:
            logger.error(f"找不到团队成员: {member_name}")
            return Command(goto="supervisor", update={"next": "supervisor"})
        
        # 调用团队成员的主agent处理函数
        result = await member.main_agent_node(state)
        
        # 添加团队成员签名到消息中
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if last_message.tool_calls and len(last_message.tool_calls) > 0:
                next = self.get_tools_node_name(member_name)
                return Command(
                    goto=next,
                    update={"messages": [last_message], "next": next}
                )
            else:
                content = f"{member_name}: {last_message.content}"
                new_message = HumanMessage(content=content, name=member_name)
                
                return Command(
                    goto="supervisor", 
                    update={"messages": [new_message], "next": "supervisor"}
                )
        
        return Command(goto="supervisor", update={"next": "supervisor"})


    # 添加nodes============================================================================================    # 
    
    def add_nodes(self, graph_builder: StateGraph) -> None:
        # 添加推理节点
        if self.assistant.reasoning_llm:
            graph_builder.add_node("reasoning_agent", self.assistant.reasoning_agent_node)
        
        # 添加supervisor节点
        graph_builder.add_node("supervisor", self.team_supervisor_node)
        
        # 为每个团队成员添加节点和对应的工具节点
        for member in self.get_team_members():
            # 添加成员节点
            async def member_handler(state, m=member):
                return await self.team_member_node(m.name, state)
            graph_builder.add_node(member.name, member_handler)
            
            # 如果成员有工具，添加对应的工具节点
            if member.tools and len(member.tools) > 0:
                tools_node_name = self.get_tools_node_name(member.name)
                tools_node = ToolNode(tools=member.tools.values())
                graph_builder.add_node(tools_node_name, tools_node)
                self.tools_nodes[member.name] = tools_node_name
            
    # 添加edges============================================================================================    # 
    def add_edges(self, graph_builder: StateGraph) -> None:
        # 添加起始边
        if self.assistant.reasoning_llm:
            graph_builder.add_edge(START, "reasoning_agent")
            graph_builder.add_edge("reasoning_agent", "supervisor")
        else:
            graph_builder.add_edge(START, "supervisor")
        
        # 为每个成员添加工具相关边
        for member in self.get_team_members():
            if member.name in self.tools_nodes:
                tools_node_name = self.tools_nodes[member.name]
                
                # 从成员节点到工具节点的条件边
                graph_builder.add_conditional_edges(
                    member.name,
                    tools_condition,
                    {
                        "tools": tools_node_name,  # 使用工具时
                        "supervisor": "supervisor",  # 不使用工具时
                        "__end__": "supervisor"
                    }
                )
                
                # 从工具节点回到成员节点
                graph_builder.add_edge(tools_node_name, member.name)
            else:
                # 如果成员没有工具，直接连接到supervisor
                graph_builder.add_edge(member.name, "supervisor")
        
        # 添加supervisor到各成员的条件边
        def route_from_supervisor(state):
            return state.next if hasattr(state, "next") and state.next else "__end__"
        
        edges = {
            **{member.name: member.name for member in self.get_team_members()},
            "__end__": END
        }
        
        graph_builder.add_conditional_edges(
            "supervisor",
            route_from_supervisor,
            edges
        ) 