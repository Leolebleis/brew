import pytest

from brew.chat.config import get_chat_settings


@pytest.fixture(autouse=True)
def _clear_chat_settings_cache():
    get_chat_settings.cache_clear()
    yield
    get_chat_settings.cache_clear()
