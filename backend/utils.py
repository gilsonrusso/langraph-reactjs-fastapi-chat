import time
import json
import uuid

def _extract_stream_text(content) -> str:
    """Extrai texto de um chunk, lidando com formatos de lista ou string."""
    if not content:
        return ""
    if isinstance(content, list):
        return "".join(
            c.get("text", "") if isinstance(c, dict) else str(c) for c in content
        )
    return str(content)

def _build_sse_event(type_: str, **kwargs) -> str:
    """Constrói um ServerSentEvent com tipo, timestamp e dados adicionais."""
    data = {"type": type_, "timestamp": int(time.time() * 1000)}
    data.update(kwargs)
    return f"data: {json.dumps(data)}\n\n"

def _extract_msg_text_parts(content) -> list:
    """Extrai as partes de texto de um conteúdo de mensagem do LangChain."""
    if isinstance(content, str) and content:
        return [{"type": "text", "content": content}]

    parts = []
    if isinstance(content, list):
        for c in content:
            if isinstance(c, str):
                parts.append({"type": "text", "content": c})
            elif isinstance(c, dict) and "text" in c:
                parts.append({"type": "text", "content": c["text"]})
    return parts

def _convert_msg_to_tanstack(msg) -> dict:
    """Converte uma mensagem do LangChain para o formato esperado pelo TanStack UI."""
    role_map = {"human": "user", "ai": "assistant", "tool": "tool"}
    role = role_map.get(msg.type, "assistant")

    parts = _extract_msg_text_parts(msg.content)

    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            parts.append(
                {
                    "type": "tool-call",
                    "name": tc.get("name"),
                    "toolCallId": tc.get("id"),
                    "args": tc.get("args"),
                }
            )

    if msg.type == "tool":
        parts.append(
            {
                "type": "tool-result",
                "name": getattr(msg, "name", ""),
                "toolCallId": getattr(msg, "tool_call_id", ""),
                "result": msg.content,
            }
        )

    return {"id": getattr(msg, "id", str(uuid.uuid4())), "role": role, "parts": parts}
