# BREW — BREW Regularly Entangles Wires

Self-hosted REST API and MCP server for [Fellow Aiden](https://fellowproducts.com/products/aiden) coffee machines. Control your brewer through HTTP endpoints or natural language via [Claude](https://claude.ai) and other MCP clients.

Built with FastAPI, powered by the [fellow-aiden](https://github.com/9b/fellow-aiden) Python library.

## Features

- **REST API** -- full control over device settings, brew profiles, and schedules
- **MCP Server** -- expose your coffee machine to LLMs via the [Model Context Protocol](https://modelcontextprotocol.io)
- **Profile Management** -- create, update, delete, and share brew profiles
- **Schedule Management** -- set up one-time or recurring brews on specific days and times

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/Leolebleis/brew.git
cd brew
cp .env.example .env
```

Edit `.env` with your Fellow account credentials:

```
FELLOW_FELLOW_EMAIL=your@email.com
FELLOW_FELLOW_PASSWORD=your-password
FELLOW_API_KEY=optional-api-key-for-auth
FELLOW_MCP_ENABLED=true
```

### 2. Run with Docker

```bash
docker compose up -d --build
```

The API is now available at `http://localhost:8000`.

### 3. Or run locally

```bash
uv sync
uv run uvicorn brew.main:app --port 8000
```

## Configuration

| Variable | Required | Description |
|---|---|---|
| `FELLOW_FELLOW_EMAIL` | Yes | Fellow account email |
| `FELLOW_FELLOW_PASSWORD` | Yes | Fellow account password |
| `FELLOW_API_KEY` | No | API key for request authentication. If unset, all requests are allowed. |
| `FELLOW_MCP_ENABLED` | No | Set to `true` to enable the MCP server at `/mcp`. Default: `false`. |

## Endpoints

| Path | Description |
|---|---|
| `GET /device` | Device info and settings |
| `GET /profiles` | All brew profiles |
| `POST /profiles` | Create a profile |
| `GET /schedules` | All schedules |
| `POST /schedules` | Create a schedule |
| `GET /mcp/` | MCP server (when enabled) |
| `GET /health` | Health check |

Once running, visit `http://localhost:8000/docs` for the full interactive Swagger UI.

## Error format

All errors use a consistent envelope:

```json
{
  "error": {
    "code": "not_found",
    "message": "Profile 123 not found",
    "context": {}
  }
}
```

## MCP Server

When `FELLOW_MCP_ENABLED=true`, an MCP endpoint is available at `/mcp/` using Streamable HTTP transport.

### Resources (read-only context)

| URI | Description |
|---|---|
| `coffee://device` | Machine info -- brewer ID, name, firmware |
| `coffee://profiles` | All brew profiles |
| `coffee://profiles/{id}` | Single profile by ID |
| `coffee://schedules` | All scheduled brews |

### Tools

| Tool | Description |
|---|---|
| `update_device_setting` | Change device settings (name, volume, etc.) |
| `create_profile` | Create a profile from scratch or import from a shared link |
| `update_profile` | Update fields on an existing profile |
| `delete_profile` | Delete a profile |
| `generate_profile_link` | Get a shareable URL for a profile |
| `create_schedule` | Schedule a one-time or recurring brew |
| `update_schedule` | Update an existing schedule |
| `delete_schedule` | Delete a schedule |

### Client Configuration

Add to your `.mcp.json` or Claude Code config:

```json
{
  "mcpServers": {
    "brew": {
      "type": "http",
      "url": "https://your-host/mcp/",
      "headers": {
        "X-API-Key": "${FELLOW_API_KEY}"
      }
    }
  }
}
```

## Development

```bash
uv sync                          # install dependencies
uv run pytest -v                 # run tests
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run ty check src/             # type check
```

## Notes

- The Fellow cloud API is the only way to communicate with Aiden machines -- there is no local/LAN API
- JWT tokens expire every ~15 minutes; the `fellow-aiden` library handles re-authentication automatically
- `fellow-aiden` is installed from GitHub (not PyPI) due to a [known bug](https://github.com/9b/fellow-aiden/pull/20) in the published version
- The Aiden connects via 2.4 GHz WiFi only

## License

MIT
