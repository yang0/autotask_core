from typing import Dict, Any, List, Optional
from loguru import logger
from autotask.agent.agentRegistry import AgentRegistry
from autotask.agent.agentType import BaseAgent, AgentContext
from openai import AsyncOpenAI
import json

@AgentRegistry.register_agent
class FunctionCallAgent(BaseAgent):
    """支持Function Calling的Agent"""
    NAME = "Function Call Agent"
    DESCRIPTION = "支持工具调用的智能助手，可以通过调用各种工具来完成任务"
    LLM_NAME = "deepseek-chat"
    TAGS = ["function_calling", "tool", "assistant"]
    
    def client(self):
        """获取客户端实例"""
        return AsyncOpenAI(
            api_key=self.get_api_key(),
            base_url=self.get_api_url()
        )

    async def query(self, messages: List[Dict[str, str]]) -> Any:
        """执行单次查询，支持function calling"""
        functions = self.get_tools_as_functions()
        
        response = await self.client().chat.completions.create(
            model=self.get_llm_name(),
            messages=messages,
            functions=functions,
            function_call="auto" if functions else None,
            temperature=0.7,
            max_tokens=1000,
            stream=False
        )
        
        # 处理function calling响应
        message = response.choices[0].message
        if hasattr(message, 'function_call') and message.function_call:
            function_result = await self.handle_function_call(message.function_call)
            
            # 将函数调用结果添加到消息历史
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments
                }
            })
            messages.append({
                "role": "function",
                "name": message.function_call.name,
                "content": json.dumps(function_result, ensure_ascii=False)
            })
            
            # 让模型解释函数调用结果
            return await self.client().chat.completions.create(
                model=self.get_llm_name(),
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=False
            )
            
        return response

    async def stream(self, messages: List[Dict[str, str]]):
        """执行流式查询，支持function calling"""
        logger.info(f"Stream query: {messages}")
        
        # 添加系统提示词到消息列表
        system_prompt = self.get_formatted_system_prompt()
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
            
        # 获取工具函数定义
        functions = self.get_tools_as_functions()
        logger.info(f"Using functions: {functions}")
        
        # 用于收集function calling的信息
        current_function_call = {
            "name": None,
            "arguments": ""
        }
        
        response_stream = await self.client().chat.completions.create(
            model=self.get_llm_name(),
            messages=messages,
            functions=functions,
            function_call="auto" if functions else None,
            temperature=0.7,
            max_tokens=1000,
            stream=True
        )
        
        # 处理流式响应
        async for chunk in response_stream:
            delta = chunk.choices[0].delta
            
            # 处理function calling
            if hasattr(delta, 'function_call'):
                function_call = delta.function_call
                
                # 收集函数名
                if hasattr(function_call, 'name') and function_call.name:
                    current_function_call["name"] = function_call.name
                    yield {
                        "type": "function_call_start",
                        "name": function_call.name
                    }
                    
                # 收集参数
                if hasattr(function_call, 'arguments') and function_call.arguments:
                    current_function_call["arguments"] += function_call.arguments
                    yield {
                        "type": "function_args",
                        "arguments": function_call.arguments
                    }
                    
                # 如果是最后一个chunk，执行函数调用
                if chunk.choices[0].finish_reason == "function_call":
                    # 执行函数调用
                    if current_function_call["name"] and current_function_call["arguments"]:
                        try:
                            # 构造function call对象
                            complete_function_call = type('FunctionCall', (), {
                                'name': current_function_call["name"],
                                'arguments': current_function_call["arguments"]
                            })
                            
                            # 执行函数调用
                            function_result = await self.handle_function_call(complete_function_call)
                            
                            # 将函数调用结果添加到消息历史
                            messages.append({
                                "role": "assistant",
                                "content": None,
                                "function_call": current_function_call
                            })
                            messages.append({
                                "role": "function",
                                "name": current_function_call["name"],
                                "content": json.dumps(function_result, ensure_ascii=False)
                            })
                            
                            # 发送函数执行结果
                            yield {
                                "type": "function_result",
                                "name": current_function_call["name"],
                                "result": function_result
                            }
                            
                            # 让模型解释函数调用结果
                            explanation_response = await self.client().chat.completions.create(
                                model=self.get_llm_name(),
                                messages=messages,
                                temperature=0.7,
                                max_tokens=1000,
                                stream=True
                            )
                            
                            # 流式返回解释
                            async for explanation_chunk in explanation_response:
                                if hasattr(explanation_chunk.choices[0].delta, 'content'):
                                    content = explanation_chunk.choices[0].delta.content
                                    if content:
                                        yield {
                                            "type": "content",
                                            "content": content
                                        }
                                        
                        except Exception as e:
                            logger.error(f"Error in function execution: {str(e)}")
                            yield {
                                "type": "error",
                                "message": f"Function execution failed: {str(e)}"
                            }
                            
                    # 重置function call信息
                    current_function_call = {"name": None, "arguments": ""}
                    
            # 处理普通文本内容
            elif hasattr(delta, 'content') and delta.content:
                yield {
                    "type": "content",
                    "content": delta.content
                }

    async def handle_function_call(self, function_call: Any) -> Dict[str, Any]:
        """处理函数调用"""
        try:
            function_name = function_call.name
            arguments = json.loads(function_call.arguments)
            
            logger.info(f"Calling function {function_name} with arguments: {arguments}")
            
            # 执行工具函数
            tool = self.get_tool(function_name)
            if not tool:
                return {
                    "status": "error",
                    "message": f"Tool {function_name} not found"
                }
                
            result = await tool.run(**arguments)
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing function: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """获取工具实例"""
        tools = self.get_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

