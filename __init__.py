from .nodes.basic import *
from .nodes.iteratorNode import *
from .nodes.assistant import *
from .nodes.time import *
from .embedder import *
from .reader.text_reader import *
from .reader.pdf_reader import *
from .reader.word_reader import *
from .assistants.default_assistant import *



VERSION = "1.0.1"
GIT_URL = "https://github.com/yang0/autotask_core.git"
NAME = "AutoTask Core"
DESCRIPTION = """Core plugin for AutoTask that provides essential components for building AI-powered automation systems:

• Workflow Nodes
  - Flow Control: Iterator and Boolean Condition nodes
  - Time Operations: Current Time and Time Difference nodes
  - File System: Read, Write, List, Delete, and Info nodes
  - AI Integration: Assistant node for LLM interaction

• Knowledge Base Components
  - Text Reader: Intelligent document processing with multi-format support
  - Embedding Models: Vector embedding for knowledge base construction
  - Advanced Text Chunking: Smart document splitting for optimal processing

• AI Assistant Framework
  - Base Assistant Classes: Foundation for building custom AI assistants
  - LLM Integration: Support for multiple language models
  - Function Calling: Extensible function execution framework

This plugin provides the core building blocks for creating sophisticated AI-powered automation systems."""

TAGS = ["core", "workflow", "embedding", "knowledge-base", "ai-assistant"]
