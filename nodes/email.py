import json
import time
import traceback
import re
from typing import Dict, Any, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger


@register_node
class EmailSendNode(Node):
    """
    发送电子邮件节点
    
    这个节点允许从工作流程中发送电子邮件。支持纯文本和HTML格式内容，可以添加附件，
    并且支持多个收件人。可用于通知、报告分发或在工作流中触发外部操作。
    
    使用场景:
    - 发送工作流执行结果通知
    - 分发报告和数据文件
    - 在关键事件发生时触发警报
    - 向用户发送自动响应
    
    特点:
    - 支持纯文本和HTML格式内容
    - 可以添加文件附件
    - 支持多个收件人（收件人、抄送、密送）
    - 可自定义发件人名称
    
    注意:
    - 需要有效的SMTP服务器配置
    - 某些邮件服务可能需要应用专用密码
    - 附件大小可能受到邮件服务器限制
    """
    NAME = "邮件发送"
    DESCRIPTION = "发送电子邮件到指定收件人"
    CATEGORY = "Communication"
    ICON = "envelope"

    INPUTS = {
        "to": {
            "label": "收件人",
            "description": "邮件接收者，多个地址用逗号分隔",
            "type": "STRING",
            "required": True,
        },
        "subject": {
            "label": "主题",
            "description": "邮件主题",
            "type": "STRING",
            "required": True,
        },
        "body": {
            "label": "内容",
            "description": "邮件内容(支持纯文本或HTML)",
            "type": "STRING",
            "required": True,
        },
        "is_html": {
            "label": "HTML格式",
            "description": "内容是否为HTML格式",
            "type": "BOOL",
            "default": False,
            "required": False,
        },
        "cc": {
            "label": "抄送",
            "description": "抄送收件人，多个地址用逗号分隔",
            "type": "STRING",
            "required": False,
        },
        "bcc": {
            "label": "密送",
            "description": "密送收件人，多个地址用逗号分隔",
            "type": "STRING",
            "required": False,
        },
        "from_name": {
            "label": "发件人名称",
            "description": "显示的发件人名称",
            "type": "STRING",
            "required": False,
        },
        "attachment_paths": {
            "label": "附件路径",
            "description": "要附加的文件路径，多个文件用逗号分隔",
            "type": "STRING",
            "required": False,
        },
        "smtp_server": {
            "label": "SMTP服务器",
            "description": "SMTP服务器地址",
            "type": "STRING",
            "required": True,
        },
        "smtp_port": {
            "label": "SMTP端口",
            "description": "SMTP服务器端口",
            "type": "INT",
            "default": 587,
            "required": False,
        },
        "smtp_username": {
            "label": "SMTP用户名",
            "description": "SMTP服务器用户名",
            "type": "STRING",
            "required": True,
        },
        "smtp_password": {
            "label": "SMTP密码",
            "description": "SMTP服务器密码",
            "type": "STRING",
            "required": True,
        },
        "use_ssl": {
            "label": "使用SSL",
            "description": "是否使用SSL连接SMTP服务器",
            "type": "BOOL",
            "default": False,
            "required": False,
        }
    }

    OUTPUTS = {
        "success": {
            "label": "成功状态",
            "description": "邮件是否成功发送",
            "type": "BOOL",
        },
        "message": {
            "label": "结果消息",
            "description": "操作结果的详细信息或错误消息",
            "type": "STRING",
        },
        "recipients_count": {
            "label": "收件人数量",
            "description": "邮件发送的收件人总数",
            "type": "INT",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取基本邮件参数
            to_str = node_inputs.get("to", "")
            subject = node_inputs.get("subject", "")
            body = node_inputs.get("body", "")
            is_html = node_inputs.get("is_html", False)
            cc_str = node_inputs.get("cc", "")
            bcc_str = node_inputs.get("bcc", "")
            from_name = node_inputs.get("from_name", "")
            attachment_paths_str = node_inputs.get("attachment_paths", "")
            
            # 获取SMTP参数
            smtp_server = node_inputs.get("smtp_server", "")
            smtp_port = node_inputs.get("smtp_port", 587)
            smtp_username = node_inputs.get("smtp_username", "")
            smtp_password = node_inputs.get("smtp_password", "")
            use_ssl = node_inputs.get("use_ssl", False)
            
            # 验证必填参数
            if not to_str:
                logger.error("No recipients specified")
                return {
                    "success": False,
                    "message": "No recipients specified",
                    "recipients_count": 0
                }
                
            if not subject:
                logger.warning("Email subject is empty")
                
            if not smtp_server or not smtp_username or not smtp_password:
                logger.error("Missing SMTP server configuration")
                return {
                    "success": False,
                    "message": "Missing SMTP server configuration",
                    "recipients_count": 0
                }
            
            # 解析收件人列表
            to_list = [email.strip() for email in to_str.split(",") if email.strip()]
            cc_list = [email.strip() for email in cc_str.split(",") if email.strip()]
            bcc_list = [email.strip() for email in bcc_str.split(",") if email.strip()]
            
            # 验证电子邮件地址格式
            all_recipients = to_list + cc_list + bcc_list
            invalid_emails = []
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for email in all_recipients:
                if not re.match(email_pattern, email):
                    invalid_emails.append(email)
            
            if invalid_emails:
                error_msg = f"Invalid email addresses: {', '.join(invalid_emails)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "recipients_count": 0
                }
                
            # 解析附件路径
            attachment_paths = [path.strip() for path in attachment_paths_str.split(",") if path.strip()]
            
            # 构建邮件
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{smtp_username}>" if from_name else smtp_username
            msg["To"] = ", ".join(to_list)
            
            if cc_list:
                msg["Cc"] = ", ".join(cc_list)
                
            # 添加正文
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
                
            # 添加附件
            for file_path in attachment_paths:
                try:
                    path = Path(file_path)
                    if not path.exists():
                        logger.warning(f"Attachment not found: {file_path}")
                        continue
                        
                    with open(path, "rb") as file:
                        part = MIMEApplication(file.read(), Name=path.name)
                        part["Content-Disposition"] = f'attachment; filename="{path.name}"'
                        msg.attach(part)
                        logger.info(f"Added attachment: {path.name}")
                except Exception as e:
                    logger.warning(f"Failed to attach file {file_path}: {str(e)}")
            
            # 发送邮件
            logger.info(f"Sending email to {len(all_recipients)} recipients: {', '.join(all_recipients)}")
            start_time = time.time()
            
            try:
                # 连接SMTP服务器
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                else:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()  # 为连接启用安全传输
                
                # 登录
                server.login(smtp_username, smtp_password)
                
                # 发送邮件
                server.send_message(msg)
                
                # 关闭连接
                server.quit()
                
                elapsed = time.time() - start_time
                logger.info(f"Email sent successfully in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "message": f"Email sent successfully to {len(all_recipients)} recipients",
                    "recipients_count": len(all_recipients)
                }
                
            except Exception as e:
                error_msg = f"Failed to send email: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "message": error_msg,
                    "recipients_count": 0
                }
            
        except Exception as e:
            error_msg = f"Unexpected error in Email Send node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": error_msg,
                "recipients_count": 0
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
    
    # Test EmailSendNode
    print("\nTesting EmailSendNode (no actual email will be sent):")
    node = EmailSendNode()
    
    # Example test data - this would NOT be executed unless explicitly run with credentials
    test_inputs = {
        "to": "recipient@example.com",
        "subject": "Test Email from Workflow",
        "body": "<h1>Hello from Workflow</h1><p>This is a test email.</p>",
        "is_html": True,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user@example.com",
        "smtp_password": "password"
    }
    
    print("Would configure email with:")
    print(f"To: {test_inputs['to']}")
    print(f"Subject: {test_inputs['subject']}")
    print(f"HTML Content: {test_inputs['is_html']}")
    print(f"SMTP: {test_inputs['smtp_server']}:{test_inputs['smtp_port']}")
    
    # Uncomment to actually run the test with real credentials
    # result = asyncio.run(node.execute(test_inputs, logger))
    # print(f"Success: {result['success']}")
    # print(f"Message: {result['message']}")
    # print(f"Recipients: {result['recipients_count']}") 