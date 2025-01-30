import json
from typing import Dict, Any, List
from pathlib import Path

try:
    from autotask.nodes import Node, register_node
except ImportError:
    from ..stub import Node, register_node

@register_node
class AgentNode(Node):
    """Agent processing node that handles input text using configured agent"""
    
    NAME = "Agent Processor"
    DESCRIPTION = "Process input text using a selected agent"

    INPUTS = {
        "agent_id": {
            "label": "Agent",
            "description": "Select the agent to process the input",
            "type": "AGENT",
            "options": Node.get_all_configured_agents(),
            "required": True
        },
        "input_text": {
            "label": "Input Text",
            "description": "Text to be processed by the agent",
            "type": "STRING",
            "required": True
        }
    }

    OUTPUTS = {
        "output_text": {
            "label": "Output Text",
            "description": "Processed text from the agent",
            "type": "STRING"
        }
    }

    def get_inputs(self) -> Dict[str, Any]:
        """Override get_inputs to provide dynamic agent options"""
        inputs = self.INPUTS.copy()
        inputs["agent_id"] = inputs["agent_id"].copy()
        inputs["agent_id"]["options"] = Node.get_all_configured_agents()
        return inputs

    def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            workflow_logger.info("Starting agent processing")
            
            agent_id = node_inputs.get("agent_id")
            input_text = node_inputs.get("input_text", "")
            
            if not agent_id:
                raise ValueError("Agent ID is required")
            
            # 使用基类的 run_agent 方法，它会内部处理异步调用
            output_text = self.run_agent(agent_id, input_text)
            
            workflow_logger.info("Agent processing completed successfully")
            return {"output_text": output_text}

        except Exception as e:
            error_msg = f"Agent processing failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {"output_text": ""}
