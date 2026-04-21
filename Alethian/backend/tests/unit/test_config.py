import os
from unittest import mock
from app.core.config import Settings

def test_settings_default_fallbacks():
    with mock.patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        assert settings.MIN_TEXT_LENGTH == 50
        assert settings.OCR_DPI == 300
        assert settings.GROBID_TIMEOUT == 120

def test_settings_environment_overrides():
    with mock.patch.dict(os.environ, {"OCR_DPI": "150", "FETCHER_TIMEOUT": "5.0"}, clear=True):
        settings = Settings()
        assert settings.OCR_DPI == 150
        assert settings.FETCHER_TIMEOUT == 5.0
