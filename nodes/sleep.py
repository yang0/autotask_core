try:
    from autotask.nodes import Node, register_node
except ImportError:
    # Mock for development environment
    from stub import Node, register_node

import asyncio
import time
from typing import Dict, Any, Optional


@register_node
class SleepNode(Node):
    """Node for pausing workflow execution for a specified duration"""
    NAME = "Sleep"
    DESCRIPTION = "Pauses workflow execution for a specified number of seconds"
    CATEGORY = "Utility"
    ICON = "clock"
    
    INPUTS = {
        "seconds": {
            "label": "Seconds",
            "description": "Number of seconds to pause execution",
            "type": "INT",
            "default": 5,
            "required": True,
        },
        "message": {
            "label": "Custom Message",
            "description": "Optional custom message to log during the sleep period",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "duration": {
            "label": "Actual Duration",
            "description": "The actual time (in seconds) that execution was paused",
            "type": "FLOAT",
        },
        "message": {
            "label": "Result Message",
            "description": "Message confirming the sleep operation completed",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            seconds = node_inputs.get("seconds", 5)
            custom_message = node_inputs.get("message", "")
            
            # Ensure seconds is a positive integer
            try:
                seconds = int(seconds)
                if seconds < 0:
                    seconds = 0
            except (ValueError, TypeError):
                workflow_logger.warning(f"Invalid sleep duration: {seconds}, defaulting to 5 seconds")
                seconds = 5
            
            message = custom_message if custom_message else f"Sleeping for {seconds} seconds"
            workflow_logger.info(f"Starting sleep: {message}")
            
            # Record start time
            start_time = time.time()
            
            # Use asyncio.sleep for asynchronous sleep
            if seconds > 0:
                await asyncio.sleep(seconds)
            
            # Calculate actual duration
            end_time = time.time()
            actual_duration = end_time - start_time
            
            result_message = custom_message if custom_message else f"Slept for {seconds} seconds"
            workflow_logger.info(f"Sleep completed: {result_message}")
            
            return {
                "success": "true",
                "duration": actual_duration,
                "message": result_message,
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error during sleep operation: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "duration": 0,
                "message": "",
                "error_message": error_msg
            }


@register_node
class TimedOperationNode(Node):
    """Node for measuring the time taken by a placeholder operation"""
    NAME = "Timed Operation"
    DESCRIPTION = "Simulates an operation taking a specified amount of time and reports the duration"
    CATEGORY = "Utility"
    ICON = "hourglass"
    
    INPUTS = {
        "operation_time": {
            "label": "Operation Time",
            "description": "Simulated time (in seconds) for the operation to complete",
            "type": "INT",
            "default": 3,
            "required": True,
        },
        "operation_name": {
            "label": "Operation Name",
            "description": "Name of the simulated operation",
            "type": "STRING",
            "default": "Processing",
            "required": False,
        },
        "success_probability": {
            "label": "Success Probability",
            "description": "Probability (0-100) that the operation succeeds",
            "type": "INT",
            "default": 100,
            "required": False,
        }
    }
    
    OUTPUTS = {
        "duration": {
            "label": "Operation Duration",
            "description": "The time (in seconds) taken by the operation",
            "type": "FLOAT",
        },
        "operation_name": {
            "label": "Operation Name",
            "description": "The name of the operation that was performed",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            operation_time = node_inputs.get("operation_time", 3)
            operation_name = node_inputs.get("operation_name", "Processing")
            success_probability = node_inputs.get("success_probability", 100)
            
            # Ensure inputs are valid
            try:
                operation_time = int(operation_time)
                if operation_time < 0:
                    operation_time = 0
                
                success_probability = int(success_probability)
                if success_probability < 0:
                    success_probability = 0
                elif success_probability > 100:
                    success_probability = 100
            except (ValueError, TypeError):
                workflow_logger.warning(f"Invalid input parameters, using defaults")
                operation_time = 3
                success_probability = 100
            
            workflow_logger.info(f"Starting {operation_name} operation (estimated time: {operation_time}s)")
            
            # Record start time
            start_time = time.time()
            
            # Simulate the operation
            if operation_time > 0:
                # Show progress at 25%, 50%, and 75%
                quarter_time = operation_time / 4
                for i in range(1, 4):
                    await asyncio.sleep(quarter_time)
                    progress = i * 25
                    workflow_logger.info(f"{operation_name} progress: {progress}%")
                
                # Complete the operation
                await asyncio.sleep(quarter_time)
            
            # Calculate actual duration
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # Determine if operation succeeded based on probability
            import random
            operation_succeeded = random.randint(1, 100) <= success_probability
            
            if operation_succeeded:
                workflow_logger.info(f"{operation_name} completed successfully in {actual_duration:.2f} seconds")
                return {
                    "success": "true",
                    "duration": actual_duration,
                    "operation_name": operation_name,
                    "error_message": ""
                }
            else:
                error_msg = f"{operation_name} failed (simulated failure)"
                workflow_logger.error(error_msg)
                return {
                    "success": "false",
                    "duration": actual_duration,
                    "operation_name": operation_name,
                    "error_message": error_msg
                }
            
        except Exception as e:
            error_msg = f"Error during {node_inputs.get('operation_name', 'operation')}: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "duration": 0,
                "operation_name": node_inputs.get("operation_name", "Unknown"),
                "error_message": error_msg
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def test_nodes():
        # Test SleepNode
        print("\nTesting SleepNode:")
        node1 = SleepNode()
        result = await node1.execute({"seconds": 2}, logger)
        print(f"Success: {result['success']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Message: {result['message']}")
        
        # Test TimedOperationNode
        print("\nTesting TimedOperationNode:")
        node2 = TimedOperationNode()
        result = await node2.execute({
            "operation_time": 1,
            "operation_name": "Test Processing",
            "success_probability": 100
        }, logger)
        print(f"Success: {result['success']}")
        print(f"Operation: {result['operation_name']}")
        print(f"Duration: {result['duration']:.2f}s")
    
    # Run tests
    import asyncio
    asyncio.run(test_nodes()) 