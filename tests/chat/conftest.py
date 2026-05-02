import pytest

from brew.chat.config import get_chat_settings
from brew.errors import CloudUnreachableError


@pytest.fixture(autouse=True)
def _clear_chat_settings_cache():
    get_chat_settings.cache_clear()
    yield
    get_chat_settings.cache_clear()


def make_fake_chat_agent(events, raise_after=None):
    """Build a fake ChatAgent that yields scripted events.

    `raise_after` (optional int): raise CloudUnreachableError after yielding
    that many events (e.g. raise_after=2 yields events[0], events[1], then
    raises). Works whether or not events has more entries past `raise_after`.
    """

    class _FakeChatAgent:
        async def stream(self, prompt, history):  # noqa: ARG002
            for i, ev in enumerate(events):
                if raise_after is not None and i >= raise_after:
                    raise CloudUnreachableError(message="fake mid-stream failure")
                yield ev
            if raise_after is not None:
                raise CloudUnreachableError(message="fake mid-stream failure")

    return _FakeChatAgent()
