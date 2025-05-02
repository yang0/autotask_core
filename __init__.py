import time
print(f"[CoreInit] Start __init__.py at {time.time()}")
print(f"[CoreInit] Before import basic at {time.time()}")
from .nodes.basic import *
print(f"[CoreInit] After import basic at {time.time()}")
print(f"[CoreInit] Before import iteratorNode at {time.time()}")
from .nodes.iteratorNode import *
print(f"[CoreInit] After import iteratorNode at {time.time()}")
print(f"[CoreInit] Before import assistant at {time.time()}")
from .nodes.assistant import *
print(f"[CoreInit] After import assistant at {time.time()}")
print(f"[CoreInit] Before import time at {time.time()}")
from .nodes.time import *
print(f"[CoreInit] After import time at {time.time()}")
print(f"[CoreInit] Before import embedder at {time.time()}")
from .embedder import *
print(f"[CoreInit] After import embedder at {time.time()}")
print(f"[CoreInit] Before import text_reader at {time.time()}")
from .reader.text_reader import *
print(f"[CoreInit] After import text_reader at {time.time()}")
print(f"[CoreInit] Before import pdf_reader at {time.time()}")
from .reader.pdf_reader import *
print(f"[CoreInit] After import pdf_reader at {time.time()}")
print(f"[CoreInit] Before import word_reader at {time.time()}")
from .reader.word_reader import *
print(f"[CoreInit] After import word_reader at {time.time()}")
print(f"[CoreInit] Before import default_assistant at {time.time()}")
from .assistants.default_assistant import *
print(f"[CoreInit] After import default_assistant at {time.time()}")



VERSION = "1.0.3"
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
