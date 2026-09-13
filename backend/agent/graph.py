import json
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agent.tools import ALL_TOOLS
from agent.prompts import SYSTEM_PROMPT
from config import GROQ_API_KEY, MODEL_NAME


class AgentState(TypedDict):
    """State managed by the LangGraph agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    complaint_data: dict
    tool_calls_log: list


def create_agent_graph():
    """Create and compile the LangGraph agent workflow.
    
    The graph follows a ReAct pattern:
    START → agent_node → should_continue? → tool_node → agent_node → ... → END
    
    The agent decides which tools to call based on user input, executes them,
    and returns structured complaint data along with a conversational response.
    """
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=MODEL_NAME,
        temperature=0.1,
        max_tokens=4096,
    )

    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState) -> dict:
        """The main agent node that processes messages and decides on tool calls."""
        messages = state["messages"]

        # Ensure system prompt is at the beginning
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

        # Add context about current complaint data if available
        complaint_data = state.get("complaint_data", {})
        if complaint_data:
            context_msg = f"\n\n[CURRENT COMPLAINT DATA]: {json.dumps(complaint_data)}"
            # Append context to the last human message
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                messages = list(messages[:-1]) + [
                    HumanMessage(content=last_msg.content + context_msg)
                ]

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Determine if the agent should continue to tool execution or end."""
        last_message = state["messages"][-1]
        tool_calls_log = state.get("tool_calls_log", [])
        if len(tool_calls_log) >= 3:
            return END
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    def process_tool_results(state: AgentState) -> dict:
        """After tool execution, extract complaint data from tool results."""
        messages = state["messages"]
        complaint_data = state.get("complaint_data", {})
        tool_calls_log = state.get("tool_calls_log", [])

        # Look at the most recent tool message results
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "tool":
                try:
                    result = json.loads(msg.content)
                    # If it has complaint-like fields, merge into complaint_data
                    complaint_fields = [
                        "productName", "productStrength", "batchNumber",
                        "complaintDescription", "severityLevel", "riskScore",
                        "complainantPhone", "complainantEmail", "countryCode",
                    ]
                    if any(field in result for field in complaint_fields):
                        complaint_data.update(result)
                    
                    # Handle completeness check results
                    if "completenessScore" in result:
                        complaint_data["completenessScore"] = result["completenessScore"]
                    
                    tool_calls_log.append({
                        "tool": msg.name if hasattr(msg, "name") else "unknown",
                        "result": result,
                    })
                except (json.JSONDecodeError, TypeError):
                    pass
                break

        return {
            "complaint_data": complaint_data,
            "tool_calls_log": tool_calls_log,
        }

    # Build the graph
    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("process_results", process_tool_results)

    # Set entry point
    graph.set_entry_point("agent")

    # Add edges
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "process_results")
    graph.add_edge("process_results", "agent")

    return graph.compile()


# Create a singleton compiled graph
agent_graph = create_agent_graph()


async def run_agent(
    user_message: str,
    complaint_data: dict | None = None,
    chat_history: list | None = None,
) -> dict:
    """Run the LangGraph agent with a user message and return results.
    
    Args:
        user_message: The user's natural language input
        complaint_data: Current complaint data (for edit operations)
        chat_history: Previous chat messages for context
    
    Returns:
        Dictionary with 'response' (AI text), 'complaint_data' (updated fields),
        and 'tool_calls' (list of tools invoked).
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add chat history
    if chat_history:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    # Add the current user message
    messages.append(HumanMessage(content=user_message))

    initial_state: AgentState = {
        "messages": messages,
        "complaint_data": complaint_data or {},
        "tool_calls_log": [],
    }

    # Run the graph
    result = agent_graph.invoke(initial_state)

    # Extract the final AI response
    ai_response = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            ai_response = msg.content
            break

    return {
        "response": ai_response,
        "complaint_data": result.get("complaint_data", {}),
        "tool_calls": result.get("tool_calls_log", []),
    }
