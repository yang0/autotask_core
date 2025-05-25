import logging
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from langgraph.graph import END
import json
from langchain_core.runnables import RunnableConfig

from .prompts.template import apply_prompt_template
from autotask.utils.json_utils import repair_json_output
from .types import State, Step, Plan

logger = logging.getLogger(__name__)

def coordinator_node(state: State) -> Command[Literal["planner", "background_investigator", "__end__"]]:
    """Coordinator node that communicate with customers."""
    logger.info("Coordinator talking.")
    messages = state.get("messages", [])
    if not messages:
        return Command(goto=END)
        
    # Get coordinator messages from prompt template
    messages = apply_prompt_template("coordinator", state)
    
    # Use main_llm for coordinator
    llm = state.get("main_llm")
    if not llm:
        logger.error("Main LLM not found")
        return Command(goto=END)
        
    try:
        response = llm.invoke(messages)
        goto = "planner"
        if state.get("enable_background_investigation"):
            goto = "background_investigator"
            
        return Command(
            update={
                "locale": state.get("locale", "en-US"),
                "messages": [AIMessage(content=response.content, name="coordinator")]
            },
            goto=goto,
        )
    except Exception as e:
        logger.error(f"Error in coordinator node: {str(e)}")
        return Command(goto=END)

def background_investigation_node(state: State) -> Command[Literal["planner"]]:
    """Background investigation node that performs initial research."""
    logger.info("Background investigation node is running.")
    query = state["messages"][-1].content
    # Here you would implement the actual search functionality
    # For now, we'll just pass through to planner
    return Command(goto="planner")

def planner_node(state: State, config: RunnableConfig) -> Command[Literal["human_feedback", "reporter"]]:
    """Planner node that generate the full plan."""
    logger.info("Planner generating full plan")
    plan_iterations = state.get("plan_iterations", 0)
    
    # if the plan iterations is greater than the max plan iterations, return the reporter node
    if plan_iterations >= config.get("max_plan_iterations", 3):
        return Command(goto="reporter")

    # Apply prompt template to get messages for LLM
    messages = apply_prompt_template("planner", state, config)

    # Add background investigation results if available
    if (
        plan_iterations == 0
        and state.get("enable_background_investigation")
        and state.get("background_investigation_results")
    ):
        messages += [
            {
                "role": "user",
                "content": (
                    "background investigation results of user query:\n"
                    + state["background_investigation_results"]
                    + "\n"
                ),
            }
        ]

    # Get LLM instance - prefer reasoning_llm, fallback to main_llm
    llm = state.get("reasoning_llm") or state.get("main_llm")
    if not llm:
        logger.error("No LLM found for planner")
        return Command(goto="__end__")

    # Add structured output to LLM
    llm = llm.with_structured_output(Plan)

    try:
        # Get plan from LLM
        response = llm.invoke(messages)
        full_response = response.model_dump_json(indent=4, exclude_none=True)
        
        # Parse the response
        curr_plan = json.loads(repair_json_output(full_response))
        
        if curr_plan.get("has_enough_context"):
            logger.info("Planner response has enough context.")
            new_plan = Plan.model_validate(curr_plan)
            return Command(
                update={
                    "messages": [AIMessage(content=full_response, name="planner")],
                    "current_plan": new_plan,
                },
                goto="reporter",
            )
        
        return Command(
            update={
                "messages": [AIMessage(content=full_response, name="planner")],
                "current_plan": full_response,
            },
            goto="human_feedback",
        )
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error in planner node: {str(e)}")
        if plan_iterations > 0:
            return Command(goto="reporter")
        else:
            return Command(goto="__end__")

def human_feedback_node(state: State) -> Command[Literal["planner", "research_team", "reporter", "__end__"]]:
    """Handle human feedback on the plan."""
    current_plan = state.get("current_plan")
    plan_iterations = state.get("plan_iterations", 0)
    
    # For now, we'll auto-accept the plan and proceed to research team
    return Command(
        update={"plan_iterations": plan_iterations + 1},
        goto="research_team",
    )

def research_team_node(state: State) -> Command[str]:
    """Research team node that collaborates on tasks."""
    logger.info("Research team is collaborating on tasks.")
    current_plan = state.get("current_plan")
    
    if not current_plan or not current_plan.steps:
        return Command(goto="planner")
        
    # Find first unexecuted step
    for step in current_plan.steps:
        if not step.execution_res:
            # Get the assigned team member
            assigned_to = step.assigned_to
            if assigned_to in state.get("team_members", {}):
                return Command(goto=assigned_to)
            return Command(goto="planner")
                
    return Command(goto="planner")

def researcher_node(state: State) -> Command[Literal["research_team"]]:
    """Researcher node that performs research tasks."""
    logger.info("Researcher node is researching.")
    current_plan = state.get("current_plan")
    
    # Here you would implement the actual research logic
    # For now, we'll just mark the step as complete
    for step in current_plan.steps:
        if not step.execution_res:
            step.execution_res = "Research completed"
            break
            
    return Command(
        update={"current_plan": current_plan},
        goto="research_team",
    )

def coder_node(state: State) -> Command[Literal["research_team"]]:
    """Coder node that performs processing tasks."""
    logger.info("Coder node is processing.")
    current_plan = state.get("current_plan")
    
    # Here you would implement the actual processing logic
    # For now, we'll just mark the step as complete
    for step in current_plan.steps:
        if not step.execution_res:
            step.execution_res = "Processing completed"
            break
            
    return Command(
        update={"current_plan": current_plan},
        goto="research_team",
    )

def reporter_node(state: State):
    """Reporter node that writes the final report."""
    logger.info("Reporter writing final report")
    current_plan = state.get("current_plan")
    
    # Here you would implement the actual report generation logic
    final_report = f"Research Report\n\nTitle: {current_plan.title}\n\nFindings: {current_plan.thought}"
    
    return {"final_report": final_report}
