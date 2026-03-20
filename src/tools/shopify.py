"""Shopify-Tools — Produkte, Bestellungen, Inventar von Shopify-Stores."""

import httpx
from mcp.server.fastmcp import FastMCP

from src.db import save_connector, get_connector


async def _shopify_request(connector_name: str, endpoint: str,
                           params: dict | None = None) -> dict:
    """HTTP-Request an die Shopify Admin API senden."""
    connector = get_connector(connector_name)
    if connector is None:
        return {"error": f"Connector '{connector_name}' nicht gefunden. "
                         "Zuerst mit connect_shopify einrichten."}

    base_url = connector["base_url"].rstrip("/")
    api_key = connector.get("api_key", "")

    # Shopify Admin API URL aufbauen
    url = f"{base_url}/admin/api/2024-01/{endpoint}.json"
    headers = {"X-Shopify-Access-Token": api_key}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.json()


def register_shopify_tools(mcp: FastMCP):
    """Shopify-bezogene MCP-Tools registrieren."""

    @mcp.tool()
    async def connect_shopify(connector_name: str, store_url: str,
                              api_key: str) -> dict:
        """Shopify-Store verbinden.

        Richtet eine Verbindung zu einem Shopify-Store ein.
        Danach können Produkte, Bestellungen und Inventar abgefragt werden.

        Args:
            connector_name: Eindeutiger Name für diese Verbindung (z.B. "mein-shop")
            store_url: Shopify Store URL (z.B. "https://mein-shop.myshopify.com")
            api_key: Shopify Admin API Access Token
        """
        # URL normalisieren
        store_url = store_url.rstrip("/")
        if not store_url.startswith("http"):
            store_url = f"https://{store_url}"

        # Verbindung testen
        try:
            url = f"{store_url}/admin/api/2024-01/shop.json"
            headers = {"X-Shopify-Access-Token": api_key}
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                shop_data = resp.json().get("shop", {})
        except httpx.HTTPError as e:
            return {"error": f"Verbindung fehlgeschlagen: {e}",
                    "hint": "Prüfe Store-URL und API-Key."}

        # Connector speichern
        save_connector(
            name=connector_name,
            platform="shopify",
            base_url=store_url,
            api_key=api_key,
            config={"shop_name": shop_data.get("name", "")},
        )

        return {
            "success": True,
            "connector_name": connector_name,
            "shop_name": shop_data.get("name", ""),
            "shop_domain": shop_data.get("domain", ""),
            "message": f"Shopify-Store '{shop_data.get('name', '')}' verbunden.",
        }

    @mcp.tool()
    async def shopify_get_products(connector_name: str,
                                   limit: int = 10) -> dict:
        """Produkte aus einem Shopify-Store abrufen.

        Args:
            connector_name: Name des Shopify-Connectors
            limit: Maximale Anzahl Produkte (Standard: 10, Max: 50)
        """
        limit = min(max(1, limit), 50)
        data = await _shopify_request(
            connector_name, "products", {"limit": limit}
        )
        if "error" in data:
            return data

        products = data.get("products", [])
        return {
            "connector": connector_name,
            "total_returned": len(products),
            "products": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "status": p.get("status", ""),
                    "vendor": p.get("vendor", ""),
                    "product_type": p.get("product_type", ""),
                    "variants_count": len(p.get("variants", [])),
                    "price_range": _price_range(p.get("variants", [])),
                    "created_at": p.get("created_at", ""),
                }
                for p in products
            ],
        }

    @mcp.tool()
    async def shopify_get_orders(connector_name: str,
                                 limit: int = 10,
                                 status: str = "any") -> dict:
        """Bestellungen aus einem Shopify-Store abrufen.

        Args:
            connector_name: Name des Shopify-Connectors
            limit: Maximale Anzahl Bestellungen (Standard: 10, Max: 50)
            status: Filter — "any", "open", "closed", "cancelled"
        """
        limit = min(max(1, limit), 50)
        data = await _shopify_request(
            connector_name, "orders",
            {"limit": limit, "status": status},
        )
        if "error" in data:
            return data

        orders = data.get("orders", [])
        return {
            "connector": connector_name,
            "total_returned": len(orders),
            "orders": [
                {
                    "id": o["id"],
                    "order_number": o.get("order_number", ""),
                    "financial_status": o.get("financial_status", ""),
                    "fulfillment_status": o.get("fulfillment_status"),
                    "total_price": o.get("total_price", ""),
                    "currency": o.get("currency", ""),
                    "line_items_count": len(o.get("line_items", [])),
                    "created_at": o.get("created_at", ""),
                }
                for o in orders
            ],
        }

    @mcp.tool()
    async def shopify_get_inventory(connector_name: str,
                                    limit: int = 10) -> dict:
        """Inventar-Levels aus einem Shopify-Store abrufen.

        Zeigt Lagerbestände für alle Produkt-Varianten.

        Args:
            connector_name: Name des Shopify-Connectors
            limit: Maximale Anzahl Produkte (Standard: 10, Max: 50)
        """
        limit = min(max(1, limit), 50)
        # Zuerst Produkte mit Varianten holen
        data = await _shopify_request(
            connector_name, "products", {"limit": limit}
        )
        if "error" in data:
            return data

        products = data.get("products", [])
        inventory = []
        for p in products:
            for v in p.get("variants", []):
                inventory.append({
                    "product_title": p["title"],
                    "variant_title": v.get("title", "Default"),
                    "sku": v.get("sku", ""),
                    "inventory_quantity": v.get("inventory_quantity", 0),
                    "price": v.get("price", ""),
                    "inventory_management": v.get("inventory_management"),
                })

        return {
            "connector": connector_name,
            "products_checked": len(products),
            "total_variants": len(inventory),
            "inventory": inventory,
        }


def _price_range(variants: list) -> str:
    """Preisspanne aus Varianten berechnen."""
    if not variants:
        return "N/A"
    prices = []
    for v in variants:
        try:
            prices.append(float(v.get("price", 0)))
        except (ValueError, TypeError):
            continue
    if not prices:
        return "N/A"
    low, high = min(prices), max(prices)
    if low == high:
        return f"${low:.2f}"
    return f"${low:.2f} - ${high:.2f}"
