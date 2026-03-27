# Garden Planner

A local-first, AI-native garden journal. Track every plant from seed to harvest via a conversational MCP API.

## Installation

**Step 1** — Add this repository to your Home Assistant add-on store:

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fjulienmachon%2Fgarden-planner)

**Step 2** — Find "Garden Planner" in the add-on store and click Install.

**Step 3** — Start the add-on and point your MCP client at it:

```json
{
  "mcpServers": {
    "garden-planner": {
      "url": "http://homeassistant.local:8765/sse"
    }
  }
}
```

## Data & Backups

All data is stored in `/data/garden.db` (SQLite) and is automatically included in your Home Assistant backups.
