"""Tests for A2UI message generator."""
import pytest
from src.a2ui.generator import A2UIGenerator


@pytest.fixture
def generator():
    return A2UIGenerator()


class TestA2UIGenerator:
    def test_text_reply(self, generator):
        data = {"type": "text_reply", "content": "Hello!"}
        messages = generator.generate(data)
        assert len(messages) >= 1
        update = [m for m in messages if m["type"] == "updateComponents"]
        assert len(update) == 1
        assert update[0]["components"][0]["type"] == "Text"
        assert update[0]["components"][0]["props"]["content"] == "Hello!"

    def test_info_card(self, generator):
        data = {
            "type": "info_card",
            "title": "Weather",
            "subtitle": "Shanghai",
            "items": ["Sunny 28C", "Humidity 60%"],
            "summary": "Nice day!",
        }
        messages = generator.generate(data)
        update = [m for m in messages if m["type"] == "updateComponents"]
        assert len(update) == 1
        components = update[0]["components"]
        titles = [c for c in components if c["props"].get("variant") == "heading"]
        assert len(titles) == 1
        assert titles[0]["props"]["content"] == "Weather"
        assert len(components) >= 4  # title + subtitle + 2 items + summary

    def test_location_list(self, generator):
        data = {
            "type": "location_list",
            "title": "Nearby",
            "places": [
                {"name": "Starbucks", "distance": "200m", "rating": "4.5"},
                {"name": "Costa", "distance": "500m", "rating": "4.2"},
            ],
        }
        messages = generator.generate(data)
        update = [m for m in messages if m["type"] == "updateComponents"]
        assert len(update) == 1

    def test_create_surface_message(self, generator):
        data = {"type": "text_reply", "content": "test"}
        messages = generator.generate(data)
        create = [m for m in messages if m["type"] == "createSurface"]
        assert len(create) == 1
        assert "surfaceId" in create[0]

    def test_unknown_type_fallback(self, generator):
        data = {"type": "unknown_type", "foo": "bar"}
        messages = generator.generate(data)
        assert len(messages) >= 1
