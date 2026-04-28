import uuid
from collections.abc import AsyncIterable

from langchain_core.messages import HumanMessage

from config import langfuse_handler
from utils import _build_sse_event, _extract_stream_text


async def stream_chat(agent, message_text: str, thread_id: str) -> AsyncIterable[str]:
    config = {"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]}
    run_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())

    yield _build_sse_event("RUN_STARTED", runId=run_id)
    yield _build_sse_event("TEXT_MESSAGE_START", messageId=msg_id, role="assistant")

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message_text)]}, config, version="v2"
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                text = _extract_stream_text(event["data"]["chunk"].content)
                if text:
                    yield _build_sse_event(
                        "TEXT_MESSAGE_CONTENT", messageId=msg_id, delta=text
                    )

            elif kind == "on_tool_start":
                yield _build_sse_event(
                    "TOOL_CALL_START",
                    toolCallId=event.get("run_id", str(uuid.uuid4())),
                    toolName=event.get("name", "tool"),
                    parentMessageId=msg_id,
                )

            elif kind == "on_tool_end":
                result_data = event.get("data", {}).get("output")
                result_str = (
                    str(result_data.content)
                    if hasattr(result_data, "content")
                    else str(result_data)
                )

                yield _build_sse_event(
                    "TOOL_CALL_END",
                    toolCallId=event.get("run_id", str(uuid.uuid4())),
                    toolName=event.get("name", "tool"),
                    result=result_str,
                )

    except Exception as e:
        yield _build_sse_event("RUN_ERROR", runId=run_id, error={"message": str(e)})

    yield _build_sse_event("TEXT_MESSAGE_END", messageId=msg_id)
    yield _build_sse_event("RUN_FINISHED", runId=run_id, finishReason="stop")
