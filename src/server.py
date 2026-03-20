"""Business Bridge MCP Server — Verbindet AI-Agents mit Business-Plattformen."""

from mcp.server.fastmcp import FastMCP

from src.tools.connectors import register_connector_tools
from src.tools.shopify import register_shopify_tools
from src.tools.wordpress import register_wordpress_tools
from src.tools.calendly import register_calendly_tools

mcp = FastMCP(
    "Business Bridge MCP Server",
    instructions=(
        "Pre-built connectors for common business platforms. "
        "Connect to Shopify, WordPress, Calendly and more. "
        "Configure connectors once, then query data across platforms."
    ),
)

# Alle Tools registrieren
register_connector_tools(mcp)
register_shopify_tools(mcp)
register_wordpress_tools(mcp)
register_calendly_tools(mcp)


def main():
    """Server starten."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
