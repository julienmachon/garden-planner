# Garden Planner

A local-first garden journal with an MCP API for conversational logging and querying via Claude (or any MCP-compatible client).

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `port` | `8765`  | Port the MCP API listens on |

## MCP Tools

| Tool | Description |
|------|-------------|
| `add_planting_material` | Register a seed, bulb, tuber, seedling, etc. |
| `list_planting_materials` | List all registered materials |
| `log_planting` | Start tracking a new planting |
| `log_transplant` | Record a transplant to final location |
| `log_event` | Log a lifecycle event (germination, first flower, etc.) |
| `log_harvest` | Record a harvest |
| `end_planting` | Mark a planting as ended |
| `get_planting_history` | Full lifecycle timeline for a planting |
| `list_active_plantings` | All currently active plantings |
| `get_season_summary` | Season overview with totals |
| `search_plantings` | Search by plant name or location |

## Data

All data is stored in `/data/garden.db` (SQLite) and is included in Home Assistant backups automatically.

## Connecting Claude

Add the following to your Claude MCP configuration:

```json
{
  "mcpServers": {
    "garden-planner": {
      "url": "http://homeassistant.local:8765/sse"
    }
  }
}
```
