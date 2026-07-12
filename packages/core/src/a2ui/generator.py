"""A2UI JSON message generator for wearable device rendering."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class A2UIGenerator:
    """Generates A2UI protocol messages from structured data."""

    def generate(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert structured agent data into A2UI message sequence."""
        surface_id = f"surface-{uuid4().hex[:8]}"
        msg_type = data.get("type", "text_reply")

        if msg_type == "info_card":
            return self._gen_info_card(surface_id, data)
        elif msg_type == "location_list":
            return self._gen_location_list(surface_id, data)
        elif msg_type == "text_reply":
            return self._gen_text_reply(surface_id, data)
        else:
            return self._gen_text_reply(surface_id, {"content": str(data)})

    def _gen_info_card(self, surface_id: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate A2UI messages for an info card."""
        components = [
            {
                "id": f"{surface_id}-title",
                "type": "Text",
                "props": {
                    "content": data.get("title", ""),
                    "variant": "heading",
                },
            },
        ]

        if data.get("subtitle"):
            components.append({
                "id": f"{surface_id}-subtitle",
                "type": "Text",
                "props": {
                    "content": data["subtitle"],
                    "variant": "caption",
                },
            })

        # Add list items
        for i, item in enumerate(data.get("items", [])):
            components.append({
                "id": f"{surface_id}-item-{i}",
                "type": "Text",
                "props": {
                    "content": f"• {item}",
                    "variant": "body",
                },
            })

        if data.get("summary"):
            components.append({
                "id": f"{surface_id}-summary",
                "type": "Text",
                "props": {
                    "content": data["summary"],
                    "variant": "caption",
                },
            })

        return [
            {
                "type": "createSurface",
                "surfaceId": surface_id,
                "presentation": {"mode": "card"},
            },
            {
                "type": "updateComponents",
                "surfaceId": surface_id,
                "components": components,
            },
        ]

    def _gen_location_list(self, surface_id: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate A2UI messages for a location list."""
        components = [
            {
                "id": f"{surface_id}-title",
                "type": "Text",
                "props": {
                    "content": data.get("title", "Nearby"),
                    "variant": "heading",
                },
            },
        ]

        for i, place in enumerate(data.get("places", [])):
            name = place.get("name", "Unknown")
            distance = place.get("distance", "")
            rating = place.get("rating", "")
            subtitle = f"{distance}" + (f" · ⭐{rating}" if rating else "")
            components.append({
                "id": f"{surface_id}-place-{i}",
                "type": "Text",
                "props": {
                    "content": f"📍 {name}",
                    "variant": "body",
                },
            })
            if subtitle:
                components.append({
                    "id": f"{surface_id}-place-info-{i}",
                    "type": "Text",
                    "props": {
                        "content": f"   {subtitle}",
                        "variant": "caption",
                    },
                })

        return [
            {
                "type": "createSurface",
                "surfaceId": surface_id,
                "presentation": {"mode": "card"},
            },
            {
                "type": "updateComponents",
                "surfaceId": surface_id,
                "components": components,
            },
        ]

    def _gen_text_reply(self, surface_id: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate A2UI messages for a simple text reply."""
        return [
            {
                "type": "createSurface",
                "surfaceId": surface_id,
                "presentation": {"mode": "card"},
            },
            {
                "type": "updateComponents",
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": f"{surface_id}-text",
                        "type": "Text",
                        "props": {
                            "content": data.get("content", ""),
                            "variant": "body",
                        },
                    }
                ],
            },
        ]