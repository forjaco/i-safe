import pytest

from app.application.use_cases.check_email import CheckEmailUseCase
from app.core.config import settings


class ExplodingSession:
    def add(self, obj):
        raise AssertionError("add should not be called when persistence is disabled")

    async def commit(self):
        raise AssertionError("commit should not be called when persistence is disabled")


@pytest.mark.asyncio
async def test_osint_check_skips_persistence_when_diagnostic_mode_is_enabled():
    previous_mock = settings.EMAIL_CHECK_USE_MOCK
    previous_persist = settings.OSINT_PERSIST_RESULTS
    try:
        settings.EMAIL_CHECK_USE_MOCK = True
        settings.OSINT_PERSIST_RESULTS = False

        result = await CheckEmailUseCase.execute("qa@example.com", ExplodingSession())

        assert result["status"] == "MOCK_SUCCESS"
        assert result["sites"] == ["Canva (Mock)", "LinkedIn (2012)"]
    finally:
        settings.EMAIL_CHECK_USE_MOCK = previous_mock
        settings.OSINT_PERSIST_RESULTS = previous_persist
