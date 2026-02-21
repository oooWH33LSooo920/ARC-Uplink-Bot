# ARC Uplink Bot

A fully automated Discord bot for **ARC Raiders** communities. ARC Uplink tracks live events, weekly trials, expeditions, and quests — all through clean slash commands. No dashboard needed.

---

## ✨ Features

| Feature | Command | Auto-Post |
|---|---|---|
| Weekly Trials | `/trials` | ✅ Weekly (on reset) |
| Live Events | `/liveevents` | ✅ On new event |
| Expeditions | `/expedition`, `/expeditions` | ✅ On new expedition |
| Quest Lookup | `/quest <name>`, `/quest_list` | — |

**Admin setup commands** (require Administrator permission):
- `/setweeklytrials <channel>` — set auto-post channel for weekly trials
- `/setliveevents <channel>` — set auto-post channel for live event alerts
- `/setexpedition <channel>` — set auto-post channel for expedition updates

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/oooWH33LSooo920/ARC-Uplink-Bot.git
cd ARC-Uplink-Bot
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Bot Token

```bash
cp .env.example .env
```

Edit `.env` and replace `your_discord_bot_token_here` with your actual Discord bot token:

```
DISCORD_TOKEN=your_discord_bot_token_here
```

> 🔐 **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 5. Start the Bot

```bash
python bot.py
```

If everything is set up correctly, the bot will come online and sync its slash commands.

---

## 🔗 Invite the Bot

Use the [Discord Developer Portal](https://discord.com/developers/applications) to create an OAuth2 invite link with the following scopes:

- `bot`
- `applications.commands`

### Required Bot Permissions

| Permission | Reason |
|---|---|
| Send Messages | Post updates and replies |
| Embed Links | Rich embeds for game data |
| Read Message History | Context for thread responses |
| Use Application Commands | Slash command support |

---

## 🗂️ Project Structure

```
ARC-Uplink-Bot/
├── bot.py               # Main entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment config
├── .gitignore
├── LICENSE
├── cogs/
│   ├── trials.py        # Weekly trials commands + auto-post
│   ├── events.py        # Live events commands + auto-post
│   ├── expeditions.py   # Expeditions commands + auto-post
│   └── quests.py        # Quest lookup commands
└── data/
    ├── quests.json          # Local quest data (fallback)
    ├── expeditions.json     # Local expedition data (fallback)
    └── guild_settings.json  # Auto-generated guild configuration
```

---

## 📡 Data Sources

ARC Uplink fetches live game data from the [MetaForge ARC Raiders API](https://metaforge.app/arc-raiders/api). If the API is unavailable, the bot falls back to the local JSON files in the `data/` directory.

---

## 🛠️ Running as a Service (Optional)

### systemd (Linux VPS)

```ini
[Unit]
Description=ARC Uplink Discord Bot
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/ARC-Uplink-Bot
ExecStart=/home/YOUR_USER/ARC-Uplink-Bot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable arc-uplink
sudo systemctl start arc-uplink
```

---

## 📄 License

Licensed under the [MIT License](LICENSE). Free to use, modify, and distribute with attribution.

---

*ARC Uplink is a community project and is not affiliated with or endorsed by Embark Studios AB.*
