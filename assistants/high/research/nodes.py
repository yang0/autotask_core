import logging
from typing import Literal, Callable, Dict
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from langgraph.graph import END
import json
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from typing import Annotated

from .prompts.template import apply_prompt_template
from autotask.utils.json_utils import repair_json_output
from autotask.utils.assistant_config_utils import get_dict_from_runnable_config
from .types import State, Step, Plan
import os

logger = logging.getLogger(__name__)

@tool
def handoff_to_planner(
    task_title: Annotated[str, "The title of the task to be handed off."],
    locale: Annotated[str, "The user's detected language locale (e.g., en-US, zh-CN)."],
):
    """Handoff to planner agent to do plan."""
    # This tool is not returning anything: we're just using it
    # as a way for LLM to signal that it needs to hand off to planner agent
    return

def create_coordinator_node(llm) -> Callable[[State], Command[Literal["planner", "background_investigator", "__end__"]]]:
    """Factory function that creates a coordinator node with injected LLM."""
    def coordinator_node(state: State, config: RunnableConfig) -> Command[Literal["planner", "background_investigator", "__end__"]]:
        """Coordinator node that communicate with customers."""
        logger.info("Coordinator talking.")
        messages = state.get("messages", [])
        if not messages:
            return Command(goto=END)
            
        # Get coordinator messages from prompt template
        messages = apply_prompt_template("coordinator", state, config.get("metadata", {}))
        
        try:
            # Bind the handoff_to_planner tool to the LLM
            response = llm.bind_tools([handoff_to_planner]).invoke(messages)
            goto = "__end__"
            locale = state.get("locale", "en-US")  # Default locale if not specified
            
            if len(response.tool_calls) > 0:
                goto = "planner"
                if state.get("enable_background_investigation"):
                    goto = "background_investigator"
                    
                try:
                    for tool_call in response.tool_calls:
                        if tool_call.get("name", "") != "handoff_to_planner":
                            continue
                        if tool_locale := tool_call.get("args", {}).get("locale"):
                            locale = tool_locale
                            break
                except Exception as e:
                    logger.error(f"Error processing tool calls: {e}")
            else:
                logger.warning("Coordinator response contains no tool calls. Terminating workflow execution.")
                logger.debug(f"Coordinator response: {response}")
                
            return Command(
                update={
                    "locale": locale
                },
                goto=goto,
            )
        except Exception as e:
            logger.error(f"Error in coordinator node: {str(e)}")
            return Command(goto=END)
    
    return coordinator_node

def create_planner_node(main_llm, reasoning_llm) -> Callable[[State, RunnableConfig], Command[Literal["human_feedback", "reporter"]]]:
    """Factory function that creates a planner node with injected LLMs."""
    def planner_node(state: State, config: RunnableConfig) -> Command[Literal["human_feedback", "reporter"]]:
        """Planner node that generate the full plan."""
        logger.info("Planner generating full plan")
        plan_iterations = state.get("plan_iterations", 0)
        
        # if the plan iterations is greater than the max plan iterations, return the reporter node
        if plan_iterations >= config.get("max_plan_iterations", 1):
            return Command(goto="reporter")


        # Apply prompt template to get messages for LLM
        messages = apply_prompt_template("planner", state, config.get("metadata", {}))

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
        llm = reasoning_llm or main_llm
        if not llm:
            logger.error("No LLM found for planner")
            return Command(goto="__end__")

        # Add structured output to LLM
        llm = llm.with_structured_output(Plan, method="json_mode")

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
                    "current_plan": Plan.model_validate(curr_plan),
                    "plan_iterations": plan_iterations + 1
                },
                goto="research_team",
            )
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error in planner node: {str(e)}")
            if plan_iterations > 0:
                return Command(goto="reporter")
            else:
                return Command(goto="__end__")
    
    return planner_node

def background_investigation_node(state: State) -> Command[Literal["planner"]]:
    """Background investigation node that performs initial research."""
    logger.info("Background investigation node is running.")
    query = state["messages"][-1].content
    # Here you would implement the actual search functionality
    # For now, we'll just pass through to planner
    return Command(goto="planner")

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
            member_name = step.member_name
            if member_name in state.get("team_members", {}):
                return Command(goto=member_name)
            return Command(goto="planner")
                
    return Command(goto="planner")


async def _execute_agent_step(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """Helper function to execute a step using the specified agent."""
    current_plan = state.get("current_plan")
    observations = state.get("observations", [])

    # Find the first unexecuted step
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        if not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.warning("No unexecuted step found")
        return Command(goto="research_team")

    logger.info(f"Executing step: {current_step.title}")

    # Format completed steps information
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# Existing Research Findings\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## Existing Finding {i+1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # Prepare the input for the agent with completed steps info
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"{completed_steps_info}# Current Task\n\n## Title\n\n{current_step.title}\n\n## Description\n\n{current_step.description}\n\n## Locale\n\n{state.get('locale', 'en-US')}"
            )
        ]
    }

    # Add citation reminder for researcher agent
    if agent_name == "researcher":
        agent_input["messages"].append(
            HumanMessage(
                content="IMPORTANT: DO NOT include inline citations in the text. Instead, track all sources and include a References section at the end using link reference format. Include an empty line between each citation for better readability. Use this format for each reference:\n- [Source Title](URL)\n\n- [Another Source](URL)",
                name="system",
            )
        )

    # Invoke the agent
    default_recursion_limit = 25
    try:
        env_value_str = os.getenv("AGENT_RECURSION_LIMIT", str(default_recursion_limit))
        parsed_limit = int(env_value_str)

        if parsed_limit > 0:
            recursion_limit = parsed_limit
            logger.info(f"Recursion limit set to: {recursion_limit}")
        else:
            logger.warning(
                f"AGENT_RECURSION_LIMIT value '{env_value_str}' (parsed as {parsed_limit}) is not positive. "
                f"Using default value {default_recursion_limit}."
            )
            recursion_limit = default_recursion_limit
    except ValueError:
        raw_env_value = os.getenv("AGENT_RECURSION_LIMIT")
        logger.warning(
            f"Invalid AGENT_RECURSION_LIMIT value: '{raw_env_value}'. "
            f"Using default value {default_recursion_limit}."
        )
        recursion_limit = default_recursion_limit

    result = await agent.ainvoke(
        input=agent_input, config={"recursion_limit": recursion_limit}
    )

    # Process the result
    response_content = result["messages"][-1].content
    logger.debug(f"{agent_name.capitalize()} full response: {response_content}")

    # Update the step with the execution result
    current_step.execution_res = response_content
    logger.info(f"Step '{current_step.title}' execution completed by {agent_name}")

    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response_content,
                    name=agent_name,
                )
            ],
            "observations": observations + [response_content],
        },
        goto="research_team",
    )

def create_reporter_node(llm) -> Callable[[State], Dict[str, str]]:
    """Factory function that creates a reporter node with injected LLM."""
    def reporter_node(state: State):
        """Reporter node that writes the final report."""
        logger.info("Reporter writing final report")
        current_plan = state.get("current_plan")
        
        input_ = {
            "messages": [
                HumanMessage(
                    content=f"# Research Requirements\n\n## Task\n\n{current_plan.title}\n\n## Description\n\n{current_plan.thought}"
                )
            ],
            "locale": state.get("locale", "en-US"),
        }
        
        invoke_messages = apply_prompt_template("reporter", input_)
        observations = state.get("observations", [])
        
        # Add a reminder about the report format and citation style
        invoke_messages.append(
            HumanMessage(
                content="IMPORTANT: Structure your report according to the format in the prompt. Remember to include:\n\n"
                       "1. Key Points - A bulleted list of the most important findings\n"
                       "2. Overview - A brief introduction to the topic\n"
                       "3. Detailed Analysis - Organized into logical sections\n"
                       "4. Survey Note (optional) - For more comprehensive reports\n"
                       "5. Key Citations - List all references at the end\n\n"
                       "For citations, DO NOT include inline citations in the text. Instead, place all citations in the 'Key Citations' "
                       "section at the end using the format: `- [Source Title](URL)`. Include an empty line between each citation for "
                       "better readability.\n\n"
                       "PRIORITIZE USING MARKDOWN TABLES for data presentation and comparison. Use tables whenever presenting comparative "
                       "data, statistics, features, or options. Structure tables with clear headers and aligned columns. Example table format:\n\n"
                       "| Feature | Description | Pros | Cons |\n"
                       "|---------|-------------|------|------|\n"
                       "| Feature 1 | Description 1 | Pros 1 | Cons 1 |\n"
                       "| Feature 2 | Description 2 | Pros 2 | Cons 2 |",
                name="system",
            )
        )
        
        # Add observations
        for observation in observations:
            invoke_messages.append(
                HumanMessage(
                    content=f"Below are some observations for the research task:\n\n{observation}",
                    name="observation",
                )
            )
        
        logger.debug(f"Current invoke messages: {invoke_messages}")
        response = llm.invoke(invoke_messages)
        response_content = response.content
        logger.info(f"Reporter response: {response_content}")
        
        return {"final_report": response_content}
    
    return reporter_node
