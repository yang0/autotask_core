try:
    from autotask.nodes import Node, register_node
except ImportError:
    # Mock for development environment
    from stub import Node, register_node

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


@register_node
class FileWriteNode(Node):
    """Node for writing content to a file"""
    NAME = "File Write"
    DESCRIPTION = "Writes content to a file at specified path"
    CATEGORY = "File"
    ICON = "file-pen"
    
    INPUTS = {
        "contents": {
            "label": "File Contents",
            "description": "The content to write to the file",
            "type": "STRING",
            "required": True,
        },
        "file_name": {
            "label": "File Name",
            "description": "The name/path of the file to write to (relative to base directory)",
            "type": "STRING",
            "required": True,
        },
        "overwrite": {
            "label": "Overwrite",
            "description": "Whether to overwrite the file if it already exists",
            "type": "STRING",
            "default": "true",
            "required": False,
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "The base directory to save the file in (leave empty for current working directory)",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "The path of the saved file if successful",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the file write operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if write operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            contents = node_inputs.get("contents", "")
            file_name = node_inputs.get("file_name", "")
            overwrite_str = node_inputs.get("overwrite", "true")
            base_dir = node_inputs.get("base_dir", "")
            
            # Convert overwrite string to boolean
            overwrite = overwrite_str.lower() == "true"
            
            if not file_name:
                workflow_logger.error("No file name provided")
                return {
                    "success": "false",
                    "error_message": "No file name provided",
                    "file_path": ""
                }
            
            # Determine base directory
            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)
                if not base_path.exists():
                    workflow_logger.info(f"Creating base directory: {base_path}")
                    base_path.mkdir(parents=True, exist_ok=True)
            
            # Create full file path
            file_path = base_path.joinpath(file_name)
            
            # Create parent directories if they don't exist
            if not file_path.parent.exists():
                workflow_logger.info(f"Creating parent directories: {file_path.parent}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and handle overwrite
            if file_path.exists() and not overwrite:
                workflow_logger.warning(f"File {file_path} already exists and overwrite is set to false")
                return {
                    "success": "false",
                    "error_message": f"File {file_path} already exists",
                    "file_path": str(file_path)
                }
            
            # Write content to file
            workflow_logger.info(f"Saving content to file: {file_path}")
            file_path.write_text(contents)
            
            return {
                "success": "true",
                "file_path": str(file_path),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error writing to file: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "file_path": ""
            }


@register_node
class FileReadNode(Node):
    """Node for reading content from a file"""
    NAME = "File Read"
    DESCRIPTION = "Reads content from a file at specified path"
    CATEGORY = "File"
    ICON = "file-magnifying-glass"
    
    INPUTS = {
        "file_name": {
            "label": "File Name",
            "description": "The name/path of the file to read (relative to base directory)",
            "type": "STRING",
            "required": True,
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "The base directory to read the file from (leave empty for current working directory)",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "contents": {
            "label": "File Contents",
            "description": "The content read from the file",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the file read operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if read operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            file_name = node_inputs.get("file_name", "")
            base_dir = node_inputs.get("base_dir", "")
            
            if not file_name:
                workflow_logger.error("No file name provided")
                return {
                    "success": "false",
                    "error_message": "No file name provided",
                    "contents": ""
                }
            
            # Determine base directory
            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)
            
            # Create full file path
            file_path = base_path.joinpath(file_name)
            
            # Check if file exists
            if not file_path.exists():
                workflow_logger.error(f"File does not exist: {file_path}")
                return {
                    "success": "false",
                    "error_message": f"File does not exist: {file_path}",
                    "contents": ""
                }
            
            # Read file content
            workflow_logger.info(f"Reading content from file: {file_path}")
            contents = file_path.read_text()
            
            return {
                "success": "true",
                "contents": contents,
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "contents": ""
            }


@register_node
class FileListNode(Node):
    """Node for listing files in a directory"""
    NAME = "File List"
    DESCRIPTION = "Lists files and directories in the specified directory"
    CATEGORY = "File"
    ICON = "folder-open"
    
    INPUTS = {
        "directory": {
            "label": "Directory Path",
            "description": "The directory to list files from (leave empty for current working directory)",
            "type": "STRING",
            "required": False,
        },
        "pattern": {
            "label": "File Pattern",
            "description": "Pattern to filter files (e.g., '*.txt' for text files)",
            "type": "STRING",
            "required": False,
        },
        "include_dirs": {
            "label": "Include Directories",
            "description": "Whether to include directories in the results",
            "type": "STRING",
            "default": "true",
            "required": False,
        },
        "recursive": {
            "label": "Recursive",
            "description": "Whether to search recursively through subdirectories",
            "type": "STRING",
            "default": "false",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "files": {
            "label": "Files List",
            "description": "JSON string containing list of files found",
            "type": "STRING",
        },
        "count": {
            "label": "File Count",
            "description": "Number of files found",
            "type": "INT",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the file listing operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if listing operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            directory = node_inputs.get("directory", "")
            pattern = node_inputs.get("pattern", "")
            include_dirs_str = node_inputs.get("include_dirs", "true")
            recursive_str = node_inputs.get("recursive", "false")
            
            # Convert string inputs to booleans
            include_dirs = include_dirs_str.lower() == "true"
            recursive = recursive_str.lower() == "true"
            
            # Determine directory path
            if directory:
                dir_path = Path(directory)
            else:
                dir_path = Path.cwd()
            
            if not dir_path.exists() or not dir_path.is_dir():
                workflow_logger.error(f"Directory does not exist or is not a directory: {dir_path}")
                return {
                    "success": "false",
                    "error_message": f"Directory does not exist or is not a directory: {dir_path}",
                    "files": "[]",
                    "count": 0
                }
            
            workflow_logger.info(f"Listing files in directory: {dir_path}")
            
            # Collect files
            file_list = []
            
            if recursive:
                # Use rglob for recursive search
                if pattern:
                    paths = list(dir_path.rglob(pattern))
                else:
                    paths = list(dir_path.rglob("*"))
            else:
                # Use glob for non-recursive search
                if pattern:
                    paths = list(dir_path.glob(pattern))
                else:
                    paths = list(dir_path.glob("*"))
            
            # Filter and format the results
            for path in paths:
                if path.is_dir() and not include_dirs:
                    continue
                    
                file_info = {
                    "path": str(path),
                    "name": path.name,
                    "is_dir": path.is_dir(),
                    "size": path.stat().st_size if path.is_file() else 0,
                    "modified": path.stat().st_mtime
                }
                file_list.append(file_info)
            
            workflow_logger.info(f"Found {len(file_list)} files/directories")
            
            return {
                "success": "true",
                "files": json.dumps(file_list, indent=2),
                "count": len(file_list),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error listing files: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "files": "[]",
                "count": 0
            }


@register_node
class FileDeleteNode(Node):
    """Node for deleting a file or directory"""
    NAME = "File Delete"
    DESCRIPTION = "Deletes a file or directory at the specified path"
    CATEGORY = "File"
    ICON = "trash"
    
    INPUTS = {
        "file_path": {
            "label": "File/Directory Path",
            "description": "The path of the file or directory to delete",
            "type": "STRING",
            "required": True,
        },
        "recursive": {
            "label": "Recursive Delete",
            "description": "Whether to recursively delete directories (required for non-empty directories)",
            "type": "STRING",
            "default": "false",
            "required": False,
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "The base directory (leave empty for current working directory)",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "deleted_path": {
            "label": "Deleted Path",
            "description": "The path that was deleted",
            "type": "STRING",
        },
        "success": {
            "label": "Success Status",
            "description": "Whether the delete operation was successful",
            "type": "STRING",
        },
        "error_message": {
            "label": "Error Message",
            "description": "Error message if delete operation failed",
            "type": "STRING",
        }
    }
    
    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            file_path_input = node_inputs.get("file_path", "")
            recursive_str = node_inputs.get("recursive", "false")
            base_dir = node_inputs.get("base_dir", "")
            
            # Convert string inputs to booleans
            recursive = recursive_str.lower() == "true"
            
            if not file_path_input:
                workflow_logger.error("No file path provided")
                return {
                    "success": "false",
                    "error_message": "No file path provided",
                    "deleted_path": ""
                }
            
            # Determine base directory
            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)
            
            # Create full file path
            file_path = base_path.joinpath(file_path_input)
            
            if not file_path.exists():
                workflow_logger.warning(f"File/directory does not exist: {file_path}")
                return {
                    "success": "false",
                    "error_message": f"File/directory does not exist: {file_path}",
                    "deleted_path": str(file_path)
                }
            
            # Handle directory deletion
            if file_path.is_dir():
                if recursive:
                    workflow_logger.info(f"Recursively deleting directory: {file_path}")
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    workflow_logger.info(f"Deleting directory: {file_path}")
                    try:
                        file_path.rmdir()  # Will only work if directory is empty
                    except OSError as e:
                        return {
                            "success": "false",
                            "error_message": f"Directory not empty. Use recursive=true to delete non-empty directories",
                            "deleted_path": str(file_path)
                        }
            else:
                # Handle file deletion
                workflow_logger.info(f"Deleting file: {file_path}")
                file_path.unlink()
            
            return {
                "success": "true",
                "deleted_path": str(file_path),
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error deleting file/directory: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "deleted_path": ""
            }


@register_node
class FileInfoNode(Node):
    """Node for getting information about a file or directory"""
    NAME = "File Info"
    DESCRIPTION = "Retrieves information about a file or directory"
    CATEGORY = "File"
    ICON = "circle-info"
    
    INPUTS = {
        "file_path": {
            "label": "File/Directory Path",
            "description": "The path of the file or directory to get information about",
            "type": "STRING",
            "required": True,
        },
        "base_dir": {
            "label": "Base Directory",
            "description": "The base directory (leave empty for current working directory)",
            "type": "STRING",
            "required": False,
        }
    }
    
    OUTPUTS = {
        "info": {
            "label": "File Information",
            "description": "JSON string containing information about the file or directory",
            "type": "STRING",
        },
        "exists": {
            "label": "File Exists",
            "description": "Whether the file or directory exists",
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
            file_path_input = node_inputs.get("file_path", "")
            base_dir = node_inputs.get("base_dir", "")
            
            if not file_path_input:
                workflow_logger.error("No file path provided")
                return {
                    "success": "false",
                    "error_message": "No file path provided",
                    "info": "{}",
                    "exists": "false"
                }
            
            # Determine base directory
            base_path = Path.cwd()
            if base_dir:
                base_path = Path(base_dir)
            
            # Create full file path
            file_path = base_path.joinpath(file_path_input)
            
            # Check if file exists
            if not file_path.exists():
                workflow_logger.info(f"File/directory does not exist: {file_path}")
                return {
                    "success": "true",
                    "info": json.dumps({
                        "path": str(file_path),
                        "exists": False
                    }),
                    "exists": "false",
                    "error_message": ""
                }
            
            # Get file information
            workflow_logger.info(f"Getting information for: {file_path}")
            
            is_dir = file_path.is_dir()
            
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "exists": True,
                "is_directory": is_dir,
                "is_file": file_path.is_file(),
                "parent": str(file_path.parent),
                "extension": file_path.suffix if file_path.is_file() else "",
                "stem": file_path.stem
            }
            
            # Add stat information
            stats = file_path.stat()
            info["size"] = stats.st_size
            info["created_time"] = stats.st_ctime
            info["modified_time"] = stats.st_mtime
            info["accessed_time"] = stats.st_atime
            
            # If it's a directory, count files and subdirectories
            if is_dir:
                try:
                    contents = list(file_path.iterdir())
                    info["file_count"] = sum(1 for item in contents if item.is_file())
                    info["directory_count"] = sum(1 for item in contents if item.is_dir())
                    info["total_items"] = len(contents)
                except PermissionError:
                    info["permission_error"] = "Cannot list directory contents due to permission restrictions"
            
            return {
                "success": "true",
                "info": json.dumps(info, indent=2),
                "exists": "true",
                "error_message": ""
            }
            
        except Exception as e:
            error_msg = f"Error getting file information: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": "false",
                "error_message": error_msg,
                "info": "{}",
                "exists": "false"
            }


if __name__ == "__main__":
    # Setup basic logging for testing
    import logging
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test FileWriteNode
        print("\nTesting FileWriteNode:")
        node1 = FileWriteNode()
        result = asyncio.run(node1.execute({
            "contents": "Hello, world!",
            "file_name": "test.txt",
            "base_dir": str(temp_path)
        }, logger))
        print(f"File write success: {result['success']}, path: {result['file_path']}")
        
        # Test FileReadNode
        print("\nTesting FileReadNode:")
        node2 = FileReadNode()
        result = asyncio.run(node2.execute({
            "file_name": "test.txt",
            "base_dir": str(temp_path)
        }, logger))
        print(f"File read success: {result['success']}, content: {result['contents']}")
        
        # Create some more test files
        (temp_path / "test_dir").mkdir()
        (temp_path / "test_dir" / "nested.txt").write_text("Nested file content")
        (temp_path / "another.txt").write_text("Another file")
        
        # Test FileListNode
        print("\nTesting FileListNode:")
        node3 = FileListNode()
        result = asyncio.run(node3.execute({
            "directory": str(temp_path),
            "pattern": "*.txt"
        }, logger))
        print(f"File list success: {result['success']}, count: {result['count']}")
        
        # Test FileInfoNode
        print("\nTesting FileInfoNode:")
        node4 = FileInfoNode()
        result = asyncio.run(node4.execute({
            "file_path": "test.txt",
            "base_dir": str(temp_path)
        }, logger))
        print(f"File info success: {result['success']}, exists: {result['exists']}")
        
        # Test FileDeleteNode
        print("\nTesting FileDeleteNode:")
        node5 = FileDeleteNode()
        result = asyncio.run(node5.execute({
            "file_path": "test.txt",
            "base_dir": str(temp_path)
        }, logger))
        print(f"File delete success: {result['success']}, deleted: {result['deleted_path']}")
        
        # Verify file was deleted
        result = asyncio.run(node4.execute({
            "file_path": "test.txt",
            "base_dir": str(temp_path)
        }, logger))
        print(f"File exists after deletion: {result['exists']}") 