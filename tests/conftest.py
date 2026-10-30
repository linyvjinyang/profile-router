import pytest

from profile_router import i18n


@pytest.fixture(autouse=True)
def chinese_ui():
    """Tests assert the Chinese source texts, so pin the UI language regardless of the machine's locale."""
    i18n.set_language("zh")
    yield
    i18n.set_language("zh")
