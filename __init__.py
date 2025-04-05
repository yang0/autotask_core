from .nodes.basic import *
from .nodes.iteratorNode import *
from .nodes.assistant import *
from .nodes.time import *
from .embedder import *
from .reader.text_reader import *
from .assistants.default_assistant import *



VERSION = "0.0.44"
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
