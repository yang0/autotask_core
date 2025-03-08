try:
    from autotask.nodes import Node, register_node
except ImportError:
    # Mock for development environment
    from stub import Node, register_node

import json
import math
from typing import Dict, Any


@register_node
class AdditionNode(Node):
    """Node for adding two numbers"""
    NAME = "Addition"
    DESCRIPTION = "Adds two numbers together"
    CATEGORY = "Math"
    ICON = "plus"
    
    INPUTS = {
        "a": {
            "label": "First Number",
            "description": "The first number to add",
            "type": "FLOAT",
            "required": True,
        },
        "b": {
            "label": "Second Number",
            "description": "The second number to add",
            "type": "FLOAT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The sum of the two numbers",
            "type": "FLOAT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            a = float(node_inputs.get("a", 0))
            b = float(node_inputs.get("b", 0))
            
            workflow_logger.info(f"Adding {a} and {b}")
            result = a + b
            
            return {
                "result": result,
                "operation": "addition",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Addition failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "addition",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class SubtractionNode(Node):
    """Node for subtracting one number from another"""
    NAME = "Subtraction"
    DESCRIPTION = "Subtracts the second number from the first"
    CATEGORY = "Math"
    ICON = "minus"
    
    INPUTS = {
        "a": {
            "label": "First Number",
            "description": "The number to subtract from",
            "type": "FLOAT",
            "required": True,
        },
        "b": {
            "label": "Second Number",
            "description": "The number to subtract",
            "type": "FLOAT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The difference between the two numbers",
            "type": "FLOAT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            a = float(node_inputs.get("a", 0))
            b = float(node_inputs.get("b", 0))
            
            workflow_logger.info(f"Subtracting {b} from {a}")
            result = a - b
            
            return {
                "result": result,
                "operation": "subtraction",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Subtraction failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "subtraction",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class MultiplicationNode(Node):
    """Node for multiplying two numbers"""
    NAME = "Multiplication"
    DESCRIPTION = "Multiplies two numbers together"
    CATEGORY = "Math"
    ICON = "xmark"
    
    INPUTS = {
        "a": {
            "label": "First Number",
            "description": "The first number to multiply",
            "type": "FLOAT",
            "required": True,
        },
        "b": {
            "label": "Second Number",
            "description": "The second number to multiply",
            "type": "FLOAT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The product of the two numbers",
            "type": "FLOAT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            a = float(node_inputs.get("a", 0))
            b = float(node_inputs.get("b", 0))
            
            workflow_logger.info(f"Multiplying {a} and {b}")
            result = a * b
            
            return {
                "result": result,
                "operation": "multiplication",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Multiplication failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "multiplication",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class DivisionNode(Node):
    """Node for dividing one number by another"""
    NAME = "Division"
    DESCRIPTION = "Divides the first number by the second"
    CATEGORY = "Math"
    ICON = "divide"
    
    INPUTS = {
        "a": {
            "label": "Numerator",
            "description": "The number to be divided",
            "type": "FLOAT",
            "required": True,
        },
        "b": {
            "label": "Denominator",
            "description": "The number to divide by",
            "type": "FLOAT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The quotient of the division",
            "type": "FLOAT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            a = float(node_inputs.get("a", 0))
            b = float(node_inputs.get("b", 0))
            
            if b == 0:
                workflow_logger.error("Division by zero attempted")
                return {
                    "result": 0,
                    "operation": "division",
                    "success": "false",
                    "error_message": "Division by zero is undefined"
                }
            
            workflow_logger.info(f"Dividing {a} by {b}")
            result = a / b
            
            return {
                "result": result,
                "operation": "division",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Division failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "division",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class ExponentiationNode(Node):
    """Node for raising a number to a power"""
    NAME = "Exponentiation"
    DESCRIPTION = "Raises the first number to the power of the second"
    CATEGORY = "Math"
    ICON = "superscript"
    
    INPUTS = {
        "a": {
            "label": "Base",
            "description": "The base number",
            "type": "FLOAT",
            "required": True,
        },
        "b": {
            "label": "Exponent",
            "description": "The exponent to raise the base to",
            "type": "FLOAT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The result of the exponentiation",
            "type": "FLOAT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            a = float(node_inputs.get("a", 0))
            b = float(node_inputs.get("b", 0))
            
            workflow_logger.info(f"Raising {a} to the power of {b}")
            result = math.pow(a, b)
            
            return {
                "result": result,
                "operation": "exponentiation",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Exponentiation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "exponentiation",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class FactorialNode(Node):
    """Node for calculating the factorial of a number"""
    NAME = "Factorial"
    DESCRIPTION = "Calculates the factorial of a number"
    CATEGORY = "Math"
    ICON = "calculator"
    
    INPUTS = {
        "n": {
            "label": "Number",
            "description": "The number to calculate the factorial of",
            "type": "INT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The factorial of the input number",
            "type": "INT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            n = int(node_inputs.get("n", 0))
            
            if n < 0:
                workflow_logger.error("Factorial of negative number attempted")
                return {
                    "result": 0,
                    "operation": "factorial",
                    "success": "false",
                    "error_message": "Factorial of a negative number is undefined"
                }
            
            workflow_logger.info(f"Calculating factorial of {n}")
            result = math.factorial(n)
            
            return {
                "result": result,
                "operation": "factorial",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Factorial calculation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "factorial",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class PrimeCheckNode(Node):
    """Node for checking if a number is prime"""
    NAME = "Prime Check"
    DESCRIPTION = "Checks if a number is prime"
    CATEGORY = "Math"
    ICON = "check"
    
    INPUTS = {
        "n": {
            "label": "Number",
            "description": "The number to check if prime",
            "type": "INT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "is_prime": {
            "label": "Is Prime",
            "description": "Whether the number is prime",
            "type": "STRING",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            n = int(node_inputs.get("n", 0))
            
            workflow_logger.info(f"Checking if {n} is prime")
            
            if n <= 1:
                is_prime = "false"
            else:
                is_prime = "true"
                for i in range(2, int(math.sqrt(n)) + 1):
                    if n % i == 0:
                        is_prime = "false"
                        break
            
            return {
                "is_prime": is_prime,
                "operation": "prime_check",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Prime check failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "is_prime": "false",
                "operation": "prime_check",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class SquareRootNode(Node):
    """Node for calculating the square root of a number"""
    NAME = "Square Root"
    DESCRIPTION = "Calculates the square root of a number"
    CATEGORY = "Math"
    ICON = "square-root-variable"
    
    INPUTS = {
        "n": {
            "label": "Number",
            "description": "The number to calculate the square root of",
            "type": "FLOAT",
            "required": True,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The square root of the input number",
            "type": "FLOAT",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            n = float(node_inputs.get("n", 0))
            
            if n < 0:
                workflow_logger.error("Square root of negative number attempted")
                return {
                    "result": 0,
                    "operation": "square_root",
                    "success": "false",
                    "error_message": "Square root of a negative number is undefined"
                }
            
            workflow_logger.info(f"Calculating square root of {n}")
            result = math.sqrt(n)
            
            return {
                "result": result,
                "operation": "square_root",
                "success": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Square root calculation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "operation": "square_root",
                "success": "false",
                "error_message": error_msg
            }


@register_node
class CalculatorNode(Node):
    """Node for performing various mathematical operations"""
    NAME = "Calculator"
    DESCRIPTION = "Performs a selected mathematical operation on input values"
    CATEGORY = "Math"
    ICON = "calculator"
    
    INPUTS = {
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation to perform",
            "type": "STRING",
            "options": ["add", "subtract", "multiply", "divide", "exponentiate", "factorial", "prime_check", "square_root"],
            "default": "add",
            "required": True,
        },
        "a": {
            "label": "First Number",
            "description": "The first number (for binary operations)",
            "type": "FLOAT",
            "required": False,
        },
        "b": {
            "label": "Second Number",
            "description": "The second number (for binary operations)",
            "type": "FLOAT",
            "required": False,
        },
        "n": {
            "label": "Number",
            "description": "The input number (for unary operations like factorial)",
            "type": "FLOAT",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The result of the mathematical operation",
            "type": "FLOAT",
        },
        "is_prime": {
            "label": "Is Prime",
            "description": "Whether the number is prime (for prime_check operation)",
            "type": "STRING",
        },
        "operation": {
            "label": "Operation",
            "description": "The mathematical operation performed",
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
            operation = node_inputs.get("operation", "add")
            a = float(node_inputs.get("a", 0))
            b = float(node_inputs.get("b", 0))
            n = float(node_inputs.get("n", 0))
            
            workflow_logger.info(f"Performing operation: {operation}")
            
            # Initialize outputs
            result = 0
            is_prime = "false"
            error_message = ""
            success = "true"
            
            # Perform the selected operation
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    success = "false"
                    error_message = "Division by zero is undefined"
                else:
                    result = a / b
            elif operation == "exponentiate":
                result = math.pow(a, b)
            elif operation == "factorial":
                try:
                    n_int = int(n)
                    if n_int < 0:
                        success = "false"
                        error_message = "Factorial of a negative number is undefined"
                    else:
                        result = math.factorial(n_int)
                except ValueError:
                    success = "false"
                    error_message = "Factorial requires an integer input"
            elif operation == "prime_check":
                try:
                    n_int = int(n)
                    if n_int <= 1:
                        is_prime = "false"
                    else:
                        is_prime = "true"
                        for i in range(2, int(math.sqrt(n_int)) + 1):
                            if n_int % i == 0:
                                is_prime = "false"
                                break
                except ValueError:
                    success = "false"
                    error_message = "Prime check requires an integer input"
            elif operation == "square_root":
                if n < 0:
                    success = "false"
                    error_message = "Square root of a negative number is undefined"
                else:
                    result = math.sqrt(n)
            else:
                success = "false"
                error_message = f"Unknown operation: {operation}"
            
            return {
                "result": result,
                "is_prime": is_prime,
                "operation": operation,
                "success": success,
                "error_message": error_message
            }
            
        except Exception as e:
            error_msg = f"Calculator operation failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "result": 0,
                "is_prime": "false",
                "operation": node_inputs.get("operation", "unknown"),
                "success": "false",
                "error_message": error_msg
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def test_nodes():
        # Test AdditionNode
        print("\nTesting AdditionNode:")
        node = AdditionNode()
        result = await node.execute({"a": 5, "b": 3}, logger)
        print(f"5 + 3 = {result['result']}, success: {result['success']}")
        
        # Test SubtractionNode
        print("\nTesting SubtractionNode:")
        node = SubtractionNode()
        result = await node.execute({"a": 10, "b": 4}, logger)
        print(f"10 - 4 = {result['result']}, success: {result['success']}")
        
        # Test MultiplicationNode
        print("\nTesting MultiplicationNode:")
        node = MultiplicationNode()
        result = await node.execute({"a": 6, "b": 7}, logger)
        print(f"6 * 7 = {result['result']}, success: {result['success']}")
        
        # Test DivisionNode
        print("\nTesting DivisionNode:")
        node = DivisionNode()
        result = await node.execute({"a": 20, "b": 5}, logger)
        print(f"20 / 5 = {result['result']}, success: {result['success']}")
        
        # Test division by zero
        result = await node.execute({"a": 10, "b": 0}, logger)
        print(f"10 / 0 error: {result['error_message']}, success: {result['success']}")
        
        # Test ExponentiationNode
        print("\nTesting ExponentiationNode:")
        node = ExponentiationNode()
        result = await node.execute({"a": 2, "b": 3}, logger)
        print(f"2^3 = {result['result']}, success: {result['success']}")
        
        # Test FactorialNode
        print("\nTesting FactorialNode:")
        node = FactorialNode()
        result = await node.execute({"n": 5}, logger)
        print(f"5! = {result['result']}, success: {result['success']}")
        
        # Test PrimeCheckNode
        print("\nTesting PrimeCheckNode:")
        node = PrimeCheckNode()
        result = await node.execute({"n": 17}, logger)
        print(f"Is 17 prime? {result['is_prime']}, success: {result['success']}")
        
        result = await node.execute({"n": 4}, logger)
        print(f"Is 4 prime? {result['is_prime']}, success: {result['success']}")
        
        # Test SquareRootNode
        print("\nTesting SquareRootNode:")
        node = SquareRootNode()
        result = await node.execute({"n": 16}, logger)
        print(f"√16 = {result['result']}, success: {result['success']}")
        
        # Test CalculatorNode
        print("\nTesting CalculatorNode:")
        node = CalculatorNode()
        
        operations = ["add", "subtract", "multiply", "divide", "exponentiate", "factorial", "prime_check", "square_root"]
        inputs = [
            {"operation": "add", "a": 5, "b": 3},
            {"operation": "subtract", "a": 10, "b": 4},
            {"operation": "multiply", "a": 6, "b": 7},
            {"operation": "divide", "a": 20, "b": 5},
            {"operation": "exponentiate", "a": 2, "b": 3},
            {"operation": "factorial", "n": 5},
            {"operation": "prime_check", "n": 17},
            {"operation": "square_root", "n": 16}
        ]
        
        for input_data in inputs:
            result = await node.execute(input_data, logger)
            if input_data["operation"] == "prime_check":
                print(f"{input_data['operation']} result: {result['is_prime']}, success: {result['success']}")
            else:
                print(f"{input_data['operation']} result: {result['result']}, success: {result['success']}")
    
    # Run tests
    asyncio.run(test_nodes()) 