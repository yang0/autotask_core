from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from langchain_core.language_models.chat_models import BaseChatModel

class Step(BaseModel):
    member_name: str = Field(..., description="Name of the team member assigned to this step")
    title: str
    description: str = Field(..., description="Specify exactly what data to collect")
    execution_res: Optional[str] = Field(default=None, description="The Step execution result")

class Plan(BaseModel):
    locale: str = Field(..., description="e.g. 'en-US' or 'zh-CN', based on the user's language")
    has_enough_context: bool
    thought: str
    title: str
    steps: List[Step] = Field(default_factory=list, description="Steps to get more context")

class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""
    locale: str = "en-US"
    observations: list[str] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None
    team_members: List[str] = Field(default_factory=list, description="List of team members")
