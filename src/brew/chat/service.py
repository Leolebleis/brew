"""Chat service — orchestrates persistence + agent streaming."""

import json
from collections.abc import AsyncIterator

from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelRequest, UserPromptPart

from brew.chat.client import ChatAgent
from brew.chat.model.event import (
    AgentDone,
    ChatStreamEvent,
    Done,
    Error,
)
from brew.chat.model.message import ChatMessage, ChatMessageCreate
from brew.chat.repository import ChatRepository
from brew.datetime_utils import to_iso
from brew.errors import DomainError, NotFoundError

_KIND = "chat_message"


def _build_user_request_payload(text: str) -> dict:
    """Build the canonical ModelRequest JSON for an eager user-row write."""
    msg = ModelRequest(parts=[UserPromptPart(content=text)])
    payload_bytes = ModelMessagesTypeAdapter.dump_json([msg])
    return json.loads(payload_bytes.decode())[0]


class ChatService:
    def __init__(self, repo: ChatRepository, agent: ChatAgent) -> None:
        self._repo = repo
        self._agent = agent

    async def append_message(self, create: ChatMessageCreate) -> ChatMessage:
        return await self._repo.append(create)

    async def get_thread(
        self,
        thread_id: str,
        *,
        limit: int = 50,
        before_id: str | None = None,
    ) -> tuple[list[ChatMessage], str | None]:
        """Return (messages newest-first, next_before_id).

        `next_before_id` is set to the oldest message's id iff the page is full.
        Raises NotFoundError when `before_id` is provided but unknown.
        """
        before_tuple: tuple[str, int] | None = None
        if before_id is not None:
            cursor_msg = await self._repo.get_message(before_id)
            if cursor_msg is None:
                raise NotFoundError.for_resource(_KIND, before_id)
            # Fetch raw rowid via the repo's connection (private invariant).
            row_cursor = await self._repo._conn.execute(  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                "SELECT rowid FROM chat_messages WHERE id = ?",
                (before_id,),
            )
            row = await row_cursor.fetchone()
            assert row is not None, f"row missing for {before_id} after get_message returned non-None"  # noqa: S101
            before_tuple = (to_iso(cursor_msg.created_at), row["rowid"])

        messages = await self._repo.list_thread(thread_id, limit=limit, before=before_tuple)

        next_before_id: str | None = None
        if len(messages) == limit and messages:
            next_before_id = messages[-1].id

        return messages, next_before_id

    async def get_message(self, message_id: str) -> ChatMessage | None:
        return await self._repo.get_message(message_id)

    async def list_threads(self) -> list[str]:
        return await self._repo.list_threads()

    async def stream_message(
        self,
        thread_id: str,
        text: str,
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream a chat turn — user-row eager, assistant-row atomic on AgentDone.

        Mid-stream errors yield Error(code, message) and stop; the user-row
        stays as an orphan (interpretable on replay as "this turn errored").
        """
        # Load capped history for the agent (oldest-first).
        history = await self._repo.load_history(thread_id)
        history_payloads = [m.payload for m in history]

        # Eager user-row write — visible in replay even if the run errors mid-stream.
        await self._repo.append(
            ChatMessageCreate(
                thread_id=thread_id,
                kind="request",
                payload=_build_user_request_payload(text),
            )
        )

        try:
            async for ev in self._agent.stream(prompt=text, history=history_payloads):
                if isinstance(ev, AgentDone):
                    # Persist assistant-row, emit wire-side Done(message_id).
                    asst = await self._repo.append(
                        ChatMessageCreate(
                            thread_id=thread_id,
                            kind="response",
                            payload=ev.payload,
                        )
                    )
                    yield Done(message_id=asst.id)
                else:
                    # Pass-through: TextDelta / ToolCallStart / ToolCallDelta /
                    # ToolCallResult / ThinkingDelta / Error.
                    yield ev
        except DomainError as exc:
            yield Error(code=exc.code, message=exc.message)
        except Exception as exc:  # noqa: BLE001
            yield Error(code="unknown", message=str(exc))
