[Python 3.10+] [MIT License] [Linux | macOS | Windows]

# Slack Free Backup Bot

Lightweight, incremental Slack backup tool that stores conversations, files, and readable Markdown archives locally.

---

## Quick Start

1. Create a Slack App and generate a Bot Token.
2. Invite the bot to the channels you want to archive.
3. Clone this repository.
4. Set your `SLACK_BOT_TOKEN`.
5. Run `backup_slack.py`.

That’s it.

---

## Features

- Incremental backup (only downloads new messages)
- Supports public and private channels
- Downloads shared files and images
- Converts Slack IDs into real user names
- Generates human-readable Markdown archives
- Cross-platform (Linux, macOS, Windows)
- Cron / Scheduler automation
- Works with Slack Free plan (within its limits)

---

## How It Works

1. A Slack App (bot) is created.
2. The bot is invited to the channels you want to back up.
3. The script:
   - Fetches new messages incrementally
   - Saves raw data (`.jsonl`)
   - Downloads shared files
   - Regenerates Markdown output
4. A scheduler (cron / launchd / Task Scheduler) runs the script automatically.

---

## Step 1 — Create a Slack App

Go to:

https://api.slack.com/apps

Click **Create New App → From scratch**

Add the following **Bot Token Scopes** under:

**OAuth & Permissions → Bot Token Scopes**

```
channels:read
channels:history
groups:read
groups:history
users:read
files:read
```

Then:

- Click **Install App**
- Copy the **Bot User OAuth Token** (`xoxb-...`)

---

## Step 2 — Invite the Bot to Channels

In Slack, for each channel you want to back up:

```
/invite @your-bot-name
```

Only channels where the bot is a member will be archived.

---

## Step 3 — Installation

### Clone the Repository

```bash
git clone https://github.com/Karimbelmonte/Slack-free-backup-bot.git
cd Slack-free-backup-bot
```

---

### Linux / macOS Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Windows Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 4 — Configure Environment

Create a `.env` file in the root directory of the repository:

```bash
SLACK_BOT_TOKEN="xoxb-your-token-here"
```

---

## Step 5 — Run Manually

### Linux / macOS

```bash
set -a
source .env
set +a
python backup_slack.py
```

### Windows (PowerShell)

```powershell
$env:SLACK_BOT_TOKEN="xoxb-your-token-here"
python backup_slack.py
```

---

## Output Structure

After running, the following directory structure will be created:

```
slack_backup/
├── data/      # Raw JSONL messages
├── md/        # Human-readable Markdown archives
├── files/     # Downloaded attachments
├── state.json
└── users.json
```

---

## Automation (Cross-Platform)

### Linux (cron)

```bash
crontab -e
```

Add:

```
0 * * * * cd /path/to/repo && . ./.env && ./venv/bin/python backup_slack.py >> ~/slack_backup/cron.log 2>&1
```

Runs every hour.

---

### macOS (launchd)

Create:

```
~/Library/LaunchAgents/com.slackbackup.plist
```

Then load:

```bash
launchctl load ~/Library/LaunchAgents/com.slackbackup.plist
```

---

### Windows (Task Scheduler)

1. Open **Task Scheduler**
2. Create **Basic Task**
3. Set Trigger → Repeat every 1 hour
4. Choose Action → Start a Program

**Program:**

```
C:\Path\To\repo\venv\Scripts\python.exe
```

**Start in:**

```
C:\Path\To\repo\
```

---

## Limitations

- Only channels where the bot is invited are backed up.
- Direct Messages (1:1) are not supported.
- Slack Free plan may limit accessible message history.
- Deleted Slack messages are not removed locally.
- Thread replies are stored as normal messages (no thread hierarchy reconstruction).

---

## Security Notes

- The Slack bot token grants read access to channels where it is invited.
- Store the token securely.
- Never commit `.env` to version control.

---

## Troubleshooting

### `missing_scope`

A required permission was not added → reinstall the Slack app.

### `not_in_channel`

The bot is not invited to that channel.

### `rate_limited`

Slack rate limit reached → reduce execution frequency.
