import json
import re
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from groq import BadRequestError

from agent.tools import ALL_TOOLS
from agent.prompts import SYSTEM_PROMPT
from config import GROQ_API_KEY, MODEL_NAME
from services.llm_factory import get_groq_llm
from services.field_edits import (
    apply_field_edits,
    looks_like_field_edit,
    parse_field_edits,
)



REQUIRED_FIELDS = {
    "productName": "Product Name",
    "productStrength": "Product Strength",
    "dosageForm": "Dosage Form",
    "batchNumber": "Batch Number",
    "lotNumber": "Lot Number",
    "manufacturingDate": "Manufacturing Date",
    "expiryDate": "Expiry Date",
    "complaintCategory": "Complaint Category",
    "complaintDescription": "Complaint Description",
    "complainantName": "Complainant Name",
    "complainantEmail": "Complainant Email",
    "complainantPhone": "Complainant Phone",
    "countryCode": "Country Code",
    "dateOfComplaint": "Date of Complaint",
    "dateOfIncident": "Date of Incident",
}


def _is_filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return bool(str(value).strip())


def compute_completeness(complaint_data: dict) -> dict:
    filled = 0
    missing = []
    missing_keys = []
    for key, label in REQUIRED_FIELDS.items():
        if _is_filled(complaint_data.get(key)):
            filled += 1
        else:
            missing.append(label)
            missing_keys.append(key)
    score = round((filled / len(REQUIRED_FIELDS)) * 100, 1) if REQUIRED_FIELDS else 0
    return {
        "completenessScore": score,
        "missingFields": missing,
        "missingFieldKeys": missing_keys,
        "totalFields": len(REQUIRED_FIELDS),
        "filledFields": filled,
    }


def _filled_and_missing_summary(complaint_data: dict) -> str:
    filled_keys = [k for k in REQUIRED_FIELDS if _is_filled(complaint_data.get(k))]
    missing_keys = [k for k in REQUIRED_FIELDS if not _is_filled(complaint_data.get(k))]
    return (
        f"FILLED FIELDS (do NOT ask again): {', '.join(filled_keys) or 'none'}. "
        f"MISSING FIELDS (ask only these): {', '.join(missing_keys) or 'none'}."
    )


class AgentState(TypedDict):
    """State managed by the LangGraph agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    complaint_data: dict
    tool_calls_log: list


def _has_core_complaint_data(complaint_data: dict) -> bool:
    return any(
        _is_filled(complaint_data.get(k))
        for k in ("productName", "batchNumber", "complaintDescription")
    )


def _looks_like_complaint_narrative(text: str) -> bool:
    if not text or len(text.strip()) < 80:
        return False
    lowered = text.lower()
    signals = (
        "batch",
        "tablet",
        "capsule",
        "discolour",
        "discolor",
        "complaint",
        "expiry",
        "expire",
        "product",
        "pharmacy",
        "manufactur",
        "blister",
        "quality",
    )
    return sum(1 for s in signals if s in lowered) >= 2


def create_agent_graph():
    """Create and compile the LangGraph agent workflow."""
    llm_with_tools = get_groq_llm(
        temperature=0.1,
        max_tokens=4096,
        tools=ALL_TOOLS,
    )
    llm_force_log = get_groq_llm(
        temperature=0.1,
        max_tokens=4096,
        tools=ALL_TOOLS,
        tool_choice="log_complaint",
    )
    llm_force_edit = get_groq_llm(
        temperature=0.1,
        max_tokens=2048,
        tools=ALL_TOOLS,
        tool_choice="edit_complaint",
    )

    def agent_node(state: AgentState) -> dict:
        messages = list(state["messages"])

        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        complaint_data = state.get("complaint_data", {}) or {}
        tool_calls_log = state.get("tool_calls_log", []) or []

        # Find latest human text
        last_human = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human = msg.content or ""
                break
        # Strip injected context markers for intent detection
        last_human_raw = last_human.split("\n\n[CURRENT COMPLAINT DATA]")[0].strip()

        force_log = (
            not _has_core_complaint_data(complaint_data)
            and _looks_like_complaint_narrative(last_human_raw)
            and len(tool_calls_log) == 0
        )
        force_edit = (
            not force_log
            and _has_core_complaint_data(complaint_data)
            and looks_like_field_edit(last_human_raw)
            and len(tool_calls_log) == 0
        )

        if complaint_data or force_log or force_edit:
            field_guide = _filled_and_missing_summary(complaint_data)
            context_parts = [
                f"\n\n[CURRENT COMPLAINT DATA]: {json.dumps(complaint_data)}",
                f"\n[{field_guide}]",
            ]
            if force_log:
                context_parts.append(
                    "\n[MANDATORY ACTION]: The left form is empty and the user provided a "
                    "complaint narrative. You MUST call log_complaint NOW and extract ALL "
                    "available fields from the user text (product, strength, dosage form, "
                    "batch, dates, category, description, summary, risk). Do not ask "
                    "questions before logging. Infer countryCode=+91 when India/Maharashtra/Pune "
                    "is mentioned. Convert dates like '11 September 2026' to YYYY-MM-DD and "
                    "'July 2028' expiry to 2028-07-31. "
                    "For unknown string fields (lot_number, complainant_phone, etc.) omit them "
                    "or pass \"\" — NEVER pass null."
                )
            if force_edit:
                parsed = parse_field_edits(last_human_raw)
                context_parts.append(
                    "\n[MANDATORY ACTION]: User asked to edit existing complaint fields. "
                    "You MUST call edit_complaint NOW with ONLY the changed fields "
                    f"(parsed intent: {json.dumps(parsed)}). Do not call log_complaint."
                )
            context_msg = "".join(context_parts)
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                # Avoid stacking context on every agent loop
                base = last_msg.content.split("\n\n[CURRENT COMPLAINT DATA]")[0]
                messages = list(messages[:-1]) + [
                    HumanMessage(content=base + context_msg)
                ]

        if force_log:
            active_llm = llm_force_log
        elif force_edit:
            active_llm = llm_force_edit
        else:
            active_llm = llm_with_tools
        try:
            response = active_llm.invoke(messages)
        except BadRequestError as exc:
            # Groq rejects tool calls with null for string params; retry without forced choice
            # and with an explicit empty-string reminder.
            err = str(exc)
            if "tool_use_failed" not in err and "expected string" not in err:
                raise
            retry_hint = (
                "\n[RETRY]: Previous tool call failed because null was used for string fields. "
                "Call the tool again; omit unknown fields or use \"\" — never null."
            )
            retry_messages = list(messages)
            last_msg = retry_messages[-1]
            if isinstance(last_msg, HumanMessage):
                retry_messages[-1] = HumanMessage(content=last_msg.content + retry_hint)
            else:
                retry_messages.append(HumanMessage(content=retry_hint.strip()))
            response = llm_with_tools.invoke(retry_messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        tool_calls_log = state.get("tool_calls_log", []) or []
        has_pending_tools = bool(
            getattr(last_message, "tool_calls", None)
        )
        # Allow extract/log + assess + completeness (+ optional missing-info tool).
        # Never hard-stop while tools are still pending with an empty content turn —
        # that leaves the chat showing only wrench badges and no MissingInfoForm.
        if has_pending_tools and len(tool_calls_log) < 5:
            return "tools"
        return END

    def process_tool_results(state: AgentState) -> dict:
        messages = state["messages"]
        complaint_data = dict(state.get("complaint_data", {}) or {})
        tool_calls_log = list(state.get("tool_calls_log", []))

        # Only process tool messages that appeared after the latest AI tool-call turn
        recent_tool_msgs = []
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "tool":
                recent_tool_msgs.append(msg)
            elif isinstance(msg, AIMessage):
                break
        recent_tool_msgs.reverse()

        for msg in recent_tool_msgs:
            try:
                result = json.loads(msg.content)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(result, dict):
                continue

            if result.get("action") == "check_completeness":
                completeness = compute_completeness(complaint_data)
                complaint_data.update(completeness)
                tool_calls_log.append({
                    "tool": getattr(msg, "name", "check_completeness"),
                    "result": completeness,
                })
                continue

            for k, v in result.items():
                if k in {"missing_fields", "prompt", "openui_markup", "action"}:
                    continue
                # Never wipe existing values with empty assessment stubs
                if v is None or v == "":
                    continue
                if k == "recommendedActions" and isinstance(v, list) and len(v) == 0:
                    continue
                if k == "riskScore" and v == 0 and not result.get("severityLevel"):
                    continue
                if k == "severityLevel":
                    from services.complaint_sanitize import normalize_severity_level
                    v = normalize_severity_level(v, result.get("riskScore") or complaint_data.get("riskScore"))
                complaint_data[k] = v

            tool_calls_log.append({
                "tool": getattr(msg, "name", "unknown"),
                "result": result,
            })

        complaint_data.update(compute_completeness(complaint_data))

        return {
            "complaint_data": complaint_data,
            "tool_calls_log": tool_calls_log,
        }

    tool_node = ToolNode(ALL_TOOLS)
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("process_results", process_tool_results)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "process_results")
    graph.add_edge("process_results", "agent")
    return graph.compile()


agent_graph = create_agent_graph()


async def run_agent(
    user_message: str,
    complaint_data: dict | None = None,
    chat_history: list | None = None,
) -> dict:
    """Run the LangGraph agent with a user message and return results."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if chat_history:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_message))

    initial_state: AgentState = {
        "messages": messages,
        "complaint_data": complaint_data or {},
        "tool_calls_log": [],
    }

    result = agent_graph.invoke(initial_state)

    ai_response = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            ai_response = msg.content
            break

    complaint_out = result.get("complaint_data", {}) or {}
    # Deterministic NL edit merge — ensures left form updates even if the model
    # only wrote a confirmation card without a successful edit_complaint tool call.
    complaint_out = apply_field_edits(complaint_out, user_message)
    completeness = compute_completeness(complaint_out)
    complaint_out.update(completeness)
    ai_response = _normalize_missing_info_form(ai_response, completeness, complaint_out)

    # If user asked to edit and we applied it, make sure the reply reflects new values
    edits = parse_field_edits(user_message)
    if edits:
        for key, value in edits.items():
            # Keep OpenUI ComplaintCard batch/product in sync when present
            if key == "batchNumber":
                ai_response = re.sub(
                    r'(batch=")[^"]*(")',
                    rf'\g<1>{value}\2',
                    ai_response,
                    count=1,
                    flags=re.I,
                )
            if key == "productName":
                ai_response = re.sub(
                    r'(product=")[^"]*(")',
                    rf'\g<1>{value}\2',
                    ai_response,
                    count=1,
                    flags=re.I,
                )
        if not ai_response.strip():
            pairs = ", ".join(f"{k}={v}" for k, v in edits.items())
            ai_response = f"Updated the form: {pairs}."

    return {
        "response": ai_response,
        "complaint_data": complaint_out,
        "tool_calls": result.get("tool_calls_log", []),
    }


def _normalize_missing_info_form(
    response: str,
    completeness: dict,
    complaint_data: dict | None = None,
) -> str:
    """Ensure MissingInfoForm only lists blank keys; inject it if the model omitted it."""
    import re

    missing_keys = completeness.get("missingFieldKeys") or []
    missing_labels = completeness.get("missingFields") or []
    score = completeness.get("completenessScore", 0)
    complaint_data = complaint_data or {}

    product = complaint_data.get("productName") or ""
    batch = complaint_data.get("batchNumber") or ""
    severity = complaint_data.get("severityLevel") or ""
    risk = complaint_data.get("riskScore") or 0

    form_pattern = re.compile(r"<MissingInfoForm\b[^>]*?/?>", re.IGNORECASE)
    response = (response or "").strip()

    # Model often ends on a tool-call-only turn (empty content). Build a usable reply.
    if not response and (product or missing_keys):
        parts = [
            "I've extracted the complaint details into the form on the left.",
            f'<ComplaintCard title="Complaint Record" product="{product}" batch="{batch}" '
            f'severity="{severity}" risk="{risk}" />',
            f'<RiskGauge level="{severity}" score="{risk}" />',
            f'<CompletenessWidget score="{score}" missing="{", ".join(missing_labels)}" />',
        ]
        if missing_keys:
            parts.append(
                f'<MissingInfoForm title="Provide Missing Details" '
                f'fields="{",".join(missing_keys)}" '
                f'prompt="Please provide the remaining blank fields only." />'
            )
        else:
            parts.append(
                "The record looks complete. Click **Submit Complaint** on the left when ready."
            )
        return "\n\n".join(parts)

    if not response:
        return response

    response = re.sub(
        r"<CompletenessWidget\b[^>]*?/?>",
        f'<CompletenessWidget score="{score}" missing="{", ".join(missing_labels)}" />',
        response,
        count=1,
    )

    if not missing_keys:
        return form_pattern.sub("", response).strip()

    replacement = (
        f'<MissingInfoForm title="Provide Missing Details" '
        f'fields="{",".join(missing_keys)}" '
        f'prompt="Please provide the remaining blank fields only." />'
    )
    if form_pattern.search(response):
        return form_pattern.sub(replacement, response, count=1)
    # Fields still blank but model forgot the form — append it.
    return f"{response}\n\n{replacement}"
