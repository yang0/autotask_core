import json
import os
import datetime
import traceback
import time
from typing import Dict, Any, List, Optional

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger

# 尝试导入谷歌日历依赖，如果不存在则在节点执行时再检查
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    pass

# 谷歌日历API所需的权限范围
SCOPES = ["https://www.googleapis.com/auth/calendar"]

@register_node
class GoogleCalendarEventsNode(Node):
    """
    谷歌日历事件查询节点
    
    这个节点允许查询谷歌日历中的事件。可以设置时间范围和限制返回的事件数量。
    节点需要使用OAuth 2.0进行认证，因此需要提供凭据文件路径和令牌文件路径。
    可用于获取日程安排、会议时间或任何需要日历数据的工作流。
    
    使用场景:
    - 自动化日程管理
    - 日程分析和报告
    - 会议提醒和通知
    - 工作流程日程协调
    
    特点:
    - 支持查询指定日期范围的事件
    - 可以限制返回的事件数量
    - 提供完整的事件详情，包括时间、地点和参与者
    - 使用OAuth 2.0安全认证
    
    注意:
    - 需要有效的谷歌API凭据
    - 首次运行时需要用户授权
    - 遵循谷歌API使用限制和条款
    """
    NAME = "谷歌日历事件查询"
    DESCRIPTION = "查询谷歌日历中的事件"
    CATEGORY = "Calendar"
    ICON = "calendar-check"

    INPUTS = {
        "credentials_path": {
            "label": "凭据文件路径",
            "description": "谷歌API凭据文件(credentials.json)的路径",
            "type": "STRING",
            "required": True,
        },
        "token_path": {
            "label": "令牌文件路径",
            "description": "存储认证令牌的文件(token.json)路径",
            "type": "STRING",
            "required": True,
        },
        "limit": {
            "label": "事件数量限制",
            "description": "要返回的最大事件数量",
            "type": "INT",
            "default": 10,
            "required": False,
        },
        "start_date": {
            "label": "开始日期",
            "description": "查询事件的开始日期（ISO格式：YYYY-MM-DD）",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "events": {
            "label": "事件列表",
            "description": "JSON格式的事件列表",
            "type": "STRING",
        },
        "events_count": {
            "label": "事件数量",
            "description": "返回的事件数量",
            "type": "INT",
        },
        "next_event": {
            "label": "下一个事件",
            "description": "最近的下一个事件的详细信息",
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
            credentials_path = node_inputs.get("credentials_path", "").strip()
            token_path = node_inputs.get("token_path", "").strip()
            limit = node_inputs.get("limit", 10)
            start_date = node_inputs.get("start_date", "").strip()
            
            # 验证必填参数
            if not credentials_path:
                logger.error("No credentials path provided")
                return {
                    "success": False,
                    "error_message": "No credentials path provided",
                    "events": "[]",
                    "events_count": 0,
                    "next_event": "{}"
                }
                
            if not token_path:
                logger.error("No token path provided")
                return {
                    "success": False,
                    "error_message": "No token path provided",
                    "events": "[]",
                    "events_count": 0,
                    "next_event": "{}"
                }
                
            # 检查文件是否存在
            if not os.path.exists(credentials_path):
                error_msg = f"Credentials file does not exist: {credentials_path}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "events": "[]",
                    "events_count": 0,
                    "next_event": "{}"
                }
                
            # 检查是否安装所需的包
            try:
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from google_auth_oauthlib.flow import InstalledAppFlow
                from googleapiclient.discovery import build
                from googleapiclient.errors import HttpError
            except ImportError:
                error_msg = "Required packages not installed. Please install using `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "events": "[]",
                    "events_count": 0,
                    "next_event": "{}"
                }
                
            # 处理日期
            if not start_date:
                start_datetime = datetime.datetime.now(datetime.timezone.utc).isoformat()
            else:
                try:
                    # 将日期字符串转换为datetime对象
                    date_obj = datetime.date.fromisoformat(start_date)
                    # 创建该日期的午夜时间
                    start_datetime = datetime.datetime.combine(
                        date_obj, 
                        datetime.time.min, 
                        tzinfo=datetime.timezone.utc
                    ).isoformat()
                except ValueError:
                    error_msg = f"Invalid date format: {start_date}. Please use YYYY-MM-DD format."
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error_message": error_msg,
                        "events": "[]",
                        "events_count": 0,
                        "next_event": "{}"
                    }
            
            logger.info(f"Fetching Google Calendar events from {start_date or 'now'}")
            start_time = time.time()
            
            # 认证和获取事件
            try:
                # 初始化凭据
                creds = None
                if os.path.exists(token_path):
                    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                    
                # 如果没有有效的凭据，或者凭据已过期
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    # 保存凭据供下次使用
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())
                
                # 构建服务
                service = build("calendar", "v3", credentials=creds)
                
                # 获取事件
                events_result = service.events().list(
                    calendarId="primary",
                    timeMin=start_datetime,
                    maxResults=limit,
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()
                
                events = events_result.get("items", [])
                events_count = len(events)
                
                # 准备返回数据
                if events_count > 0:
                    next_event = events[0]
                    next_event_json = json.dumps(next_event, ensure_ascii=False)
                else:
                    next_event_json = "{}"
                
                events_json = json.dumps(events, ensure_ascii=False)
                
                elapsed = time.time() - start_time
                logger.info(f"Retrieved {events_count} events in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "events": events_json,
                    "events_count": events_count,
                    "next_event": next_event_json,
                    "error_message": ""
                }
                
            except HttpError as e:
                error_msg = f"Google Calendar API error: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "events": "[]",
                    "events_count": 0,
                    "next_event": "{}"
                }
            except Exception as e:
                error_msg = f"Error querying Google Calendar: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "events": "[]",
                    "events_count": 0,
                    "next_event": "{}"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Google Calendar Events node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "events": "[]",
                "events_count": 0,
                "next_event": "{}"
            }


@register_node
class GoogleCalendarCreateEventNode(Node):
    """
    谷歌日历事件创建节点
    
    这个节点允许在谷歌日历中创建新的事件。可以设置事件的标题、描述、位置、
    开始和结束时间，以及添加与会者。节点需要使用OAuth 2.0进行认证，
    因此需要提供凭据文件路径和令牌文件路径。
    
    使用场景:
    - 自动化会议安排
    - 计划提醒和待办事项创建
    - 工作流程中的日程管理
    - 系统生成的事件添加
    
    特点:
    - 支持创建完整的日历事件
    - 可以添加多个与会者
    - 设置事件的详细信息，如标题、描述和位置
    - 使用OAuth 2.0安全认证
    
    注意:
    - 需要有效的谷歌API凭据
    - 首次运行时需要用户授权
    - 遵循谷歌API使用限制和条款
    """
    NAME = "谷歌日历事件创建"
    DESCRIPTION = "在谷歌日历中创建新事件"
    CATEGORY = "Calendar"
    ICON = "calendar-plus"

    INPUTS = {
        "credentials_path": {
            "label": "凭据文件路径",
            "description": "谷歌API凭据文件(credentials.json)的路径",
            "type": "STRING",
            "required": True,
        },
        "token_path": {
            "label": "令牌文件路径",
            "description": "存储认证令牌的文件(token.json)路径",
            "type": "STRING",
            "required": True,
        },
        "title": {
            "label": "事件标题",
            "description": "事件的标题或摘要",
            "type": "STRING",
            "required": True,
        },
        "start_datetime": {
            "label": "开始时间",
            "description": "事件开始的日期和时间（ISO格式：YYYY-MM-DDTHH:MM:SS）",
            "type": "STRING",
            "required": True,
        },
        "end_datetime": {
            "label": "结束时间",
            "description": "事件结束的日期和时间（ISO格式：YYYY-MM-DDTHH:MM:SS）",
            "type": "STRING",
            "required": True,
        },
        "description": {
            "label": "事件描述",
            "description": "事件的详细描述",
            "type": "STRING",
            "required": False,
        },
        "location": {
            "label": "位置",
            "description": "事件的位置",
            "type": "STRING",
            "required": False,
        },
        "timezone": {
            "label": "时区",
            "description": "事件的时区",
            "type": "STRING",
            "default": "UTC",
            "required": False,
        },
        "attendees": {
            "label": "与会者",
            "description": "与会者的电子邮件地址，逗号分隔",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "event_id": {
            "label": "事件ID",
            "description": "创建的事件ID",
            "type": "STRING",
        },
        "event_link": {
            "label": "事件链接",
            "description": "创建的事件的HTML链接",
            "type": "STRING",
        },
        "event_details": {
            "label": "事件详情",
            "description": "创建的事件的完整详情（JSON格式）",
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
            credentials_path = node_inputs.get("credentials_path", "").strip()
            token_path = node_inputs.get("token_path", "").strip()
            title = node_inputs.get("title", "").strip()
            start_datetime = node_inputs.get("start_datetime", "").strip()
            end_datetime = node_inputs.get("end_datetime", "").strip()
            description = node_inputs.get("description", "").strip()
            location = node_inputs.get("location", "").strip()
            timezone = node_inputs.get("timezone", "UTC").strip()
            attendees_str = node_inputs.get("attendees", "").strip()
            
            # 验证必填参数
            if not credentials_path:
                logger.error("No credentials path provided")
                return {
                    "success": False,
                    "error_message": "No credentials path provided",
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            if not token_path:
                logger.error("No token path provided")
                return {
                    "success": False,
                    "error_message": "No token path provided",
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            if not title:
                logger.error("No event title provided")
                return {
                    "success": False,
                    "error_message": "No event title provided",
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            if not start_datetime:
                logger.error("No start datetime provided")
                return {
                    "success": False,
                    "error_message": "No start datetime provided",
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            if not end_datetime:
                logger.error("No end datetime provided")
                return {
                    "success": False,
                    "error_message": "No end datetime provided",
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            # 检查文件是否存在
            if not os.path.exists(credentials_path):
                error_msg = f"Credentials file does not exist: {credentials_path}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            # 检查是否安装所需的包
            try:
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from google_auth_oauthlib.flow import InstalledAppFlow
                from googleapiclient.discovery import build
                from googleapiclient.errors import HttpError
            except ImportError:
                error_msg = "Required packages not installed. Please install using `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            # 处理日期时间
            try:
                # 格式化日期时间
                start_time = datetime.datetime.fromisoformat(start_datetime).strftime("%Y-%m-%dT%H:%M:%S")
                end_time = datetime.datetime.fromisoformat(end_datetime).strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                error_msg = f"Invalid datetime format. Please use YYYY-MM-DDTHH:MM:SS format."
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
            # 处理与会者
            attendees_list = []
            if attendees_str:
                attendees_emails = [email.strip() for email in attendees_str.split(",") if email.strip()]
                attendees_list = [{"email": email} for email in attendees_emails]
            
            logger.info(f"Creating Google Calendar event: {title}")
            start_time_exec = time.time()
            
            # 认证和创建事件
            try:
                # 初始化凭据
                creds = None
                if os.path.exists(token_path):
                    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                    
                # 如果没有有效的凭据，或者凭据已过期
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    # 保存凭据供下次使用
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())
                
                # 构建服务
                service = build("calendar", "v3", credentials=creds)
                
                # 创建事件
                event = {
                    "summary": title,
                    "location": location,
                    "description": description,
                    "start": {
                        "dateTime": start_time,
                        "timeZone": timezone
                    },
                    "end": {
                        "dateTime": end_time,
                        "timeZone": timezone
                    },
                    "attendees": attendees_list,
                }
                
                event_result = service.events().insert(calendarId="primary", body=event).execute()
                
                # 提取信息
                event_id = event_result.get("id", "")
                event_link = event_result.get("htmlLink", "")
                event_details_json = json.dumps(event_result, ensure_ascii=False)
                
                elapsed = time.time() - start_time_exec
                logger.info(f"Event created in {elapsed:.2f}s, ID: {event_id}")
                
                return {
                    "success": True,
                    "event_id": event_id,
                    "event_link": event_link,
                    "event_details": event_details_json,
                    "error_message": ""
                }
                
            except HttpError as e:
                error_msg = f"Google Calendar API error: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
            except Exception as e:
                error_msg = f"Error creating Google Calendar event: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "event_id": "",
                    "event_link": "",
                    "event_details": "{}"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Google Calendar Create Event node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "event_id": "",
                "event_link": "",
                "event_details": "{}"
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
    events_node = GoogleCalendarEventsNode()
    create_event_node = GoogleCalendarCreateEventNode()
    
    # 测试凭据路径和令牌路径
    credentials_path = "credentials.json"
    token_path = "token.json"
    
    # 测试获取事件节点
    print("\n测试谷歌日历事件查询节点:")
    print("注意：这需要有效的凭据文件和已授权的令牌文件")
    # 取消注释以下代码进行实际测试
    # result = asyncio.run(events_node.execute({
    #     "credentials_path": credentials_path,
    #     "token_path": token_path,
    #     "limit": 5,
    #     "start_date": datetime.date.today().isoformat()
    # }, logger))
    # 
    # print(f"成功: {result['success']}")
    # if result['success']:
    #     print(f"事件数量: {result['events_count']}")
    #     if result['events_count'] > 0:
    #         next_event = json.loads(result['next_event'])
    #         print(f"下一个事件: {next_event.get('summary')} - {next_event.get('start', {}).get('dateTime')}")
    # else:
    #     print(f"错误: {result['error_message']}")
    
    # 测试创建事件节点
    print("\n测试谷歌日历事件创建节点:")
    print("注意：这需要有效的凭据文件和已授权的令牌文件")
    # 取消注释以下代码进行实际测试
    # now = datetime.datetime.now()
    # tomorrow = now + datetime.timedelta(days=1)
    # start_time = now.replace(microsecond=0).isoformat()
    # end_time = tomorrow.replace(microsecond=0).isoformat()
    # 
    # result = asyncio.run(create_event_node.execute({
    #     "credentials_path": credentials_path,
    #     "token_path": token_path,
    #     "title": "测试事件",
    #     "description": "这是一个通过工作流节点创建的测试事件",
    #     "location": "线上",
    #     "start_datetime": start_time,
    #     "end_datetime": end_time,
    #     "timezone": "Asia/Shanghai",
    #     "attendees": "test@example.com"
    # }, logger))
    # 
    # print(f"成功: {result['success']}")
    # if result['success']:
    #     print(f"事件ID: {result['event_id']}")
    #     print(f"事件链接: {result['event_link']}")
    # else:
    #     print(f"错误: {result['error_message']}") 