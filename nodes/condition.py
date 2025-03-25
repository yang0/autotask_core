try:
    from autotask.nodes import Node, GeneratorNode, ConditionalNode, register_node
    from autotask.api_keys import get_api_key
except ImportError:
    from stub import Node, GeneratorNode, ConditionalNode, register_node, get_api_key

from typing import Dict, Any, Generator

@register_node
class ExampleConditionNode(ConditionalNode):
    """Conditional node to determine if a number is even"""
    NAME = "Even Number Check"
    DESCRIPTION = "Check if the input number is even and execute different branches accordingly"
    
    INPUTS = {
        "number": {
            "label": "Input Number",
            "description": "Number to check",
            "type": "INT",
            "required": True
        }
    }
    
    OUTPUTS = {
        "true_branch": {
            "label": "Even Branch",
            "description": "Output when number is even",
            "type": ""
        },
        "false_branch": {
            "label": "Odd Branch", 
            "description": "Output when number is odd",
            "type": ""
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            number = node_inputs.get("number")
            workflow_logger.debug(f"Checking number: {number}")
            
            # Check if number is even
            is_even = number % 2 == 0
            workflow_logger.debug(f"Is even: {is_even}")

            return {
                "condition_result": is_even
            }

        except Exception as e:
            error_msg = f"Even number check failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "condition_result": None
            }

    def get_active_branch(self, outputs: Dict[str, Any]) -> str:
        """Returns the name of the active branch"""
        return "true_branch" if outputs.get("condition_result") else "false_branch"