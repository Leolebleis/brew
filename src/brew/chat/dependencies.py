from brew.chat.service import ChatService


def get_chat_service() -> ChatService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
