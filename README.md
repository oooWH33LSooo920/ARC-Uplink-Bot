# ARC Uplink Bot

A Discord bot that acts as an uplink relay, keeping your server informed with the latest updates and announcements.

## Features

- **Ping / Latency check** — `!ping` or `/ping`
- **Bot info** — `!info` or `/info`
- **Uplink feed polling** — automatically posts new entries from a configured JSON feed to a designated channel every 5 minutes
- **Uplink status** — `!uplink` or `/uplink` (requires Manage Guild permission)

## Requirements

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/oooWH33LSooo920/ARC-Uplink-Bot.git
   cd ARC-Uplink-Bot
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your values:

   | Variable            | Required | Description                                            |
   |---------------------|----------|--------------------------------------------------------|
   | `DISCORD_TOKEN`     | ✅        | Your Discord bot token                                 |
   | `UPLINK_CHANNEL_ID` | Optional | Channel ID where feed updates are posted               |
   | `UPLINK_FEED_URL`   | Optional | URL of the JSON feed to poll (see Feed Format below)   |

4. **Run the bot**

   ```bash
   python bot.py
   ```

## Feed Format

The uplink poller expects the feed URL to return JSON in one of two shapes:

```json
[
  { "id": "unique-id", "title": "Entry Title", "url": "https://...", "description": "..." }
]
```

or

```json
{
  "entries": [
    { "id": "unique-id", "title": "Entry Title", "url": "https://...", "description": "..." }
  ]
}
```

Only entries with a new `id` that haven't been seen before will be posted.

## Project Structure

```
ARC-Uplink-Bot/
├── bot.py              # Bot entry point
├── cogs/
│   ├── general.py      # General commands (ping, info)
│   └── uplink.py       # Uplink feed polling and commands
├── .env.example        # Example environment file
├── requirements.txt    # Python dependencies
└── LICENSE
```

## License

MIT — see [LICENSE](LICENSE).
