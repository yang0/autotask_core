try:
    from autotask.nodes import Node, GeneratorNode, ConditionalNode, register_node
    from autotask.api_keys import get_api_key
except ImportError:
    from stub import Node, GeneratorNode, ConditionalNode, register_node, get_api_key

from typing import Dict, Any, Generator

@register_node
class BooleanConditionNode(ConditionalNode):
    """Conditional node to evaluate boolean values"""
    NAME = "Boolean Condition"
    DESCRIPTION = "Routes workflow based on boolean input value"
    
    INPUTS = {
        "boolean_value": {
            "label": "Boolean Input",
            "description": "Boolean value to evaluate",
            "type": "BOOL",
            "required": True
        }
    }
    
    OUTPUTS = {
        "true_branch": {
            "label": "True Branch",
            "description": "Output when condition is True",
            "type": "BOOL"
        },
        "false_branch": {
            "label": "False Branch", 
            "description": "Output when condition is False",
            "type": "BOOL"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            boolean_value = node_inputs.get("boolean_value")
            workflow_logger.debug(f"Evaluating boolean value: {boolean_value}")
            
            if not isinstance(boolean_value, bool):
                error_msg = f"Invalid input type. Expected boolean, got {type(boolean_value)}"
                workflow_logger.error(error_msg)
                return {"condition_result": False}

            workflow_logger.debug(f"Boolean evaluation result: {boolean_value}")
            return {
                "condition_result": boolean_value
            }

        except Exception as e:
            error_msg = f"Boolean evaluation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "condition_result": False
            }

    def get_active_branch(self, outputs: Dict[str, Any]) -> str:
        """Returns the name of the active branch based on the boolean result"""
        return "true_branch" if outputs.get("condition_result") else "false_branch"