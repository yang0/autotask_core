import json
import time
import traceback
from typing import Dict, Any, List, Optional
import os
import csv
import pandas as pd
import numpy as np
from io import StringIO

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger


@register_node
class CSVProcessorNode(Node):
    """
    CSV数据处理节点
    
    这个节点允许加载、处理和转换CSV数据。它提供了过滤、排序、分组等多种数据操作功能，
    以及计算统计信息和执行基本数据分析的能力。处理后的数据可以导出为新的CSV文件或
    返回为JSON格式供工作流中的其他节点使用。
    
    使用场景:
    - 数据清洗和预处理
    - 数据转换和重组
    - 执行数据分析和统计
    - 数据过滤和提取
    
    特点:
    - 支持多种数据操作（过滤、排序、分组等）
    - 可以执行基本的数据分析和统计
    - 支持数据导出为CSV或JSON格式
    - 可以处理大型数据集
    
    注意:
    - 大型文件可能会导致内存使用增加
    - 操作顺序会影响最终结果
    - 部分复杂操作可能需要Python代码表达式
    """
    NAME = "CSV处理器"
    DESCRIPTION = "加载、处理和转换CSV数据"
    CATEGORY = "Data"
    ICON = "table"

    INPUTS = {
        "input_file": {
            "label": "输入文件",
            "description": "要处理的CSV文件路径",
            "type": "STRING",
            "required": True,
        },
        "output_file": {
            "label": "输出文件",
            "description": "保存处理结果的CSV文件路径（如果留空则不保存文件）",
            "type": "STRING",
            "required": False,
        },
        "delimiter": {
            "label": "分隔符",
            "description": "CSV文件中使用的分隔符",
            "type": "STRING",
            "default": ",",
            "required": False,
        },
        "encoding": {
            "label": "编码",
            "description": "CSV文件的编码",
            "type": "STRING",
            "default": "utf-8",
            "required": False,
        },
        "operations": {
            "label": "操作",
            "description": "要执行的操作（JSON格式，如：[{\"type\":\"filter\",\"column\":\"age\",\"operator\":\">\",\"value\":30}]）",
            "type": "STRING",
            "required": False,
        },
        "select_columns": {
            "label": "选择列",
            "description": "要包含在结果中的列（逗号分隔，留空则包含所有列）",
            "type": "STRING",
            "required": False,
        },
        "max_rows": {
            "label": "最大行数",
            "description": "要处理的最大行数（0表示无限制）",
            "type": "INT",
            "default": 0,
            "required": False,
        },
        "skip_header": {
            "label": "跳过头部",
            "description": "是否跳过文件头行",
            "type": "BOOL",
            "default": False,
            "required": False,
        }
    }

    OUTPUTS = {
        "processed_data": {
            "label": "处理后的数据",
            "description": "处理后的数据（JSON格式）",
            "type": "STRING",
        },
        "row_count": {
            "label": "行数",
            "description": "处理后的数据行数",
            "type": "INT",
        },
        "column_count": {
            "label": "列数",
            "description": "处理后的数据列数",
            "type": "INT",
        },
        "summary": {
            "label": "摘要",
            "description": "数据的统计摘要（JSON格式）",
            "type": "STRING",
        },
        "success": {
            "label": "成功状态",
            "description": "操作是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果操作失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            input_file = node_inputs.get("input_file", "").strip()
            output_file = node_inputs.get("output_file", "").strip()
            delimiter = node_inputs.get("delimiter", ",")
            encoding = node_inputs.get("encoding", "utf-8")
            operations_json = node_inputs.get("operations", "[]")
            select_columns_str = node_inputs.get("select_columns", "")
            max_rows = node_inputs.get("max_rows", 0)
            skip_header = node_inputs.get("skip_header", False)
            
            # 验证必填参数
            if not input_file:
                logger.error("No input file provided")
                return {
                    "success": False,
                    "error_message": "No input file provided",
                    "processed_data": "[]",
                    "row_count": 0,
                    "column_count": 0,
                    "summary": "{}"
                }
                
            # 检查文件是否存在
            if not os.path.exists(input_file):
                error_msg = f"Input file does not exist: {input_file}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "processed_data": "[]",
                    "row_count": 0,
                    "column_count": 0,
                    "summary": "{}"
                }
                
            # 解析操作
            try:
                operations = json.loads(operations_json) if operations_json.strip() else []
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse operations JSON: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "processed_data": "[]",
                    "row_count": 0,
                    "column_count": 0,
                    "summary": "{}"
                }
                
            # 解析选择列
            select_columns = [col.strip() for col in select_columns_str.split(",") if col.strip()] if select_columns_str else None
            
            # 读取CSV文件
            logger.info(f"Reading CSV file: {input_file}")
            start_time = time.time()
            
            try:
                # 使用pandas读取CSV
                read_csv_kwargs = {
                    "filepath_or_buffer": input_file,
                    "sep": delimiter,
                    "encoding": encoding,
                    "header": None if skip_header else 0,
                }
                
                if max_rows > 0:
                    read_csv_kwargs["nrows"] = max_rows
                    
                df = pd.read_csv(**read_csv_kwargs)
                
                # 处理数据
                # 1. 选择列
                if select_columns:
                    try:
                        df = df[select_columns]
                    except KeyError as e:
                        logger.warning(f"Some columns in select_columns do not exist: {str(e)}")
                        # 只选择存在的列
                        existing_columns = [col for col in select_columns if col in df.columns]
                        if existing_columns:
                            df = df[existing_columns]
                        
                # 2. 执行操作
                for operation in operations:
                    op_type = operation.get("type", "").lower()
                    
                    if op_type == "filter":
                        column = operation.get("column", "")
                        operator = operation.get("operator", "==")
                        value = operation.get("value")
                        
                        if column and column in df.columns:
                            if operator == "==":
                                df = df[df[column] == value]
                            elif operator == "!=":
                                df = df[df[column] != value]
                            elif operator == ">":
                                df = df[df[column] > value]
                            elif operator == ">=":
                                df = df[df[column] >= value]
                            elif operator == "<":
                                df = df[df[column] < value]
                            elif operator == "<=":
                                df = df[df[column] <= value]
                            elif operator == "contains":
                                df = df[df[column].astype(str).str.contains(str(value), na=False)]
                            elif operator == "startswith":
                                df = df[df[column].astype(str).str.startswith(str(value), na=False)]
                            elif operator == "endswith":
                                df = df[df[column].astype(str).str.endswith(str(value), na=False)]
                                
                    elif op_type == "sort":
                        column = operation.get("column", "")
                        ascending = operation.get("ascending", True)
                        
                        if column and column in df.columns:
                            df = df.sort_values(by=column, ascending=ascending)
                            
                    elif op_type == "group":
                        column = operation.get("column", "")
                        agg_column = operation.get("agg_column", "")
                        agg_func = operation.get("agg_func", "sum")
                        
                        if column and column in df.columns and agg_column and agg_column in df.columns:
                            grouped = df.groupby(column)
                            
                            if agg_func == "sum":
                                df = grouped[agg_column].sum().reset_index()
                            elif agg_func == "mean":
                                df = grouped[agg_column].mean().reset_index()
                            elif agg_func == "count":
                                df = grouped[agg_column].count().reset_index()
                            elif agg_func == "min":
                                df = grouped[agg_column].min().reset_index()
                            elif agg_func == "max":
                                df = grouped[agg_column].max().reset_index()
                                
                    elif op_type == "dropna":
                        column = operation.get("column", "")
                        
                        if column and column in df.columns:
                            df = df.dropna(subset=[column])
                        else:
                            df = df.dropna()
                            
                    elif op_type == "fillna":
                        column = operation.get("column", "")
                        value = operation.get("value", 0)
                        
                        if column and column in df.columns:
                            df[column] = df[column].fillna(value)
                            
                    elif op_type == "rename":
                        old_name = operation.get("old_name", "")
                        new_name = operation.get("new_name", "")
                        
                        if old_name and new_name and old_name in df.columns:
                            df = df.rename(columns={old_name: new_name})
                            
                    elif op_type == "drop_columns":
                        columns = operation.get("columns", [])
                        
                        if columns:
                            df = df.drop(columns=[col for col in columns if col in df.columns], errors='ignore')
                
                # 保存处理后的数据到CSV文件
                if output_file:
                    output_dir = os.path.dirname(output_file)
                    if output_dir and not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                        
                    df.to_csv(output_file, index=False, encoding=encoding, sep=delimiter)
                    logger.info(f"Processed data saved to: {output_file}")
                
                # 计算数据摘要
                row_count = len(df)
                column_count = len(df.columns)
                
                # 生成统计摘要
                summary = {}
                for column in df.columns:
                    try:
                        if pd.api.types.is_numeric_dtype(df[column]):
                            summary[column] = {
                                "min": float(df[column].min()) if not pd.isna(df[column].min()) else None,
                                "max": float(df[column].max()) if not pd.isna(df[column].max()) else None,
                                "mean": float(df[column].mean()) if not pd.isna(df[column].mean()) else None,
                                "median": float(df[column].median()) if not pd.isna(df[column].median()) else None,
                                "std": float(df[column].std()) if not pd.isna(df[column].std()) else None,
                                "null_count": int(df[column].isna().sum())
                            }
                        else:
                            # 非数值列只计算唯一值数量和空值数量
                            summary[column] = {
                                "unique_count": int(df[column].nunique()),
                                "null_count": int(df[column].isna().sum()),
                                "most_common": df[column].value_counts().index[0] if not df[column].empty and df[column].nunique() > 0 else None
                            }
                    except Exception as e:
                        logger.warning(f"Failed to generate summary for column {column}: {str(e)}")
                        summary[column] = {"error": str(e)}
                
                elapsed = time.time() - start_time
                logger.info(f"CSV processing completed in {elapsed:.2f}s, {row_count} rows processed")
                
                # 将DataFrame转换为JSON
                processed_data_json = df.to_json(orient="records")
                summary_json = json.dumps(summary, ensure_ascii=False)
                
                return {
                    "success": True,
                    "processed_data": processed_data_json,
                    "row_count": row_count,
                    "column_count": column_count,
                    "summary": summary_json,
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error processing CSV file: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "processed_data": "[]",
                    "row_count": 0,
                    "column_count": 0,
                    "summary": "{}"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in CSV Processor node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "processed_data": "[]",
                "row_count": 0,
                "column_count": 0,
                "summary": "{}"
            }


@register_node
class JSONProcessorNode(Node):
    """
    JSON数据处理节点
    
    这个节点允许加载、处理和转换JSON数据。它提供了提取、过滤、转换等多种数据操作功能，
    并支持JSON路径表达式进行精确数据访问。处理后的数据可以保存为新的JSON文件或用于
    工作流中的后续处理。
    
    使用场景:
    - API响应处理
    - 配置文件处理
    - 数据转换和结构化
    - JSON数据提取和过滤
    
    特点:
    - 支持JSON路径表达式进行精确数据访问
    - 可以进行数据提取、过滤和转换
    - 支持扁平化嵌套结构
    - 可以合并多个JSON对象
    
    注意:
    - 复杂的嵌套结构可能需要多步处理
    - JSON路径表达式的语法需要正确
    - 大型JSON文件可能会占用大量内存
    """
    NAME = "JSON处理器"
    DESCRIPTION = "加载、处理和转换JSON数据"
    CATEGORY = "Data"
    ICON = "code-json"

    INPUTS = {
        "input_data": {
            "label": "输入数据",
            "description": "要处理的JSON数据（文件路径或JSON字符串）",
            "type": "STRING",
            "required": True,
        },
        "output_file": {
            "label": "输出文件",
            "description": "保存处理结果的JSON文件路径（如果留空则不保存文件）",
            "type": "STRING",
            "required": False,
        },
        "is_file_path": {
            "label": "是否为文件路径",
            "description": "输入是文件路径还是JSON字符串",
            "type": "BOOL",
            "default": True,
            "required": False,
        },
        "operations": {
            "label": "操作",
            "description": "要执行的操作（JSON格式，如：[{\"type\":\"extract\",\"path\":\"$.data.items\"}]）",
            "type": "STRING",
            "required": False,
        },
        "pretty_print": {
            "label": "美化输出",
            "description": "是否美化输出的JSON",
            "type": "BOOL",
            "default": True,
            "required": False,
        }
    }

    OUTPUTS = {
        "processed_data": {
            "label": "处理后的数据",
            "description": "处理后的JSON数据",
            "type": "STRING",
        },
        "is_array": {
            "label": "是否为数组",
            "description": "处理后的数据是否为数组",
            "type": "BOOL",
        },
        "element_count": {
            "label": "元素数量",
            "description": "如果结果是数组，返回元素数量",
            "type": "INT",
        },
        "success": {
            "label": "成功状态",
            "description": "操作是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果操作失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            input_data = node_inputs.get("input_data", "").strip()
            output_file = node_inputs.get("output_file", "").strip()
            is_file_path = node_inputs.get("is_file_path", True)
            operations_json = node_inputs.get("operations", "[]")
            pretty_print = node_inputs.get("pretty_print", True)
            
            # 验证必填参数
            if not input_data:
                logger.error("No input data provided")
                return {
                    "success": False,
                    "error_message": "No input data provided",
                    "processed_data": "{}",
                    "is_array": False,
                    "element_count": 0
                }
                
            # 解析操作
            try:
                operations = json.loads(operations_json) if operations_json.strip() else []
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse operations JSON: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "processed_data": "{}",
                    "is_array": False,
                    "element_count": 0
                }
                
            # 加载JSON数据
            logger.info("Loading JSON data")
            start_time = time.time()
            
            try:
                # 从文件或字符串加载JSON
                if is_file_path:
                    if not os.path.exists(input_data):
                        error_msg = f"Input file does not exist: {input_data}"
                        logger.error(error_msg)
                        return {
                            "success": False,
                            "error_message": error_msg,
                            "processed_data": "{}",
                            "is_array": False,
                            "element_count": 0
                        }
                        
                    with open(input_data, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = json.loads(input_data)
                    
                # 处理数据
                for operation in operations:
                    op_type = operation.get("type", "").lower()
                    
                    if op_type == "extract":
                        path = operation.get("path", "")
                        if path:
                            try:
                                import jsonpath_ng.ext as jsonpath
                                jsonpath_expr = jsonpath.parse(path)
                                matches = [match.value for match in jsonpath_expr.find(data)]
                                
                                if matches:
                                    if len(matches) == 1:
                                        data = matches[0]
                                    else:
                                        data = matches
                                else:
                                    logger.warning(f"No matches found for path: {path}")
                            except ImportError:
                                logger.error("jsonpath-ng package not installed. Please install it to use extract operation.")
                            except Exception as e:
                                logger.warning(f"Error extracting with path {path}: {str(e)}")
                                
                    elif op_type == "filter":
                        if isinstance(data, list):
                            field = operation.get("field", "")
                            operator = operation.get("operator", "==")
                            value = operation.get("value")
                            
                            if field:
                                filtered_data = []
                                for item in data:
                                    if isinstance(item, dict) and field in item:
                                        item_value = item[field]
                                        
                                        if operator == "==" and item_value == value:
                                            filtered_data.append(item)
                                        elif operator == "!=" and item_value != value:
                                            filtered_data.append(item)
                                        elif operator == ">" and item_value > value:
                                            filtered_data.append(item)
                                        elif operator == ">=" and item_value >= value:
                                            filtered_data.append(item)
                                        elif operator == "<" and item_value < value:
                                            filtered_data.append(item)
                                        elif operator == "<=" and item_value <= value:
                                            filtered_data.append(item)
                                        elif operator == "contains" and str(value) in str(item_value):
                                            filtered_data.append(item)
                                            
                                data = filtered_data
                        else:
                            logger.warning("Filter operation can only be applied to arrays")
                            
                    elif op_type == "transform":
                        transform_type = operation.get("transform_type", "")
                        
                        if transform_type == "flatten":
                            # 扁平化嵌套数组
                            if isinstance(data, list):
                                flat_data = []
                                for item in data:
                                    if isinstance(item, list):
                                        flat_data.extend(item)
                                    else:
                                        flat_data.append(item)
                                data = flat_data
                                
                        elif transform_type == "keys":
                            # 提取所有键
                            if isinstance(data, dict):
                                data = list(data.keys())
                            elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                                # 如果是字典列表，提取每个字典的键
                                all_keys = set()
                                for item in data:
                                    all_keys.update(item.keys())
                                data = list(all_keys)
                                
                        elif transform_type == "values":
                            # 提取所有值
                            if isinstance(data, dict):
                                data = list(data.values())
                    
                    elif op_type == "sort":
                        if isinstance(data, list):
                            key = operation.get("key", "")
                            reverse = operation.get("reverse", False)
                            
                            if key and all(isinstance(item, dict) and key in item for item in data):
                                data = sorted(data, key=lambda x: x[key], reverse=reverse)
                            elif not key and all(not isinstance(item, dict) for item in data):
                                data = sorted(data, reverse=reverse)
                                
                    elif op_type == "limit":
                        if isinstance(data, list):
                            limit = operation.get("limit", 10)
                            data = data[:limit]
                
                # 保存处理后的数据到JSON文件
                if output_file:
                    output_dir = os.path.dirname(output_file)
                    if output_dir and not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                        
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4 if pretty_print else None)
                    logger.info(f"Processed data saved to: {output_file}")
                
                # 确定结果类型和计数
                is_array = isinstance(data, list)
                element_count = len(data) if is_array else 0
                
                elapsed = time.time() - start_time
                logger.info(f"JSON processing completed in {elapsed:.2f}s")
                
                # 转换为JSON字符串
                processed_data_json = json.dumps(data, ensure_ascii=False, indent=4 if pretty_print else None)
                
                return {
                    "success": True,
                    "processed_data": processed_data_json,
                    "is_array": is_array,
                    "element_count": element_count,
                    "error_message": ""
                }
                
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "processed_data": "{}",
                    "is_array": False,
                    "element_count": 0
                }
                
            except Exception as e:
                error_msg = f"Error processing JSON data: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "processed_data": "{}",
                    "is_array": False,
                    "element_count": 0
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in JSON Processor node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "processed_data": "{}",
                "is_array": False,
                "element_count": 0
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
    
    # Create a sample CSV file for testing
    sample_csv_path = "sample_data.csv"
    with open(sample_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Age", "City"])
        writer.writerow(["Alice", 30, "New York"])
        writer.writerow(["Bob", 25, "Los Angeles"])
        writer.writerow(["Charlie", 35, "Chicago"])
    
    # Test CSVProcessorNode
    print("\nTesting CSVProcessorNode:")
    csv_node = CSVProcessorNode()
    
    # Define operations to filter for people older than 25
    operations = [{"type": "filter", "column": "Age", "operator": ">", "value": 25}]
    operations_json = json.dumps(operations)
    
    result = asyncio.run(csv_node.execute({
        "input_file": sample_csv_path,
        "operations": operations_json,
        "select_columns": "Name,Age"
    }, logger))
    
    print(f"Success: {result['success']}")
    print(f"Row count: {result['row_count']}")
    print(f"Processed data: {result['processed_data']}")
    
    # Create a sample JSON file for testing
    sample_json_path = "sample_data.json"
    sample_data = {
        "people": [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "Los Angeles"},
            {"name": "Charlie", "age": 35, "city": "Chicago"}
        ],
        "metadata": {
            "count": 3,
            "source": "test"
        }
    }
    
    with open(sample_json_path, 'w') as f:
        json.dump(sample_data, f)
    
    # Test JSONProcessorNode
    print("\nTesting JSONProcessorNode:")
    json_node = JSONProcessorNode()
    
    # Define operations to extract people array
    operations = [{"type": "extract", "path": "$.people"}]
    operations_json = json.dumps(operations)
    
    result = asyncio.run(json_node.execute({
        "input_data": sample_json_path,
        "is_file_path": True,
        "operations": operations_json
    }, logger))
    
    print(f"Success: {result['success']}")
    print(f"Is array: {result['is_array']}")
    print(f"Element count: {result['element_count']}")
    print(f"Processed data: {result['processed_data']}")
    
    # Clean up test files
    import os
    os.remove(sample_csv_path)
    os.remove(sample_json_path) 