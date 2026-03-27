# Garden Planner

A local-first, AI-native garden journal. Track every plant from seed to harvest by talking to your AI assistant — no manual UI required.

Built as a [Home Assistant](https://www.home-assistant.io/) add-on so your data lives on your own hardware and is included in your HA backups automatically.

## How it works

The app exposes an [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) API. You connect your AI assistant (e.g. Claude) to it and interact conversationally:

> *"I just planted cherry tomato seeds in bed 3"*
> *"My courgette got its first flower today"*
> *"How much did I harvest last season?"*

The assistant calls the right MCP tools behind the scenes — no forms, no UI.

## Features

- Full plant lifecycle tracking: seed/bulb/tuber/seedling → germination → transplant → first flower → harvest → end of season
- Multiple harvests per plant with quantity, unit, and quality
- Custom events (pest, disease, pruning, etc.)
- Season summaries and plant history
- SQLite database — simple, local, no dependencies

## Project structure

```
garden-planner/
├── mcp-server/              # Python MCP server (the core app)
│   ├── garden_planner/
│   │   ├── models.py        # SQLModel table definitions
│   │   ├── db.py            # Database engine and init
│   │   ├── queries.py       # All database logic
│   │   └── server.py        # MCP tools and entrypoint
│   ├── tests/               # Pytest test suite
│   └── pyproject.toml
│
└── ha-addon/                # Home Assistant add-on wrapper
    ├── config.yaml          # Add-on manifest
    ├── Dockerfile           # Built from repo root, pushed to GHCR
    └── README.md            # Install instructions + button
```

## Installing as a Home Assistant add-on

See [ha-addon/README.md](ha-addon/README.md) for the one-click install button and setup instructions.

## Running locally (development)

```bash
cd mcp-server
python -m venv .venv && source .venv/bin/activate
pip install -e .
garden-planner          # starts MCP server on http://localhost:8765/sse
```

Point your MCP client at `http://localhost:8765/sse`.

## Running tests

```bash
cd mcp-server
pip install -e ".[dev]"
pytest
```

## MCP tools

| Tool | Description |
|------|-------------|
| `add_planting_material` | Register a seed, bulb, tuber, seedling, etc. |
| `list_planting_materials` | List all registered materials |
| `log_planting` | Start tracking a new planting |
| `log_transplant` | Record a transplant to its final location |
| `log_event` | Log a lifecycle event (germination, first flower, etc.) |
| `log_harvest` | Record a harvest with quantity and quality |
| `end_planting` | Mark a planting as ended |
| `get_planting_history` | Full lifecycle timeline for a planting |
| `list_active_plantings` | All currently active plantings |
| `get_season_summary` | Season overview with totals |
| `search_plantings` | Search by plant name or location |

## License

MIT
