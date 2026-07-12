"""Tests for config module."""


def test_settings_loads():
    from src.config import settings
    assert settings.openai_base_url
    assert settings.openai_model
    assert settings.backend_port > 0
