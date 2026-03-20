"""Connector-Verwaltungs-Tools — Übersicht und Status aller Business-Connectors."""

from mcp.server.fastmcp import FastMCP

from src.db import list_connectors as db_list_connectors, get_connector

# Verfügbare Plattformen mit Beschreibungen
AVAILABLE_PLATFORMS = {
    "shopify": {
        "name": "Shopify",
        "description": "E-Commerce — Produkte, Bestellungen, Inventar",
        "requires": ["store_url", "api_key"],
    },
    "wordpress": {
        "name": "WordPress",
        "description": "CMS — Beiträge, Seiten, Kommentare",
        "requires": ["site_url"],
    },
    "calendly": {
        "name": "Calendly",
        "description": "Terminplanung — Verfügbarkeit, Event-Typen",
        "requires": ["api_key"],
    },
}


def register_connector_tools(mcp: FastMCP):
    """Connector-Verwaltungs-Tools registrieren."""

    @mcp.tool()
    async def list_connectors() -> dict:
        """Alle verfügbaren Business-Connectors anzeigen.

        Zeigt sowohl verfügbare Plattformen als auch bereits
        konfigurierte Verbindungen.
        """
        configured = db_list_connectors()
        configured_names = {c["name"] for c in configured}

        return {
            "available_platforms": AVAILABLE_PLATFORMS,
            "configured_connectors": [
                {
                    "name": c["name"],
                    "platform": c["platform"],
                    "base_url": c["base_url"],
                    "has_api_key": bool(c.get("api_key")),
                    "created_at": c["created_at"],
                }
                for c in configured
            ],
            "total_configured": len(configured_names),
            "total_available": len(AVAILABLE_PLATFORMS),
        }

    @mcp.tool()
    async def get_connector_status(connector_name: str) -> dict:
        """Status eines bestimmten Connectors prüfen.

        Zeigt ob der Connector konfiguriert ist und welche
        Einstellungen hinterlegt sind.

        Args:
            connector_name: Name des Connectors (z.B. "mein-shop")
        """
        connector = get_connector(connector_name)
        if connector is None:
            return {
                "configured": False,
                "message": f"Connector '{connector_name}' ist nicht konfiguriert.",
                "hint": "Nutze connect_shopify, connect_wordpress oder "
                        "connect_calendly um einen Connector einzurichten.",
            }

        return {
            "configured": True,
            "name": connector["name"],
            "platform": connector["platform"],
            "base_url": connector["base_url"],
            "has_api_key": bool(connector.get("api_key")),
            "config": connector["config"],
            "created_at": connector["created_at"],
            "updated_at": connector["updated_at"],
        }
