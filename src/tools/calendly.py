"""Calendly-Tools — Verfügbarkeit und Event-Typen über die Calendly API."""

import httpx
from mcp.server.fastmcp import FastMCP

from src.db import save_connector, get_connector

# Calendly API v2 Basis-URL
CALENDLY_API_URL = "https://api.calendly.com"


async def _calendly_request(connector_name: str, endpoint: str,
                            params: dict | None = None) -> dict:
    """HTTP-Request an die Calendly API senden."""
    connector = get_connector(connector_name)
    if connector is None:
        return {"error": f"Connector '{connector_name}' nicht gefunden. "
                         "Zuerst mit connect_calendly einrichten."}

    api_key = connector.get("api_key", "")
    if not api_key:
        return {"error": "Kein API-Key für diesen Connector hinterlegt."}

    url = f"{CALENDLY_API_URL}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.json()


def register_calendly_tools(mcp: FastMCP):
    """Calendly-bezogene MCP-Tools registrieren."""

    @mcp.tool()
    async def connect_calendly(connector_name: str,
                               api_key: str) -> dict:
        """Calendly-Account verbinden.

        Richtet eine Verbindung zum Calendly-Account ein.
        Benötigt einen Personal Access Token von calendly.com/integrations.

        Args:
            connector_name: Eindeutiger Name für diese Verbindung
            api_key: Calendly Personal Access Token
        """
        # Verbindung testen — eigenen User abrufen
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{CALENDLY_API_URL}/users/me", headers=headers
                )
                resp.raise_for_status()
                user_data = resp.json().get("resource", {})
        except httpx.HTTPError as e:
            return {"error": f"Verbindung fehlgeschlagen: {e}",
                    "hint": "Prüfe den Personal Access Token."}

        # User-URI speichern für spätere Abfragen
        user_uri = user_data.get("uri", "")

        save_connector(
            name=connector_name,
            platform="calendly",
            base_url=CALENDLY_API_URL,
            api_key=api_key,
            config={
                "user_name": user_data.get("name", ""),
                "user_uri": user_uri,
                "email": user_data.get("email", ""),
            },
        )

        return {
            "success": True,
            "connector_name": connector_name,
            "user_name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "message": f"Calendly-Account '{user_data.get('name', '')}' verbunden.",
        }

    @mcp.tool()
    async def calendly_get_event_types(connector_name: str) -> dict:
        """Event-Typen (Terminarten) aus Calendly abrufen.

        Zeigt alle aktiven Terminarten mit Dauer und Buchungs-URLs.

        Args:
            connector_name: Name des Calendly-Connectors
        """
        connector = get_connector(connector_name)
        if connector is None:
            return {"error": f"Connector '{connector_name}' nicht gefunden."}

        user_uri = connector.get("config", {}).get("user_uri", "")
        if not user_uri:
            return {"error": "User-URI nicht gefunden. Connector neu einrichten."}

        data = await _calendly_request(
            connector_name, "event_types",
            {"user": user_uri, "active": "true"},
        )
        if "error" in data:
            return data

        event_types = data.get("collection", [])
        return {
            "connector": connector_name,
            "total": len(event_types),
            "event_types": [
                {
                    "name": et.get("name", ""),
                    "slug": et.get("slug", ""),
                    "duration": et.get("duration", 0),
                    "kind": et.get("kind", ""),
                    "active": et.get("active", False),
                    "scheduling_url": et.get("scheduling_url", ""),
                    "description": (et.get("description_plain") or "")[:200],
                }
                for et in event_types
            ],
        }

    @mcp.tool()
    async def calendly_check_availability(connector_name: str,
                                          start_time: str,
                                          end_time: str) -> dict:
        """Verfügbarkeit in einem Zeitraum prüfen.

        Zeigt geplante Events im angegebenen Zeitraum.
        Freie Slots sind die Lücken zwischen den Events.

        Args:
            connector_name: Name des Calendly-Connectors
            start_time: Startzeit im ISO-Format (z.B. "2026-03-20T09:00:00Z")
            end_time: Endzeit im ISO-Format (z.B. "2026-03-20T18:00:00Z")
        """
        connector = get_connector(connector_name)
        if connector is None:
            return {"error": f"Connector '{connector_name}' nicht gefunden."}

        user_uri = connector.get("config", {}).get("user_uri", "")
        if not user_uri:
            return {"error": "User-URI nicht gefunden. Connector neu einrichten."}

        data = await _calendly_request(
            connector_name, "scheduled_events",
            {
                "user": user_uri,
                "min_start_time": start_time,
                "max_start_time": end_time,
                "status": "active",
            },
        )
        if "error" in data:
            return data

        events = data.get("collection", [])
        return {
            "connector": connector_name,
            "time_range": {"start": start_time, "end": end_time},
            "scheduled_events": len(events),
            "events": [
                {
                    "name": ev.get("name", ""),
                    "start_time": ev.get("start_time", ""),
                    "end_time": ev.get("end_time", ""),
                    "status": ev.get("status", ""),
                    "event_type": ev.get("event_type", ""),
                }
                for ev in events
            ],
            "hint": "Freie Slots liegen zwischen den aufgelisteten Events.",
        }
