"""WordPress-Tools — Beiträge, Seiten, Kommentare von WordPress-Sites."""

import httpx
from mcp.server.fastmcp import FastMCP

from src.db import save_connector, get_connector


async def _wp_request(connector_name: str, endpoint: str,
                      params: dict | None = None) -> dict | list:
    """HTTP-Request an die WordPress REST API senden."""
    connector = get_connector(connector_name)
    if connector is None:
        return {"error": f"Connector '{connector_name}' nicht gefunden. "
                         "Zuerst mit connect_wordpress einrichten."}

    base_url = connector["base_url"].rstrip("/")
    url = f"{base_url}/wp-json/wp/v2/{endpoint}"

    # Optional: Basic Auth falls API-Key hinterlegt
    headers = {}
    if connector.get("api_key"):
        headers["Authorization"] = f"Bearer {connector['api_key']}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.json()


def register_wordpress_tools(mcp: FastMCP):
    """WordPress-bezogene MCP-Tools registrieren."""

    @mcp.tool()
    async def connect_wordpress(connector_name: str, site_url: str,
                                api_key: str = "") -> dict:
        """WordPress-Site verbinden.

        Richtet eine Verbindung zu einer WordPress-Site ein.
        Die REST API muss aktiviert sein (Standard bei WordPress 4.7+).

        Args:
            connector_name: Eindeutiger Name für diese Verbindung
            site_url: WordPress Site URL (z.B. "https://mein-blog.de")
            api_key: Optional — Application Password oder JWT Token
        """
        site_url = site_url.rstrip("/")
        if not site_url.startswith("http"):
            site_url = f"https://{site_url}"

        # Verbindung testen — Site-Info abrufen
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{site_url}/wp-json")
                resp.raise_for_status()
                site_info = resp.json()
        except httpx.HTTPError as e:
            return {"error": f"Verbindung fehlgeschlagen: {e}",
                    "hint": "Prüfe ob die WordPress REST API aktiviert ist."}

        # Connector speichern
        save_connector(
            name=connector_name,
            platform="wordpress",
            base_url=site_url,
            api_key=api_key if api_key else None,
            config={
                "site_name": site_info.get("name", ""),
                "description": site_info.get("description", ""),
            },
        )

        return {
            "success": True,
            "connector_name": connector_name,
            "site_name": site_info.get("name", ""),
            "description": site_info.get("description", ""),
            "url": site_url,
            "message": f"WordPress-Site '{site_info.get('name', '')}' verbunden.",
        }

    @mcp.tool()
    async def wordpress_get_posts(connector_name: str,
                                  limit: int = 10,
                                  search: str = "") -> dict:
        """Beiträge von einer WordPress-Site abrufen.

        Args:
            connector_name: Name des WordPress-Connectors
            limit: Maximale Anzahl Beiträge (Standard: 10, Max: 50)
            search: Optional — Suchbegriff zum Filtern
        """
        limit = min(max(1, limit), 50)
        params = {"per_page": limit, "_embed": "true"}
        if search:
            params["search"] = search

        data = await _wp_request(connector_name, "posts", params)
        if isinstance(data, dict) and "error" in data:
            return data

        return {
            "connector": connector_name,
            "total_returned": len(data),
            "posts": [
                {
                    "id": p["id"],
                    "title": p.get("title", {}).get("rendered", ""),
                    "slug": p.get("slug", ""),
                    "status": p.get("status", ""),
                    "date": p.get("date", ""),
                    "excerpt": _strip_html(
                        p.get("excerpt", {}).get("rendered", "")
                    )[:200],
                    "link": p.get("link", ""),
                    "categories": p.get("categories", []),
                }
                for p in data
            ],
        }

    @mcp.tool()
    async def wordpress_get_pages(connector_name: str,
                                  limit: int = 10) -> dict:
        """Seiten von einer WordPress-Site abrufen.

        Args:
            connector_name: Name des WordPress-Connectors
            limit: Maximale Anzahl Seiten (Standard: 10, Max: 50)
        """
        limit = min(max(1, limit), 50)
        data = await _wp_request(
            connector_name, "pages", {"per_page": limit}
        )
        if isinstance(data, dict) and "error" in data:
            return data

        return {
            "connector": connector_name,
            "total_returned": len(data),
            "pages": [
                {
                    "id": p["id"],
                    "title": p.get("title", {}).get("rendered", ""),
                    "slug": p.get("slug", ""),
                    "status": p.get("status", ""),
                    "date": p.get("date", ""),
                    "link": p.get("link", ""),
                    "parent": p.get("parent", 0),
                }
                for p in data
            ],
        }

    @mcp.tool()
    async def wordpress_get_comments(connector_name: str,
                                     limit: int = 10,
                                     post_id: int = 0) -> dict:
        """Kommentare von einer WordPress-Site abrufen.

        Args:
            connector_name: Name des WordPress-Connectors
            limit: Maximale Anzahl Kommentare (Standard: 10, Max: 50)
            post_id: Optional — Nur Kommentare zu einem bestimmten Beitrag
        """
        limit = min(max(1, limit), 50)
        params = {"per_page": limit}
        if post_id > 0:
            params["post"] = post_id

        data = await _wp_request(connector_name, "comments", params)
        if isinstance(data, dict) and "error" in data:
            return data

        return {
            "connector": connector_name,
            "total_returned": len(data),
            "comments": [
                {
                    "id": c["id"],
                    "post_id": c.get("post", 0),
                    "author_name": c.get("author_name", ""),
                    "date": c.get("date", ""),
                    "content": _strip_html(
                        c.get("content", {}).get("rendered", "")
                    )[:300],
                    "status": c.get("status", ""),
                }
                for c in data
            ],
        }


def _strip_html(html: str) -> str:
    """Einfaches HTML-Tag-Entfernen für Vorschauen."""
    import re
    clean = re.sub(r"<[^>]+>", "", html)
    return clean.strip()
