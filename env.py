import json
import os
from typing import Dict, Any, List
from pathlib import Path

try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

# 使用相对路径：从当前文件所在目录向上两级找到config目录
CONFIG_PATH = str(Path(__file__).parent.parent.parent / "config" / "env.json")

@register_node
class EnvKeyToValueNode(Node):
    """Convert environment key to its corresponding value"""
    NAME = "Environment Key to Value Converter"
    DESCRIPTION = "Convert up to 3 environment keys to their corresponding values"
    
    @staticmethod
    def _get_env_keys() -> List[str]:
        """Get available environment keys for combo options"""
        try:
            print(f"Loading env keys from {CONFIG_PATH}")  # 临时调试信息
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                keys = [item["key"] for item in data]
                print(f"Loaded env keys: {keys}")  # 临时调试信息
                return keys
        except Exception as e:
            print(f"Failed to load env keys: {str(e)}")  # 临时调试信息
            return []
    
    INPUTS = {
        "env_key1": {
            "label": "Environment Key 1",
            "description": "First environment key to convert",
            "type": "COMBO",
            "options": _get_env_keys(),
            "required": True
        },
        "env_key2": {
            "label": "Environment Key 2",
            "description": "Second environment key to convert",
            "type": "COMBO",
            "options": _get_env_keys(),
            "required": False
        },
        "env_key3": {
            "label": "Environment Key 3",
            "description": "Third environment key to convert",
            "type": "COMBO",
            "options": _get_env_keys(),
            "required": False
        }
    }
    
    OUTPUTS = {
        "env_value1": {
            "label": "Environment Value 1",
            "description": "Value for first key",
            "type": "STRING"
        },
        "env_value2": {
            "label": "Environment Value 2",
            "description": "Value for second key",
            "type": "STRING"
        },
        "env_value3": {
            "label": "Environment Value 3",
            "description": "Value for third key",
            "type": "STRING"
        }
    }

    def get_inputs(self) -> Dict[str, Any]:
        """Override get_inputs to provide dynamic options"""
        inputs = self.INPUTS.copy()
        env_keys = self._get_env_keys()
        
        for key in ["env_key1", "env_key2", "env_key3"]:
            inputs[key] = inputs[key].copy()
            inputs[key]["options"] = env_keys
            
        return inputs

    def _load_env_config(self) -> Dict[str, str]:
        """Load environment configuration from json file"""
        try:
            with open(CONFIG_PATH, 'r') as f:
                return {item["key"]: item["value"] for item in json.load(f)}
        except Exception as e:
            workflow_logger.error(f"Failed to load env config: {str(e)}")
            return {}

    def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            workflow_logger.info("Starting environment key to value conversion")
            env_config = self._load_env_config()
            
            result = {}
            for i in range(1, 4):
                key = f"env_key{i}"
                if key in node_inputs and node_inputs[key]:
                    env_key = node_inputs[key]
                    env_value = env_config.get(env_key, "")
                    result[f"env_value{i}"] = env_value
                    workflow_logger.debug(f"Converted {env_key} to {env_value}")
                else:
                    result[f"env_value{i}"] = ""
            
            return result

        except Exception as e:
            error_msg = f"Environment conversion failed: {str(e)}"
            workflow_logger.error(error_msg)
            return {f"env_value{i}": "" for i in range(1, 4)}
