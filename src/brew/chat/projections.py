"""Project pydantic-ai ModelMessage payloads into assistant-ui ThreadMessageLike shape.

Walls off pydantic-ai part-type churn from the frontend. Raw ModelMessage stays
in chat_messages.payload; this projection runs at read time.

Returns None for messages that don't surface in the user-facing thread (system
prompts, retry prompts). Callers filter Nones.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)


def project_message(msg: ModelMessage) -> dict[str, Any] | None:
    if isinstance(msg, ModelRequest):
        return _project_request(msg)
    if isinstance(msg, ModelResponse):
        return _project_response(msg)
    return {"role": "assistant", "content": [{"type": "text", "text": str(msg)}]}


def _project_request(msg: ModelRequest) -> dict[str, Any] | None:
    user_parts: list[dict[str, Any]] = []
    tool_result_parts: list[dict[str, Any]] = []

    for part in msg.parts:
        if isinstance(part, UserPromptPart):
            text = part.content if isinstance(part.content, str) else str(part.content)
            user_parts.append({"type": "text", "text": text})
        elif isinstance(part, ToolReturnPart):
            tool_result_parts.append(
                {
                    "type": "tool-result",
                    "tool_call_id": part.tool_call_id,
                    "tool_name": part.tool_name,
                    "result": part.content,
                }
            )
        elif isinstance(part, (SystemPromptPart, RetryPromptPart)):
            continue
        else:
            user_parts.append({"type": "text", "text": str(part)})

    if user_parts and not tool_result_parts:
        return {"role": "user", "content": user_parts}
    if tool_result_parts and not user_parts:
        return {"role": "assistant", "content": tool_result_parts}
    if user_parts and tool_result_parts:
        return {"role": "user", "content": user_parts}
    return None


def _project_response(msg: ModelResponse) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    for part in msg.parts:
        if isinstance(part, TextPart):
            content.append({"type": "text", "text": part.content})
        elif isinstance(part, ToolCallPart):
            args = part.args_as_dict() if hasattr(part, "args_as_dict") else (part.args or {})
            content.append(
                {
                    "type": "tool-call",
                    "tool_call_id": part.tool_call_id,
                    "tool_name": part.tool_name,
                    "args": args,
                }
            )
        elif isinstance(part, ThinkingPart):
            content.append({"type": "reasoning", "text": part.content})
        else:
            content.append({"type": "text", "text": str(part)})
    return {"role": "assistant", "content": content}
