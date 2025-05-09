from typing import Dict, Any, AsyncGenerator, Iterable, Union, List, Set, Dict as DictType
from autotask.nodes import GeneratorNode, register_node

@register_node
class IteratorNode(GeneratorNode):
    NAME = "Iterator"
    DESCRIPTION = "Iterate through arrays, sets, other iterable objects, or strings (split by newlines) and yield elements"
    
    INPUTS = {
        "iterable": {
            "label": "Iterable Object",
            "description": "Array, set, string (split by newlines), or other iterable object to iterate through",
            "type": "",
            "required": True,
            "default": []
        },
        "skip_none": {
            "label": "Skip None Values",
            "description": "Whether to skip None values during iteration",
            "type": "BOOLEAN",
            "required": False,
            "default": True
        },
        "max_iterations": {
            "label": "Maximum Iterations",
            "description": "Maximum number of iterations (0 for unlimited)",
            "type": "INT",
            "required": False,
            "default": 0
        }
    }
    
    OUTPUTS = {
        "item": {
            "label": "Current Item",
            "description": "Current item in iteration",
            "type": ""
        }
    }
    
    CATEGORY = "Flow Control"

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> AsyncGenerator[Any, None]:
        log = workflow_logger
        try:
            iterable = node_inputs["iterable"]
            skip_none = node_inputs.get("skip_none", True)
            max_iterations = node_inputs.get("max_iterations", 0)
            
            # Handle string input by splitting on newlines
            if isinstance(iterable, str):
                log.info("Processing string input by splitting on newlines")
                iterable = iterable.splitlines()
            
            if not isinstance(iterable, (list, set, dict, tuple, Iterable)):
                log.error(f"Input must be iterable or string, got: {type(iterable)}")
                return
            
            log.info(f"Starting iteration of type: {type(iterable).__name__}")
            
            # Handle different iterable types
            if isinstance(iterable, dict):
                items = iterable.items()
            elif isinstance(iterable, (list, set, tuple)):
                items = enumerate(iterable)
            else:
                items = enumerate(iterable)
            
            iteration_count = 0
            for index, item in items:
                if max_iterations > 0 and iteration_count >= max_iterations:
                    log.info(f"Reached maximum iteration count: {max_iterations}")
                    break
                    
                if skip_none and item is None:
                    log.debug(f"Skipping None value at index {index}")
                    continue
                    
                log.debug(f"Processing item at index {index}")
                yield {
                    "success": True,
                    "item": item
                }
                iteration_count += 1
                
            log.info("Iteration completed successfully")
            
        except Exception as e:
            log.error(f"Iteration failed: {str(e)}")
            return
