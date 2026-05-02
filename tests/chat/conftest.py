import pytest

from brew.chat.config import get_chat_settings
from brew.errors import CloudUnreachableError


@pytest.fixture(autouse=True)
def _clear_chat_settings_cache():
    get_chat_settings.cache_clear()
    yield
    get_chat_settings.cache_clear()


def make_fake_chat_agent(events, *, raise_at_end=False):
    """Build a fake ChatAgent that yields scripted events.

    If `raise_at_end=True`, raises CloudUnreachableError after yielding all events.
    """

    class _FakeChatAgent:
        async def stream(self, prompt, history):  # noqa: ARG002
            for ev in events:
                yield ev
            if raise_at_end:
                raise CloudUnreachableError(message="fake mid-stream failure")

    return _FakeChatAgent()
