"""Chat service — orchestrates the chat repository."""

from pydantic_ai import Agent

from brew.chat.model.message import ChatMessage, ChatMessageCreate
from brew.chat.repository import ChatRepository


class ChatService:
    def __init__(self, repo: ChatRepository, agent: Agent) -> None:
        self._repo = repo
        self._agent = agent

    async def append_message(self, create: ChatMessageCreate) -> ChatMessage:
        return await self._repo.append(create)

    async def get_thread(self, thread_id: str) -> list[ChatMessage]:
        return await self._repo.list_thread(thread_id)

    async def list_threads(self) -> list[str]:
        return await self._repo.list_threads()
