import json
import traceback
import time
from typing import Dict, Any, Optional

import pandas as pd
from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger

# 尝试导入yfinance，如果不存在则在节点执行时再检查
try:
    import yfinance as yf
except ImportError:
    pass

@register_node
class StockPriceNode(Node):
    """
    股票价格查询节点
    
    这个节点允许查询特定股票的当前价格和基本交易信息。提供实时的或延迟的市场数据，
    包括当前价格、变动百分比、交易量等信息。可用于构建金融仪表板、市场监控或任何
    需要股票价格数据的工作流。
    
    使用场景:
    - 实时市场监控
    - 投资组合跟踪
    - 金融数据分析
    - 自动化交易策略测试
    
    特点:
    - 提供实时或接近实时的股票价格
    - 支持全球主要市场的股票代码
    - 返回丰富的价格相关信息
    - 可以用于单个股票或批量查询
    
    注意:
    - 需要网络连接获取实时数据
    - 某些市场的数据可能有延迟
    - 使用YFinance库，遵循其使用条款和限制
    """
    NAME = "股票价格查询"
    DESCRIPTION = "获取特定股票的当前价格和交易信息"
    CATEGORY = "Finance"
    ICON = "chart-line"

    INPUTS = {
        "symbol": {
            "label": "股票代码",
            "description": "要查询的股票代码（例如：AAPL, MSFT, 600519.SS）",
            "type": "STRING",
            "required": True,
        }
    }

    OUTPUTS = {
        "current_price": {
            "label": "当前价格",
            "description": "股票的当前价格",
            "type": "FLOAT",
        },
        "currency": {
            "label": "货币",
            "description": "价格的货币单位",
            "type": "STRING",
        },
        "change_percent": {
            "label": "变动百分比",
            "description": "价格变动的百分比",
            "type": "FLOAT",
        },
        "volume": {
            "label": "交易量",
            "description": "当前的交易量",
            "type": "INT",
        },
        "market_cap": {
            "label": "市值",
            "description": "公司的市值",
            "type": "FLOAT",
        },
        "success": {
            "label": "成功状态",
            "description": "查询是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果查询失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            symbol = node_inputs.get("symbol", "").strip()
            
            # 验证必填参数
            if not symbol:
                logger.error("No stock symbol provided")
                return {
                    "success": False,
                    "error_message": "No stock symbol provided",
                    "current_price": 0.0,
                    "currency": "",
                    "change_percent": 0.0,
                    "volume": 0,
                    "market_cap": 0.0
                }
                
            # 检查是否安装yfinance
            try:
                import yfinance as yf
            except ImportError:
                error_msg = "The `yfinance` package is not installed. Please install it via `pip install yfinance`."
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "current_price": 0.0,
                    "currency": "",
                    "change_percent": 0.0,
                    "volume": 0,
                    "market_cap": 0.0
                }
                
            # 获取股票信息
            logger.info(f"Fetching stock price for: {symbol}")
            start_time = time.time()
            
            try:
                # 获取股票数据
                stock = yf.Ticker(symbol)
                info = stock.info
                
                if not info:
                    error_msg = f"Could not fetch information for symbol: {symbol}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error_message": error_msg,
                        "current_price": 0.0,
                        "currency": "",
                        "change_percent": 0.0,
                        "volume": 0,
                        "market_cap": 0.0
                    }
                
                # 提取所需信息
                current_price = info.get("regularMarketPrice", info.get("currentPrice", 0.0))
                currency = info.get("currency", "USD")
                change_percent = info.get("regularMarketChangePercent", 0.0)
                volume = info.get("regularMarketVolume", 0)
                market_cap = info.get("marketCap", 0.0)
                
                elapsed = time.time() - start_time
                logger.info(f"Stock data fetched in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "current_price": current_price,
                    "currency": currency,
                    "change_percent": change_percent,
                    "volume": volume,
                    "market_cap": market_cap,
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error fetching stock data: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "current_price": 0.0,
                    "currency": "",
                    "change_percent": 0.0,
                    "volume": 0,
                    "market_cap": 0.0
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Stock Price node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "current_price": 0.0,
                "currency": "",
                "change_percent": 0.0,
                "volume": 0,
                "market_cap": 0.0
            }


@register_node
class CompanyInfoNode(Node):
    """
    公司信息查询节点
    
    这个节点允许查询特定公司的详细信息和概况。提供公司基本资料、行业分类、财务
    亮点和业务描述等信息。可用于公司研究、投资分析或任何需要公司概览数据的工作流。
    
    使用场景:
    - 投资研究与分析
    - 公司背景调查
    - 竞争对手分析
    - 行业研究
    
    特点:
    - 提供公司基本资料（名称、地址、行业等）
    - 包含关键财务指标
    - 返回业务描述和公司简介
    - 提供分析师评级和推荐
    
    注意:
    - 需要网络连接获取最新数据
    - 信息更新频率取决于数据源
    - 使用YFinance库，遵循其使用条款和限制
    """
    NAME = "公司信息查询"
    DESCRIPTION = "获取特定公司的详细信息和概况"
    CATEGORY = "Finance"
    ICON = "building"

    INPUTS = {
        "symbol": {
            "label": "股票代码",
            "description": "要查询的公司股票代码（例如：AAPL, MSFT, 600519.SS）",
            "type": "STRING",
            "required": True,
        }
    }

    OUTPUTS = {
        "company_name": {
            "label": "公司名称",
            "description": "公司的完整名称",
            "type": "STRING",
        },
        "sector": {
            "label": "行业部门",
            "description": "公司所属的行业部门",
            "type": "STRING",
        },
        "industry": {
            "label": "行业",
            "description": "公司所属的具体行业",
            "type": "STRING",
        },
        "employee_count": {
            "label": "员工人数",
            "description": "公司的员工总数",
            "type": "INT",
        },
        "website": {
            "label": "网站",
            "description": "公司的官方网站",
            "type": "STRING",
        },
        "business_summary": {
            "label": "业务摘要",
            "description": "公司业务的详细描述",
            "type": "STRING",
        },
        "company_officers": {
            "label": "公司高管",
            "description": "公司高管信息（JSON格式）",
            "type": "STRING",
        },
        "detailed_info": {
            "label": "详细信息",
            "description": "包含所有公司信息的JSON格式数据",
            "type": "STRING",
        },
        "success": {
            "label": "成功状态",
            "description": "查询是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果查询失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            symbol = node_inputs.get("symbol", "").strip()
            
            # 验证必填参数
            if not symbol:
                logger.error("No stock symbol provided")
                return {
                    "success": False,
                    "error_message": "No stock symbol provided",
                    "company_name": "",
                    "sector": "",
                    "industry": "",
                    "employee_count": 0,
                    "website": "",
                    "business_summary": "",
                    "company_officers": "[]",
                    "detailed_info": "{}"
                }
                
            # 检查是否安装yfinance
            try:
                import yfinance as yf
            except ImportError:
                error_msg = "The `yfinance` package is not installed. Please install it via `pip install yfinance`."
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "company_name": "",
                    "sector": "",
                    "industry": "",
                    "employee_count": 0,
                    "website": "",
                    "business_summary": "",
                    "company_officers": "[]",
                    "detailed_info": "{}"
                }
                
            # 获取公司信息
            logger.info(f"Fetching company info for: {symbol}")
            start_time = time.time()
            
            try:
                # 获取公司数据
                stock = yf.Ticker(symbol)
                info = stock.info
                
                if not info:
                    error_msg = f"Could not fetch information for symbol: {symbol}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error_message": error_msg,
                        "company_name": "",
                        "sector": "",
                        "industry": "",
                        "employee_count": 0,
                        "website": "",
                        "business_summary": "",
                        "company_officers": "[]",
                        "detailed_info": "{}"
                    }
                
                # 提取基本信息
                company_name = info.get("longName", info.get("shortName", ""))
                sector = info.get("sector", "")
                industry = info.get("industry", "")
                employee_count = info.get("fullTimeEmployees", 0)
                website = info.get("website", "")
                business_summary = info.get("longBusinessSummary", "")
                
                # 提取公司高管信息
                company_officers = info.get("companyOfficers", [])
                company_officers_json = json.dumps(company_officers, ensure_ascii=False)
                
                # 将所有信息转换为JSON
                detailed_info_json = json.dumps(info, ensure_ascii=False)
                
                elapsed = time.time() - start_time
                logger.info(f"Company info fetched in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "company_name": company_name,
                    "sector": sector,
                    "industry": industry,
                    "employee_count": employee_count,
                    "website": website,
                    "business_summary": business_summary,
                    "company_officers": company_officers_json,
                    "detailed_info": detailed_info_json,
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error fetching company info: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "company_name": "",
                    "sector": "",
                    "industry": "",
                    "employee_count": 0,
                    "website": "",
                    "business_summary": "",
                    "company_officers": "[]",
                    "detailed_info": "{}"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Company Info node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "company_name": "",
                "sector": "",
                "industry": "",
                "employee_count": 0,
                "website": "",
                "business_summary": "",
                "company_officers": "[]",
                "detailed_info": "{}"
            }


@register_node
class StockHistoricalDataNode(Node):
    """
    股票历史数据查询节点
    
    这个节点允许查询特定股票的历史价格和交易数据。提供不同时间段和间隔的历史数据，
    包括开盘价、收盘价、最高价、最低价和交易量等信息。可用于技术分析、回测交易策略
    或任何需要历史股票数据的工作流。
    
    使用场景:
    - 技术分析和图表研究
    - 回测交易策略
    - 市场趋势分析
    - 波动性研究
    
    特点:
    - 支持多种时间范围（天、周、月、年）
    - 可设置不同的数据间隔
    - 返回完整的OHLCV数据
    - 支持全球主要市场的股票
    
    注意:
    - 历史数据可能受数据源限制
    - 某些市场或较短间隔可能数据不完整
    - 使用YFinance库，遵循其使用条款和限制
    """
    NAME = "股票历史数据查询"
    DESCRIPTION = "获取特定股票的历史价格和交易数据"
    CATEGORY = "Finance"
    ICON = "chart-bar"

    INPUTS = {
        "symbol": {
            "label": "股票代码",
            "description": "要查询的股票代码（例如：AAPL, MSFT, 600519.SS）",
            "type": "STRING",
            "required": True,
        },
        "period": {
            "label": "时间段",
            "description": "要获取的历史数据时间段",
            "type": "STRING",
            "default": "1mo",
            "required": False,
        },
        "interval": {
            "label": "间隔",
            "description": "数据点之间的间隔",
            "type": "STRING",
            "default": "1d",
            "required": False,
        },
        "start_date": {
            "label": "开始日期",
            "description": "获取数据的开始日期（格式：YYYY-MM-DD，优先于时间段设置）",
            "type": "STRING",
            "required": False,
        },
        "end_date": {
            "label": "结束日期",
            "description": "获取数据的结束日期（格式：YYYY-MM-DD，优先于时间段设置）",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "historical_data": {
            "label": "历史数据",
            "description": "JSON格式的历史价格数据",
            "type": "STRING",
        },
        "data_points": {
            "label": "数据点数量",
            "description": "获取到的数据点数量",
            "type": "INT",
        },
        "date_range": {
            "label": "日期范围",
            "description": "数据覆盖的日期范围",
            "type": "STRING",
        },
        "highest_price": {
            "label": "最高价",
            "description": "时间段内的最高价",
            "type": "FLOAT",
        },
        "lowest_price": {
            "label": "最低价",
            "description": "时间段内的最低价",
            "type": "FLOAT",
        },
        "average_volume": {
            "label": "平均交易量",
            "description": "时间段内的平均交易量",
            "type": "FLOAT",
        },
        "success": {
            "label": "成功状态",
            "description": "查询是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果查询失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            symbol = node_inputs.get("symbol", "").strip()
            period = node_inputs.get("period", "1mo")
            interval = node_inputs.get("interval", "1d")
            start_date = node_inputs.get("start_date", "").strip()
            end_date = node_inputs.get("end_date", "").strip()
            
            # 验证必填参数
            if not symbol:
                logger.error("No stock symbol provided")
                return {
                    "success": False,
                    "error_message": "No stock symbol provided",
                    "historical_data": "{}",
                    "data_points": 0,
                    "date_range": "",
                    "highest_price": 0.0,
                    "lowest_price": 0.0,
                    "average_volume": 0.0
                }
                
            # 检查是否安装yfinance
            try:
                import yfinance as yf
            except ImportError:
                error_msg = "The `yfinance` package is not installed. Please install it via `pip install yfinance`."
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "historical_data": "{}",
                    "data_points": 0,
                    "date_range": "",
                    "highest_price": 0.0,
                    "lowest_price": 0.0,
                    "average_volume": 0.0
                }
                
            # 验证时间段参数
            valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
            if period not in valid_periods:
                logger.warning(f"Invalid period '{period}', defaulting to '1mo'")
                period = "1mo"
                
            # 验证间隔参数
            valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
            if interval not in valid_intervals:
                logger.warning(f"Invalid interval '{interval}', defaulting to '1d'")
                interval = "1d"
                
            # 获取历史数据
            logger.info(f"Fetching historical data for: {symbol}")
            start_time = time.time()
            
            try:
                # 获取股票数据
                stock = yf.Ticker(symbol)
                
                # 根据提供的参数决定是使用日期范围还是时间段
                if start_date and end_date:
                    logger.info(f"Using date range: {start_date} to {end_date}")
                    historical_data = stock.history(start=start_date, end=end_date, interval=interval)
                else:
                    logger.info(f"Using period: {period} with interval: {interval}")
                    historical_data = stock.history(period=period, interval=interval)
                
                if historical_data.empty:
                    error_msg = f"No historical data found for symbol: {symbol}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error_message": error_msg,
                        "historical_data": "{}",
                        "data_points": 0,
                        "date_range": "",
                        "highest_price": 0.0,
                        "lowest_price": 0.0,
                        "average_volume": 0.0
                    }
                
                # 计算统计数据
                data_points = len(historical_data)
                if data_points > 0:
                    date_range = f"{historical_data.index[0].strftime('%Y-%m-%d')} to {historical_data.index[-1].strftime('%Y-%m-%d')}"
                    highest_price = float(historical_data["High"].max())
                    lowest_price = float(historical_data["Low"].min())
                    average_volume = float(historical_data["Volume"].mean())
                else:
                    date_range = ""
                    highest_price = 0.0
                    lowest_price = 0.0
                    average_volume = 0.0
                
                # 将数据转换为JSON
                historical_data_json = historical_data.reset_index().to_json(orient="records", date_format="iso")
                
                elapsed = time.time() - start_time
                logger.info(f"Historical data fetched in {elapsed:.2f}s, {data_points} data points")
                
                return {
                    "success": True,
                    "historical_data": historical_data_json,
                    "data_points": data_points,
                    "date_range": date_range,
                    "highest_price": highest_price,
                    "lowest_price": lowest_price,
                    "average_volume": average_volume,
                    "error_message": ""
                }
                
            except Exception as e:
                error_msg = f"Error fetching historical data: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "historical_data": "{}",
                    "data_points": 0,
                    "date_range": "",
                    "highest_price": 0.0,
                    "lowest_price": 0.0,
                    "average_volume": 0.0
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Stock Historical Data node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "historical_data": "{}",
                "data_points": 0,
                "date_range": "",
                "highest_price": 0.0,
                "lowest_price": 0.0,
                "average_volume": 0.0
            }


# 测试代码
if __name__ == "__main__":
    import asyncio
    
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
    
    # 创建节点实例
    price_node = StockPriceNode()
    info_node = CompanyInfoNode()
    history_node = StockHistoricalDataNode()
    
    # 测试股票价格节点
    print("\n测试股票价格节点:")
    result = asyncio.run(price_node.execute({
        "symbol": "AAPL"
    }, logger))
    
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"当前价格: {result['current_price']} {result['currency']}")
        print(f"变动百分比: {result['change_percent']}%")
        print(f"交易量: {result['volume']}")
        print(f"市值: {result['market_cap']}")
    else:
        print(f"错误: {result['error_message']}")
    
    # 测试公司信息节点
    print("\n测试公司信息节点:")
    result = asyncio.run(info_node.execute({
        "symbol": "MSFT"
    }, logger))
    
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"公司名称: {result['company_name']}")
        print(f"行业: {result['sector']} / {result['industry']}")
        print(f"员工人数: {result['employee_count']}")
        print(f"网站: {result['website']}")
        print(f"业务摘要: {result['business_summary'][:100]}...")
    else:
        print(f"错误: {result['error_message']}")
    
    # 测试历史数据节点
    print("\n测试历史数据节点:")
    result = asyncio.run(history_node.execute({
        "symbol": "GOOG",
        "period": "1mo",
        "interval": "1d"
    }, logger))
    
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"数据点数量: {result['data_points']}")
        print(f"日期范围: {result['date_range']}")
        print(f"最高价: {result['highest_price']}")
        print(f"最低价: {result['lowest_price']}")
        print(f"平均交易量: {result['average_volume']}")
    else:
        print(f"错误: {result['error_message']}") 