"""
Chat router – exposes three endpoints:
  POST /api/chat          → SSE stream of agent events
  GET  /api/health        → simple health-check
  DELETE /api/sessions/{id} → clear a session's message history
"""
import json
import uuid
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

router = APIRouter()

# In-memory session store: session_id → list[BaseMessage]
sessions: dict[str, list] = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_serializable(obj):
    """Recursively convert non-JSON-serializable objects to strings."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat")
async def chat(request: ChatRequest):
    from app.main import graph  # imported here to avoid circular import at startup

    session_id = request.session_id or str(uuid.uuid4())
    history: list = sessions.get(session_id, [])

    all_messages = history + [HumanMessage(content=request.message)]

    initial_state = {
        "messages": all_messages,
        "tool_trace": [],
    }

    async def generate():
        final_output: dict | None = None

        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                etype: str = event["event"]
                ename: str = event.get("name", "")
                edata: dict = event.get("data", {})

                # ---- Tool call started ----
                if etype == "on_tool_start":
                    raw_input = edata.get("input", {})
                    payload = {
                        "type": "tool_start",
                        "tool_name": ename,
                        "input": _make_serializable(raw_input),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                # ---- Tool call completed ----
                elif etype == "on_tool_end":
                    raw_output = edata.get("output")
                    if hasattr(raw_output, "content"):
                        output_val = raw_output.content
                    else:
                        output_val = str(raw_output) if raw_output is not None else ""
                    payload = {
                        "type": "tool_end",
                        "tool_name": ename,
                        "output": output_val,
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                # ---- Streaming LLM tokens ----
                elif etype == "on_chat_model_stream":
                    chunk = edata.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload = {"type": "token", "content": chunk.content}
                        yield f"data: {json.dumps(payload)}\n\n"

                # ---- Graph completed ----
                elif etype == "on_chain_end":
                    output = edata.get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        final_output = output

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

        # ---- Persist session and send done event ----
        if final_output is not None:
            sessions[session_id] = list(final_output.get("messages", []))
            tool_trace = _make_serializable(final_output.get("tool_trace", []))
        else:
            tool_trace = []

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'tool_trace': tool_trace})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@router.get("/products")
async def list_products():
    from app.agent.tools.catalog_tools import PRODUCT_CATALOG
    return {"products": PRODUCT_CATALOG}


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}
