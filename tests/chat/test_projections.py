"""Tests for the ModelMessage → ThreadMessageLike projection.

Pure-function coverage for each pydantic-ai part type we expect.
"""

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from brew.chat.projections import project_message


def test_user_prompt_projects_to_user_text() -> None:
    msg = ModelRequest(parts=[UserPromptPart(content="hi there")])
    out = project_message(msg)
    assert out == {"role": "user", "content": [{"type": "text", "text": "hi there"}]}


def test_assistant_text_projects_to_assistant_text() -> None:
    msg = ModelResponse(parts=[TextPart(content="hello!")])
    out = project_message(msg)
    assert out == {"role": "assistant", "content": [{"type": "text", "text": "hello!"}]}


def test_assistant_tool_call_projects_with_args() -> None:
    msg = ModelResponse(parts=[ToolCallPart(tool_name="brew_now", args={"profile_id": "p1"}, tool_call_id="call_abc")])
    out = project_message(msg)
    assert out == {
        "role": "assistant",
        "content": [
            {"type": "tool-call", "tool_call_id": "call_abc", "tool_name": "brew_now", "args": {"profile_id": "p1"}},
        ],
    }


def test_assistant_thinking_projects_as_reasoning() -> None:
    msg = ModelResponse(parts=[ThinkingPart(content="checking active bag…")])
    out = project_message(msg)
    assert out == {"role": "assistant", "content": [{"type": "reasoning", "text": "checking active bag…"}]}


def test_request_with_tool_return_projects_to_assistant_tool_result() -> None:
    msg = ModelRequest(parts=[ToolReturnPart(tool_name="brew_now", tool_call_id="call_abc", content={"status": "ok"})])
    out = project_message(msg)
    assert out == {
        "role": "assistant",
        "content": [
            {"type": "tool-result", "tool_call_id": "call_abc", "tool_name": "brew_now", "result": {"status": "ok"}},
        ],
    }


def test_system_prompt_only_returns_none() -> None:
    msg = ModelRequest(parts=[SystemPromptPart(content="be helpful")])
    assert project_message(msg) is None


def test_mixed_assistant_response_combines_parts() -> None:
    msg = ModelResponse(
        parts=[
            ThinkingPart(content="let me check"),
            TextPart(content="bumping ratio"),
            ToolCallPart(tool_name="update_profile", args={"ratio": 56}, tool_call_id="c1"),
        ]
    )
    out = project_message(msg)
    assert out == {
        "role": "assistant",
        "content": [
            {"type": "reasoning", "text": "let me check"},
            {"type": "text", "text": "bumping ratio"},
            {"type": "tool-call", "tool_call_id": "c1", "tool_name": "update_profile", "args": {"ratio": 56}},
        ],
    }
