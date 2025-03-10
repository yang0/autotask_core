from .nodes.agent import *
from .nodes.iteratorNode import *
from .agents.simpleAgent import *
from .embedder import *
from .reader.text_reader import *
# from .documentLoader.jsonlLoader import *
# from .documentLoader.largeTextLoader import *
# from .documentLoader.pdfLoader import *
# from .documentLoader.sqliteLoader import *

VERSION = "0.0.43"
GIT_URL = "https://github.com/yang0/autotask_core.git"
NAME = "AutoTask Core"
DESCRIPTION = """Core plugin for AutoTask that provides essential AI agent features including:

• Simple Text Agent - A basic LLM-powered agent for text processing and interaction
• Agent Node - A workflow node for integrating AI agents into your automation flows
• Support for multiple LLM models
• Function calling capabilities
• Configurable agent parameters

This plugin serves as a foundation for building AI-powered automation workflows."""

TAGS = ["agent", "core", "AI Assistant"]
