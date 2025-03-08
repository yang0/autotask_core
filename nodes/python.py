import json
import subprocess
import sys
from typing import Dict, Any, List, Optional
import time
import traceback

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger


@register_node
class PythonCodeNode(Node):
    """
    Execute Python code in the workflow
    
    This node allows you to execute arbitrary Python code within the workflow execution environment.
    It can be used to perform custom data transformations, calculations, or to implement custom 
    logic that isn't available through other nodes. The code is executed in a controlled environment
    and can return results for further processing in the workflow.
    
    Use cases:
    - Data transformation and manipulation
    - Custom calculations and algorithms
    - Integrating with libraries not directly supported by other nodes
    - Creating dynamic content based on workflow inputs
    
    Features:
    - Execute arbitrary Python code
    - Return specific variables from the execution
    - Access workflow variables via the input dictionary
    - Detailed error reporting
    
    Safety notice:
    - This node executes arbitrary Python code and should be used with caution
    - Code execution happens in the workflow environment and has access to system resources
    """
    NAME = "Python Code"
    DESCRIPTION = "Execute Python code and return the result"
    CATEGORY = "Programming"
    ICON = "code"

    INPUTS = {
        "code": {
            "label": "Python Code",
            "description": "The Python code to execute",
            "type": "STRING",
            "required": True,
        },
        "return_variable": {
            "label": "Return Variable",
            "description": "Name of the variable to return from the code execution (optional)",
            "type": "STRING",
            "required": False,
        },
        "input_data": {
            "label": "Input Data",
            "description": "JSON string with input data to be made available in the code as 'input_data'",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The result of the code execution",
            "type": "STRING",
        },
        "success": {
            "label": "Success",
            "description": "Whether the execution was successful",
            "type": "BOOL",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if execution failed",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # Use the provided logger or the default one
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # Get inputs
            code = node_inputs.get("code", "")
            return_variable = node_inputs.get("return_variable", None)
            input_data_str = node_inputs.get("input_data", "{}")
            
            if not code.strip():
                logger.error("No Python code provided")
                return {
                    "success": False,
                    "result": "",
                    "error_message": "No Python code provided"
                }
            
            # Parse input data if provided
            try:
                input_data = json.loads(input_data_str) if input_data_str.strip() else {}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse input data as JSON: {e}. Using empty dict.")
                input_data = {}
            
            # Setup execution environment
            exec_globals = {'__builtins__': __builtins__, 'input_data': input_data}
            exec_locals = {}
            
            # Log execution start
            logger.info(f"Executing Python code")
            start_time = time.time()
            
            # Execute the code
            try:
                exec(code, exec_globals, exec_locals)
                
                # Get result
                if return_variable:
                    if return_variable in exec_locals:
                        result = exec_locals[return_variable]
                        result_str = str(result)
                    else:
                        logger.warning(f"Return variable '{return_variable}' not found in execution context")
                        result_str = f"Return variable '{return_variable}' not found"
                else:
                    result_str = "Code executed successfully"
                
                elapsed = time.time() - start_time
                logger.info(f"Python code execution completed in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "result": result_str,
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error executing Python code: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "result": "",
                    "error_message": error_msg
                }
            
        except Exception as e:
            error_msg = f"Unexpected error in Python Code node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "result": "",
                "error_message": error_msg
            }


@register_node
class PythonPackageInstallNode(Node):
    """
    Install Python packages during workflow execution
    
    This node allows you to install Python packages using pip during the workflow execution.
    It's useful for dynamically adding dependencies that your workflow might need without
    having to pre-install them in the environment. The node supports installation of multiple
    packages and provides detailed status reporting.
    
    Use cases:
    - Adding dependencies required by other nodes in the workflow
    - Testing with different package versions
    - Installing specialized packages for specific workflow tasks
    - Dynamic dependency management based on workflow inputs
    
    Features:
    - Install single or multiple packages
    - Specify package versions
    - Detailed installation status reporting
    - Error handling and reporting
    
    Safety notice:
    - Installing packages modifies the Python environment
    - Be cautious with package sources and versions
    """
    NAME = "Python Package Install"
    DESCRIPTION = "Install Python packages using pip"
    CATEGORY = "Programming"
    ICON = "package"

    INPUTS = {
        "packages": {
            "label": "Packages",
            "description": "Comma-separated list of packages to install (e.g., 'pandas,numpy==1.22.0')",
            "type": "STRING",
            "required": True,
        },
        "upgrade": {
            "label": "Upgrade",
            "description": "Whether to upgrade the package if already installed",
            "type": "BOOL",
            "default": False,
            "required": False,
        }
    }

    OUTPUTS = {
        "installation_status": {
            "label": "Installation Status",
            "description": "Status of the package installation",
            "type": "STRING",
        },
        "success": {
            "label": "Success",
            "description": "Whether all packages were installed successfully",
            "type": "BOOL",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if installation failed",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # Use the provided logger or the default one
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # Get inputs
            packages_str = node_inputs.get("packages", "")
            upgrade = node_inputs.get("upgrade", False)
            
            if not packages_str.strip():
                logger.error("No packages specified for installation")
                return {
                    "success": False,
                    "installation_status": "Failed: No packages specified",
                    "error_message": "No packages specified for installation"
                }
            
            # Parse packages list
            packages = [pkg.strip() for pkg in packages_str.split(",") if pkg.strip()]
            
            logger.info(f"Installing {len(packages)} Python packages: {', '.join(packages)}")
            start_time = time.time()
            
            # Prepare installation results
            installation_results = []
            all_successful = True
            
            # Install each package
            for package in packages:
                try:
                    # Prepare pip command
                    pip_cmd = [sys.executable, "-m", "pip", "install"]
                    if upgrade:
                        pip_cmd.append("--upgrade")
                    pip_cmd.append(package)
                    
                    logger.info(f"Running: {' '.join(pip_cmd)}")
                    
                    # Execute pip install
                    process = subprocess.run(
                        pip_cmd,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if process.returncode == 0:
                        msg = f"Successfully installed {package}"
                        logger.info(msg)
                        installation_results.append({"package": package, "status": "success", "message": msg})
                    else:
                        msg = f"Failed to install {package}: {process.stderr.strip()}"
                        logger.error(msg)
                        installation_results.append({"package": package, "status": "error", "message": msg})
                        all_successful = False
                
                except Exception as e:
                    msg = f"Error installing {package}: {str(e)}"
                    logger.error(msg)
                    installation_results.append({"package": package, "status": "error", "message": msg})
                    all_successful = False
            
            elapsed = time.time() - start_time
            logger.info(f"Package installation completed in {elapsed:.2f}s")
            
            # Prepare return data
            installation_status = json.dumps(installation_results, indent=2)
            error_message = ""
            
            if not all_successful:
                failed_packages = [r["package"] for r in installation_results if r["status"] == "error"]
                error_message = f"Failed to install the following packages: {', '.join(failed_packages)}"
            
            return {
                "success": all_successful,
                "installation_status": installation_status,
                "error_message": error_message
            }
            
        except Exception as e:
            error_msg = f"Unexpected error in Python Package Install node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "installation_status": "Failed",
                "error_message": error_msg
            }


@register_node
class PythonFileExecuteNode(Node):
    """
    Execute a Python file in the workflow
    
    This node allows you to execute a Python file within the workflow execution environment.
    It's useful for running pre-written scripts, integrating existing code, or organizing
    complex logic in separate files. The node can return specified variables from the executed
    script for further processing in the workflow.
    
    Use cases:
    - Running pre-written Python scripts
    - Integrating with existing codebase
    - Breaking complex logic into separate files
    - Maintaining reusable code components
    
    Features:
    - Execute Python files from specified paths
    - Return specific variables from execution
    - Provide arguments to the script
    - Detailed error reporting
    
    Safety notice:
    - This node executes arbitrary Python code and should be used with caution
    - Code execution happens in the workflow environment and has access to system resources
    """
    NAME = "Python File Execute"
    DESCRIPTION = "Execute a Python file and return the result"
    CATEGORY = "Programming"
    ICON = "file-code"

    INPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the Python file to execute",
            "type": "STRING",
            "required": True,
        },
        "return_variable": {
            "label": "Return Variable",
            "description": "Name of the variable to return from the script execution (optional)",
            "type": "STRING",
            "required": False,
        },
        "arguments": {
            "label": "Arguments",
            "description": "JSON string with arguments to pass to the script",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "result": {
            "label": "Result",
            "description": "The result of the file execution",
            "type": "STRING",
        },
        "success": {
            "label": "Success",
            "description": "Whether the execution was successful",
            "type": "BOOL",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if execution failed",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # Use the provided logger or the default one
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # Get inputs
            file_path = node_inputs.get("file_path", "")
            return_variable = node_inputs.get("return_variable", None)
            arguments_str = node_inputs.get("arguments", "{}")
            
            if not file_path.strip():
                logger.error("No Python file path provided")
                return {
                    "success": False,
                    "result": "",
                    "error_message": "No Python file path provided"
                }
            
            # Parse arguments if provided
            try:
                arguments = json.loads(arguments_str) if arguments_str.strip() else {}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse arguments as JSON: {e}. Using empty dict.")
                arguments = {}
            
            logger.info(f"Executing Python file: {file_path}")
            start_time = time.time()
            
            try:
                # Set up sys.argv for the script
                original_argv = sys.argv.copy()
                sys.argv = [file_path]
                
                if isinstance(arguments, dict):
                    # Add arguments as environment variables
                    import os
                    original_env = os.environ.copy()
                    for key, value in arguments.items():
                        os.environ[str(key)] = str(value)
                elif isinstance(arguments, list):
                    # Add arguments as command line args
                    for arg in arguments:
                        sys.argv.append(str(arg))
                
                # Execute the file
                globals_dict = {'__name__': '__main__'}
                try:
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                    
                    exec(file_content, globals_dict)
                    
                    # Get result
                    if return_variable:
                        if return_variable in globals_dict:
                            result = globals_dict[return_variable]
                            result_str = str(result)
                        else:
                            logger.warning(f"Return variable '{return_variable}' not found in script globals")
                            result_str = f"Return variable '{return_variable}' not found"
                    else:
                        result_str = "File executed successfully"
                    
                finally:
                    # Restore original argv and environment
                    sys.argv = original_argv
                    if isinstance(arguments, dict):
                        import os
                        os.environ.clear()
                        os.environ.update(original_env)
                
                elapsed = time.time() - start_time
                logger.info(f"Python file execution completed in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "result": result_str,
                    "error_message": ""
                }
                
            except FileNotFoundError:
                error_msg = f"Python file not found: {file_path}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "result": "",
                    "error_message": error_msg
                }
                
            except Exception as e:
                error_msg = f"Error executing Python file: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "result": "",
                    "error_message": error_msg
                }
            
        except Exception as e:
            error_msg = f"Unexpected error in Python File Execute node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "result": "",
                "error_message": error_msg
            }


# Test code (runs when this file is executed directly)
if __name__ == "__main__":
    import asyncio
    
    # Create a simple logger for testing
    class SimpleLogger:
        @staticmethod
        def info(msg): print(f"INFO: {msg}")
        @staticmethod
        def error(msg): print(f"ERROR: {msg}")
        @staticmethod
        def warning(msg): print(f"WARNING: {msg}")
        @staticmethod
        def debug(msg): print(f"DEBUG: {msg}")
    
    logger = SimpleLogger()
    
    # Test PythonCodeNode
    print("\nTesting PythonCodeNode:")
    node1 = PythonCodeNode()
    result = asyncio.run(node1.execute({
        "code": "result = 'Hello, ' + input_data.get('name', 'World')",
        "return_variable": "result",
        "input_data": '{"name": "Python"}'
    }, logger))
    print(f"Success: {result['success']}")
    print(f"Result: {result['result']}")
    
    # Test PythonPackageInstallNode
    print("\nTesting PythonPackageInstallNode:")
    node2 = PythonPackageInstallNode()
    # Note: This would actually install packages, so we'll just print what would happen
    print("Would run: pip install requests,rich")
    
    # Test PythonFileExecuteNode
    print("\nTesting PythonFileExecuteNode:")
    node3 = PythonFileExecuteNode()
    # Create a temporary Python file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("import os\n")
        f.write("test_var = 'File execution successful!'\n")
        f.write("print('Environment arg:', os.environ.get('test_arg', 'not found'))\n")
        temp_file = f.name
    
    result = asyncio.run(node3.execute({
        "file_path": temp_file,
        "return_variable": "test_var",
        "arguments": '{"test_arg": "Hello from args"}'
    }, logger))
    print(f"Success: {result['success']}")
    print(f"Result: {result['result']}")
    
    # Clean up
    import os
    os.unlink(temp_file) 