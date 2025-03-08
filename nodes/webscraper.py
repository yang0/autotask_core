import json
import time
import traceback
from typing import Dict, Any, List, Optional
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from autotask.nodes import Node, register_node
from autotask.utils.log import logger as default_logger


@register_node
class WebScraperNode(Node):
    """
    网页内容抓取节点
    
    这个节点允许从指定URL抓取网页内容。可以提取页面上的元素，如文本、链接、图像等，
    并支持使用CSS选择器或XPath精确定位元素。该节点可用于数据收集、内容聚合、
    网页监控或任何需要从网站获取信息的工作流。
    
    使用场景:
    - 从网站收集数据和信息
    - 监控网页内容变化
    - 提取特定的网页元素（如标题、文章、价格等）
    - 创建网页内容摘要
    
    特点:
    - 支持CSS选择器和XPath表达式进行精确抓取
    - 能够提取文本、链接、图像和其他HTML元素
    - 可配置请求头和用户代理
    - 支持基本的HTTP身份验证
    
    注意:
    - 请遵守网站的robots.txt规则和服务条款
    - 避免频繁请求以免被网站封锁
    - 某些网站可能会阻止爬虫访问
    """
    NAME = "网页抓取"
    DESCRIPTION = "从网页抓取内容和元素"
    CATEGORY = "Web"
    ICON = "spider"

    INPUTS = {
        "url": {
            "label": "URL",
            "description": "要抓取的网页URL",
            "type": "STRING",
            "required": True,
        },
        "selector": {
            "label": "选择器",
            "description": "CSS选择器或XPath表达式（留空则返回整个HTML）",
            "type": "STRING",
            "required": False,
        },
        "selector_type": {
            "label": "选择器类型",
            "description": "选择器的类型",
            "type": "STRING",
            "default": "css",
            "required": False,
        },
        "extract_type": {
            "label": "提取类型",
            "description": "需要提取的内容类型",
            "type": "STRING",
            "default": "text",
            "required": False,
        },
        "attribute": {
            "label": "属性",
            "description": "要提取的HTML属性（当extract_type为'attribute'时使用）",
            "type": "STRING",
            "required": False,
        },
        "user_agent": {
            "label": "User Agent",
            "description": "请求时使用的User Agent",
            "type": "STRING",
            "default": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "required": False,
        },
        "timeout": {
            "label": "超时",
            "description": "请求超时时间（秒）",
            "type": "INT",
            "default": 30,
            "required": False,
        },
        "username": {
            "label": "用户名",
            "description": "HTTP基本认证的用户名",
            "type": "STRING",
            "required": False,
        },
        "password": {
            "label": "密码",
            "description": "HTTP基本认证的密码",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "content": {
            "label": "内容",
            "description": "抓取的内容",
            "type": "STRING",
        },
        "content_list": {
            "label": "内容列表",
            "description": "找到多个元素时的内容列表",
            "type": "STRING",
        },
        "elements_count": {
            "label": "元素数量",
            "description": "找到的元素数量",
            "type": "INT",
        },
        "page_title": {
            "label": "页面标题",
            "description": "网页的标题",
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
            url = node_inputs.get("url", "").strip()
            selector = node_inputs.get("selector", "").strip()
            selector_type = node_inputs.get("selector_type", "css").lower()
            extract_type = node_inputs.get("extract_type", "text").lower()
            attribute = node_inputs.get("attribute", "")
            user_agent = node_inputs.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            timeout = node_inputs.get("timeout", 30)
            username = node_inputs.get("username", "")
            password = node_inputs.get("password", "")
            
            # 验证URL
            if not url:
                logger.error("No URL provided")
                return {
                    "success": False,
                    "error_message": "No URL provided",
                    "content": "",
                    "content_list": "[]",
                    "elements_count": 0,
                    "page_title": ""
                }
                
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"Added https:// prefix to URL: {url}")
                
            # 验证选择器类型
            if selector_type not in ["css", "xpath"]:
                logger.warning(f"Invalid selector_type '{selector_type}', defaulting to 'css'")
                selector_type = "css"
                
            # 验证提取类型
            valid_extract_types = ["text", "html", "attribute", "href", "src"]
            if extract_type not in valid_extract_types:
                logger.warning(f"Invalid extract_type '{extract_type}', defaulting to 'text'")
                extract_type = "text"
                
            # 如果提取类型是attribute但没有指定属性
            if extract_type == "attribute" and not attribute:
                logger.warning("extract_type is 'attribute' but no attribute specified, defaulting to 'text'")
                extract_type = "text"
                
            # 准备请求头
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            # 准备认证
            auth = None
            if username and password:
                auth = (username, password)
                
            # 发送请求
            logger.info(f"Fetching content from URL: {url}")
            start_time = time.time()
            
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    auth=auth
                )
                response.raise_for_status()  # 如果响应状态码不是200，引发异常
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.title.text.strip() if soup.title else ""
                
                # 提取内容
                contents = []
                
                if not selector:
                    # 如果没有指定选择器，返回整个HTML
                    contents = [str(soup)]
                else:
                    # 根据选择器类型选择元素
                    elements = []
                    if selector_type == "css":
                        elements = soup.select(selector)
                    elif selector_type == "xpath":
                        from lxml import etree
                        html = etree.HTML(str(soup))
                        xpath_results = html.xpath(selector)
                        
                        for result in xpath_results:
                            if isinstance(result, str):
                                elements.append(result)
                            else:
                                # 转换lxml元素为BeautifulSoup元素
                                element_html = etree.tostring(result, encoding='unicode')
                                elements.append(BeautifulSoup(element_html, 'html.parser'))
                    
                    # 根据提取类型提取内容
                    for element in elements:
                        if extract_type == "text":
                            if isinstance(element, str):
                                contents.append(element)
                            else:
                                contents.append(element.get_text(strip=True))
                        elif extract_type == "html":
                            if isinstance(element, str):
                                contents.append(element)
                            else:
                                contents.append(str(element))
                        elif extract_type == "attribute":
                            if not isinstance(element, str) and hasattr(element, 'get'):
                                attr_value = element.get(attribute)
                                if attr_value:
                                    contents.append(attr_value)
                        elif extract_type == "href":
                            if not isinstance(element, str) and hasattr(element, 'get'):
                                href = element.get('href')
                                if href:
                                    # 处理相对URL
                                    absolute_url = urljoin(url, href)
                                    contents.append(absolute_url)
                        elif extract_type == "src":
                            if not isinstance(element, str) and hasattr(element, 'get'):
                                src = element.get('src')
                                if src:
                                    # 处理相对URL
                                    absolute_url = urljoin(url, src)
                                    contents.append(absolute_url)
                
                elapsed = time.time() - start_time
                logger.info(f"Scraped {len(contents)} elements in {elapsed:.2f}s")
                
                # 准备输出
                content = contents[0] if contents else ""
                content_list = json.dumps(contents, ensure_ascii=False)
                
                return {
                    "success": True,
                    "content": content,
                    "content_list": content_list,
                    "elements_count": len(contents),
                    "page_title": page_title,
                    "error_message": ""
                }
                
            except requests.RequestException as e:
                error_msg = f"Error fetching URL: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg,
                    "content": "",
                    "content_list": "[]",
                    "elements_count": 0,
                    "page_title": ""
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Web Scraper node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "content": "",
                "content_list": "[]",
                "elements_count": 0,
                "page_title": ""
            }


@register_node
class WebsiteScreenshotNode(Node):
    """
    网站截图节点
    
    这个节点可以获取指定网页的截图，并将其保存为图像文件。它使用无头浏览器渲染网页，
    因此可以正确捕获包含JavaScript动态内容的现代网站。支持调整截图尺寸、等待页面加载
    完成以及各种其他选项，以确保获得高质量的网页截图。
    
    使用场景:
    - 网站监控和测试
    - 创建网页报告和文档
    - 存档网页外观
    - 可视化测试和比较
    
    特点:
    - 支持完整页面或指定尺寸的截图
    - 可以等待页面加载或特定元素出现
    - 支持设置浏览器视口尺寸
    - 可以处理需要登录或交互的网站
    
    注意:
    - 需要安装Selenium和适当的WebDriver
    - 处理大型页面或多个截图时可能较慢
    - 某些网站可能会阻止自动化浏览器访问
    """
    NAME = "网站截图"
    DESCRIPTION = "获取网页的屏幕截图"
    CATEGORY = "Web"
    ICON = "camera"

    INPUTS = {
        "url": {
            "label": "URL",
            "description": "要截图的网页URL",
            "type": "STRING",
            "required": True,
        },
        "output_path": {
            "label": "输出路径",
            "description": "保存截图的文件路径（包括扩展名，如.png）",
            "type": "STRING",
            "required": True,
        },
        "width": {
            "label": "宽度",
            "description": "浏览器窗口宽度（像素）",
            "type": "INT",
            "default": 1280,
            "required": False,
        },
        "height": {
            "label": "高度",
            "description": "浏览器窗口高度（像素）",
            "type": "INT",
            "default": 800,
            "required": False,
        },
        "full_page": {
            "label": "整页截图",
            "description": "是否截取整个页面（而非仅可见区域）",
            "type": "BOOL",
            "default": True,
            "required": False,
        },
        "wait_time": {
            "label": "等待时间",
            "description": "截图前等待页面加载的时间（秒）",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "wait_for_selector": {
            "label": "等待选择器",
            "description": "截图前等待此CSS选择器的元素出现",
            "type": "STRING",
            "required": False,
        },
        "hide_elements": {
            "label": "隐藏元素",
            "description": "截图前隐藏的元素CSS选择器，用逗号分隔",
            "type": "STRING",
            "required": False,
        }
    }

    OUTPUTS = {
        "screenshot_path": {
            "label": "截图路径",
            "description": "保存的截图文件路径",
            "type": "STRING",
        },
        "width": {
            "label": "截图宽度",
            "description": "截图的宽度（像素）",
            "type": "INT",
        },
        "height": {
            "label": "截图高度",
            "description": "截图的高度（像素）",
            "type": "INT",
        },
        "success": {
            "label": "成功状态",
            "description": "截图是否成功",
            "type": "BOOL",
        },
        "error_message": {
            "label": "错误信息",
            "description": "如果截图失败，返回错误信息",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger=None) -> Dict[str, Any]:
        # 使用传入的logger或默认logger
        logger = workflow_logger if workflow_logger is not None else default_logger
        
        try:
            # 获取输入参数
            url = node_inputs.get("url", "").strip()
            output_path = node_inputs.get("output_path", "").strip()
            width = node_inputs.get("width", 1280)
            height = node_inputs.get("height", 800)
            full_page = node_inputs.get("full_page", True)
            wait_time = node_inputs.get("wait_time", 5)
            wait_for_selector = node_inputs.get("wait_for_selector", "").strip()
            hide_elements_str = node_inputs.get("hide_elements", "").strip()
            
            # 验证必填参数
            if not url:
                logger.error("No URL provided")
                return {
                    "success": False,
                    "error_message": "No URL provided",
                    "screenshot_path": "",
                    "width": 0,
                    "height": 0
                }
                
            if not output_path:
                logger.error("No output path provided")
                return {
                    "success": False,
                    "error_message": "No output path provided",
                    "screenshot_path": "",
                    "width": 0,
                    "height": 0
                }
                
            # 确保URL格式正确
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"Added https:// prefix to URL: {url}")
                
            # 准备隐藏元素列表
            hide_elements = [sel.strip() for sel in hide_elements_str.split(",") if sel.strip()]
                
            logger.info(f"Taking screenshot of URL: {url}")
            logger.info(f"Output path: {output_path}")
            start_time = time.time()
            
            try:
                # 检查是否已安装Selenium和WebDriver
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.chrome.service import Service
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from webdriver_manager.chrome import ChromeDriverManager
                except ImportError:
                    logger.error("Missing required packages. Please install selenium and webdriver-manager.")
                    return {
                        "success": False,
                        "error_message": "Missing required packages. Please install selenium and webdriver-manager.",
                        "screenshot_path": "",
                        "width": 0,
                        "height": 0
                    }
                
                # 设置Chrome选项
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument(f"--window-size={width},{height}")
                
                # 初始化WebDriver
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                
                try:
                    # 设置窗口大小
                    driver.set_window_size(width, height)
                    
                    # 访问URL
                    driver.get(url)
                    
                    # 等待页面加载
                    if wait_time > 0:
                        logger.info(f"Waiting {wait_time} seconds for page to load")
                        time.sleep(wait_time)
                        
                    # 等待特定元素（如果指定）
                    if wait_for_selector:
                        logger.info(f"Waiting for selector: {wait_for_selector}")
                        wait = WebDriverWait(driver, 10)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector)))
                        
                    # 隐藏指定元素
                    for selector in hide_elements:
                        try:
                            script = f"""
                                var elements = document.querySelectorAll('{selector}');
                                for (var i = 0; i < elements.length; i++) {{
                                    elements[i].style.visibility = 'hidden';
                                }}
                            """
                            driver.execute_script(script)
                            logger.info(f"Hidden elements matching: {selector}")
                        except Exception as e:
                            logger.warning(f"Failed to hide elements {selector}: {str(e)}")
                    
                    # 获取完整页面的高度（如果需要）
                    if full_page:
                        total_width = driver.execute_script("return document.body.scrollWidth")
                        total_height = driver.execute_script("return document.body.scrollHeight")
                        driver.set_window_size(total_width, total_height)
                        logger.info(f"Full page dimensions: {total_width}x{total_height}")
                    
                    # 截图
                    driver.save_screenshot(output_path)
                    
                    # 获取最终截图的尺寸
                    final_width = driver.execute_script("return document.documentElement.clientWidth")
                    final_height = driver.execute_script("return document.documentElement.clientHeight")
                    
                    elapsed = time.time() - start_time
                    logger.info(f"Screenshot taken in {elapsed:.2f}s and saved to {output_path}")
                    
                    return {
                        "success": True,
                        "screenshot_path": output_path,
                        "width": final_width,
                        "height": final_height,
                        "error_message": ""
                    }
                    
                finally:
                    # 确保关闭浏览器
                    driver.quit()
                
            except Exception as e:
                error_msg = f"Error taking screenshot: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error_message": error_msg,
                    "screenshot_path": "",
                    "width": 0,
                    "height": 0
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in Website Screenshot node: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": error_msg,
                "screenshot_path": "",
                "width": 0,
                "height": 0
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
    
    # Test WebScraperNode
    print("\nTesting WebScraperNode:")
    scraper_node = WebScraperNode()
    
    # This will make an actual web request, so we'll test with a simple example
    result = asyncio.run(scraper_node.execute({
        "url": "https://example.com",
        "selector": "h1",
        "selector_type": "css",
        "extract_type": "text"
    }, logger))
    
    print(f"Success: {result['success']}")
    print(f"Content: {result['content']}")
    print(f"Elements count: {result['elements_count']}")
    print(f"Page title: {result['page_title']}")
    
    # Test WebsiteScreenshotNode (commented out as it requires additional dependencies)
    print("\nWebsiteScreenshotNode would require Selenium and Chrome WebDriver")
    # Uncomment to test with actual screenshot
    # screenshot_node = WebsiteScreenshotNode()
    # result = asyncio.run(screenshot_node.execute({
    #     "url": "https://example.com",
    #     "output_path": "example_screenshot.png",
    #     "full_page": True
    # }, logger)) 