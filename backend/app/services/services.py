import uuid
import json
from collections.abc import AsyncIterable

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from ..core.config import langfuse_handler
from .utils import _build_sse_event
from ..core.logger import logger
from ..schemas.schemas import Decision


async def stream_chat(
    agent, message_text: str | None, thread_id: str, decision: Decision | None = None
) -> AsyncIterable[str]:
    config = {"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]}
    run_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())

    def logged_yield(event):
        logger.debug(f"Yielding SSE event: {event[:100]}...")
        return event

    yield logged_yield(_build_sse_event("RUN_STARTED", runId=run_id))
    yield logged_yield(_build_sse_event("TEXT_MESSAGE_START", messageId=msg_id, role="assistant"))

    state_next = False
    try:
        # Determine the input for astream_events
        if decision:
            input_data = Command(resume={"decisions": [decision.model_dump(exclude_none=True)]})
        else:
            input_data = {"messages": [HumanMessage(content=message_text)]}

        async for event in agent.astream_events(
            input_data,
            config,
            stream_mode=["updates", "custom"],
            version="v2",
        ):
            kind = event.get("event")
            
            # 1. Detect Interrupts (HITL) during stream
            if kind == "on_chain_stream":
                data = event.get("data", {})
                chunk = data.get("chunk", [])
                if isinstance(chunk, tuple) and len(chunk) > 1:
                    updates = chunk[1]
                    if isinstance(updates, dict) and "__interrupt__" in updates:
                        interrupt_data = updates["__interrupt__"]
                        if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                            hitl_data = interrupt_data[0].value if hasattr(interrupt_data[0], "value") else interrupt_data[0]
                            
                            logger.info(f"Interrupt detected: {hitl_data}")
                            state_next = True
                            
                            # Envia anotações da mensagem (muitas bibliotecas usam isso para metadados)
                            yield _build_sse_event(
                                "MESSAGE_ANNOTATIONS",
                                messageId=msg_id,
                                annotations=[{"hitl_request": hitl_data}],
                                metadata={"hitl_request": hitl_data}
                            )
                            
                            tc_id = f"hitl-{uuid.uuid4()}"
                            
                            # Voltando para os nomes MAIÚSCULOS que o frontend detectava
                            yield _build_sse_event(
                                "TOOL_CALL_START",
                                messageId=msg_id,
                                toolCallId=tc_id,
                                toolName="human_review",
                                name="human_review",
                                args=json.dumps(hitl_data),
                                arguments=json.dumps(hitl_data),
                                metadata={"hitl_request": hitl_data}
                            )
                            # Enviamos um chunk também, por segurança
                            yield _build_sse_event(
                                "TOOL_CALL_CHUNK",
                                messageId=msg_id,
                                toolCallId=tc_id,
                                args=json.dumps(hitl_data),
                                arguments=json.dumps(hitl_data)
                            )
                            yield _build_sse_event(
                                "TOOL_CALL_RESULT",
                                messageId=msg_id,
                                toolCallId=tc_id,
                                result="pending"
                            )

            elif kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk", {}).content
                if content:
                    yield logged_yield(_build_sse_event("TEXT_MESSAGE_CHUNK", messageId=msg_id, chunk=content))

            elif kind == "on_tool_start":
                tc_id = event.get("run_id", str(uuid.uuid4()))
                tc_args = event.get("data", {}).get("input")
                yield _build_sse_event(
                    "TOOL_CALL_START",
                    messageId=msg_id,
                    toolCallId=tc_id,
                    toolName=event.get("name", "tool"),
                    name=event.get("name", "tool"),
                    args=json.dumps(tc_args) if tc_args else "{}",
                    arguments=json.dumps(tc_args) if tc_args else "{}"
                )
                yield _build_sse_event(
                    "TOOL_CALL_CHUNK",
                    messageId=msg_id,
                    toolCallId=tc_id,
                    args=json.dumps(tc_args) if tc_args else "{}",
                    arguments=json.dumps(tc_args) if tc_args else "{}"
                )

    except Exception as e:
        logger.error(f"Error in stream_chat: {e}", exc_info=True)
        yield _build_sse_event("ERROR", content=str(e))

    yield _build_sse_event("TEXT_MESSAGE_END", messageId=msg_id)
    yield _build_sse_event("RUN_FINISHED", runId=run_id, finishReason="stop" if state_next else "done")
