from autotask.nodes import Node, register_node

@register_node
class StringProcessNode(Node):
    """A basic node that processes string input and returns string output"""
    
    NAME = "String Process"
    DESCRIPTION = "A basic node that takes a string input and returns it as output"
    CATEGORY = "Basic"
    
    INPUTS = {
        "input_text": {
            "type": "STRING",
            "description": "Input text to process",
            "required": True,
            "label": "输入文本"
        }
    }
    
    OUTPUTS = {
        "output_text": {
            "type": "STRING",
            "description": "Processed output text",
            "label": "输出文本"
        }
    }

    async def execute(self, node_inputs: dict, workflow_logger) -> dict:
        """
        Execute the node's logic
        
        Args:
            node_inputs: Dictionary containing the input parameters
            workflow_logger: Logger instance for the workflow
            
        Returns:
            Dictionary containing the output parameters
        """
        try:
            workflow_logger.info(f"Node inputs received: {node_inputs}")
            
            # Get the input text
            input_text = node_inputs.get("input_text")
            workflow_logger.info(f"Raw input text: {input_text!r}")
            
            # Handle empty or null input
            if input_text is None:
                workflow_logger.warning("Input text is None")
                return {"output_text": ""}
                
            if not isinstance(input_text, str):
                workflow_logger.warning(f"Input text is not a string, converting from {type(input_text)}")
                input_text = str(input_text)
            
            if input_text.strip() == "":
                workflow_logger.warning("Input text is empty or whitespace")
                return {"output_text": ""}
            
            workflow_logger.info(f"Processing input text: {input_text}")
            
            # Process and return the input text
            result = {
                "output_text": input_text
            }
            workflow_logger.info(f"Generated output: {result}")
            return result
            
        except Exception as e:
            workflow_logger.error(f"Error processing text: {str(e)}")
            workflow_logger.error(f"Input data was: {node_inputs}")
            raise
