# Business Bridge MCP Server

MCP Server with pre-built connectors for common business platforms. Connect AI agents to Shopify, WordPress, Calendly and more.

## Features

- **Shopify** — Products, orders, inventory from any Shopify store
- **WordPress** — Posts, pages, comments via REST API
- **Calendly** — Event types, availability, scheduled events
- **Connector Management** — List, configure, and check connector status

## Installation

```bash
pip install business-bridge-mcp-server
```

## Usage with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "business-bridge": {
      "command": "uvx",
      "args": ["business-bridge-mcp-server"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_connectors` | Show all available business connectors |
| `get_connector_status` | Check if a connector is configured |
| `connect_shopify` | Connect a Shopify store |
| `shopify_get_products` | Get products from a Shopify store |
| `shopify_get_orders` | Get orders from a Shopify store |
| `shopify_get_inventory` | Get inventory levels from a Shopify store |
| `connect_wordpress` | Connect a WordPress site |
| `wordpress_get_posts` | Read posts from a WordPress site |
| `wordpress_get_pages` | Read pages from a WordPress site |
| `wordpress_get_comments` | Read comments from a WordPress site |
| `connect_calendly` | Connect a Calendly account |
| `calendly_get_event_types` | List Calendly event types |
| `calendly_check_availability` | Check availability in a time range |

## Data Storage

Connector configurations are stored locally in SQLite at `~/.business-bridge/connectors.db`.


---

## More MCP Servers by AiAgentKarl

| Category | Servers |
|----------|---------|
| 🔗 Blockchain | [Solana](https://github.com/AiAgentKarl/solana-mcp-server) |
| 🌍 Data | [Weather](https://github.com/AiAgentKarl/weather-mcp-server) · [Germany](https://github.com/AiAgentKarl/germany-mcp-server) · [Agriculture](https://github.com/AiAgentKarl/agriculture-mcp-server) · [Space](https://github.com/AiAgentKarl/space-mcp-server) · [Aviation](https://github.com/AiAgentKarl/aviation-mcp-server) · [EU Companies](https://github.com/AiAgentKarl/eu-company-mcp-server) |
| 🔒 Security | [Cybersecurity](https://github.com/AiAgentKarl/cybersecurity-mcp-server) · [Policy Gateway](https://github.com/AiAgentKarl/agent-policy-gateway-mcp) · [Audit Trail](https://github.com/AiAgentKarl/agent-audit-trail-mcp) |
| 🤖 Agent Infra | [Memory](https://github.com/AiAgentKarl/agent-memory-mcp-server) · [Directory](https://github.com/AiAgentKarl/agent-directory-mcp-server) · [Hub](https://github.com/AiAgentKarl/mcp-appstore-server) · [Reputation](https://github.com/AiAgentKarl/agent-reputation-mcp-server) |
| 🔬 Research | [Academic](https://github.com/AiAgentKarl/crossref-academic-mcp-server) · [LLM Benchmark](https://github.com/AiAgentKarl/llm-benchmark-mcp-server) · [Legal](https://github.com/AiAgentKarl/legal-court-mcp-server) |

[→ Full catalog (40+ servers)](https://github.com/AiAgentKarl)

## License

MIT
