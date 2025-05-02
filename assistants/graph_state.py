"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.messages import AnyMessage
from typing_extensions import Annotated
from autotask.assistant.graph_state import State as BaseState



@dataclass
class State(BaseState):
    def __post_init__(self):
        # lazy import langgraph only if needed
        pass
    # 需要用到add_messages或IsLastStep时再import
    @staticmethod
    def add_messages(*args, **kwargs):
        from langgraph.graph import add_messages
        return add_messages(*args, **kwargs)
    @staticmethod
    def is_last_step(*args, **kwargs):
        from langgraph.managed import IsLastStep
        return IsLastStep(*args, **kwargs)