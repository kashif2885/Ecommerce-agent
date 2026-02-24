"""
Pure ReAct agent – no explicit intent router.

Graph topology:
    START → agent ⇄ tools → END

The LLM receives all tools simultaneously.  Rich tool descriptions guide it
to select the right tool for each user request.  The ReAct loop continues
until the model produces a response without any tool calls.
"""
from __future__ import annotations

import operator
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Sequence, TypedDict
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# ---------------------------------------------------------------------------
# Module-level constants  (after all imports – PEP 8 E402 compliant)
# ---------------------------------------------------------------------------
TIMEZONE = ZoneInfo("Asia/Riyadh")
_PROMPT_PATH = Path(__file__).parent / "prompt.md"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_trace: Annotated[list, operator.add]


# ---------------------------------------------------------------------------
# System prompt  (generated fresh on every agent call so the time is current)
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    now = datetime.now(tz=TIMEZONE)
    date_str = now.strftime("%A, %d %B %Y")   # e.g. Monday, 24 February 2026
    time_str = now.strftime("%I:%M %p %Z")    # e.g. 03:45 PM AST
    return _PROMPT_TEMPLATE.replace("{{DATE}}", date_str).replace("{{TIME}}", time_str)


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(vectorstore, model_name: str, api_key: str):
    """Build and compile the pure ReAct LangGraph agent."""

    from app.agent.tools.calendar_tools import (
        book_appointment,
        cancel_appointment,
        check_availability,
        list_appointments,
    )
    from app.agent.tools.catalog_tools import (
        compare_products,
        get_product_details,
        search_products,
    )
    from app.agent.tools.rag_tools import make_rag_tool

    search_knowledge_base = make_rag_tool(vectorstore)

    all_tools = [
        check_availability,
        book_appointment,
        cancel_appointment,
        list_appointments,
        search_products,
        get_product_details,
        compare_products,
        search_knowledge_base,
    ]
    tool_map: dict[str, object] = {t.name: t for t in all_tools}

    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        openai_api_key=api_key,
        streaming=True,
    )
    llm_with_tools = llm.bind_tools(all_tools)

    # ------------------------------------------------------------------
    # Node: agent  (LLM decides which tools to call)
    # ------------------------------------------------------------------
    def agent_node(state: AgentState) -> dict:
        messages = [SystemMessage(content=_build_system_prompt())] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # ------------------------------------------------------------------
    # Node: tools  (execute every tool_call from the last AI message)
    # ------------------------------------------------------------------
    def tools_node(state: AgentState) -> dict:
        last_message = state["messages"][-1]
        results: list[ToolMessage] = []
        traces: list[dict] = []

        for tc in last_message.tool_calls:
            tool_name: str = tc["name"]
            tool_args: dict = tc["args"]

            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_args)
                    result_str = result if isinstance(result, str) else str(result)
                except Exception as exc:
                    result_str = f"Tool error: {exc}"
            else:
                result_str = f"Unknown tool: {tool_name}"

            results.append(
                ToolMessage(
                    content=result_str,
                    tool_call_id=tc["id"],
                    name=tool_name,
                )
            )
            traces.append(
                {
                    "step": "tool_call",
                    "tool_name": tool_name,
                    "input": tool_args,
                    "output": result_str,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return {"messages": results, "tool_trace": traces}

    # ------------------------------------------------------------------
    # Conditional edge: loop back if the LLM made tool calls
    # ------------------------------------------------------------------
    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        last_msg = state["messages"][-1]
        if isinstance(last_msg, AIMessage) and getattr(last_msg, "tool_calls", None):
            return "tools"
        return END

    # ------------------------------------------------------------------
    # Assemble graph
    # ------------------------------------------------------------------
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
