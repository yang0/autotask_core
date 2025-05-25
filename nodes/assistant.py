import json
from typing import Dict, Any, List
from pathlib import Path

try:
    from autotask.nodes import Node, register_node
    from autotask.assistant.assistant_manager import run_assistant_sync
    from autotask.assistant.assistant_config import assistant_config_manager
except ImportError:
    from ..stub import Node, register_node


@register_node
class AssistantNode(Node):
    """Agent processing node that handles input text using configured agent"""

    NAME = "Assistant"
    DESCRIPTION = "Process input text using a selected assistant"

    INPUTS = {
        "assistant_id": {
            "label": "Assistant",
            "description": "Select the assistant to process the input",
            "type": "ASSISTANT",
            "required": True
        },
        "input_text": {
            "label": "Input Text",
            "description": "Text to be processed by the assistant",
            "type": "STRING",
            "required": True,
        },
    }

    OUTPUTS = {
        "output_text": {
            "label": "Output Text",
            "description": "Processed text from the assistant",
            "type": "STRING",
        }
    }

    def get_inputs(self) -> Dict[str, Any]:
        """Override get_inputs to provide dynamic agent options"""
        inputs = self.INPUTS.copy()
        inputs["assistant_id"] = inputs["assistant_id"].copy()
        inputs["assistant_id"]["options"] = Node.get_all_configured_assistants()
        return inputs

    async def execute(
        self, node_inputs: Dict[str, Any], workflow_logger
    ) -> Dict[str, Any]:
        try:
            workflow_logger.info("Starting agent processing")

            assistant_id = node_inputs.get("assistant_id")
            input_text = node_inputs.get("input_text", "")

            if not assistant_id:
                raise ValueError("Assistant ID is required")

            # 使用基类的 run_assistant 方法，它会内部处理异步调用
            output_text = await run_assistant_sync(input_text, assistant_id)

            workflow_logger.info("Assistant processing completed successfully")
            return {"output_text": output_text}

        except Exception as e:
            error_msg = f"Assistant processing failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {"output_text": ""}
