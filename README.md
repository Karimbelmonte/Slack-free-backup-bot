# Slack Free Backup Bot

![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

Lightweight, incremental Slack backup tool that stores conversations, files, and readable Markdown archives locally.

---

## Overview

Slack Free plans provide limited export capabilities.  
This tool allows you to maintain a structured, incremental local archive of:

- Messages
- Files
- Images
- Human-readable Markdown archives

Backups are incremental — only new messages are downloaded on each run.

---

## Features

- Incremental backup (downloads only new messages)
- Supports public and private channels
- Downloads shared files and images
- Converts Slack IDs into real user names
- Generates readable Markdown archives
- Cross-platform (Linux, macOS, Windows)
- Automation via cron / launchd / Task Scheduler
- Compatible with Slack Free plan (within its limits)

---

## How It Works

1. A Slack App (bot) is created.
2. The bot is invited to channels you want to archive.
3. The script:
   - Tracks the last downloaded timestamp
   - Fetches only new messages
   - Stores raw JSON data
   - Downloads attachments
   - Regenerates Markdown output
4. A scheduler can automate periodic backups.

---

# Step 1 — Create a Slack App

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

# Step 2 — Invite the Bot to Channels

In Slack, for each channel you want to back up:

```
/invite @your-bot-name
```

Only channels where the bot is a member will be archived.

---

# Installation

---

# Linux / macOS

## 1. Clone the repository

```bash
git clone https://github.com/Karimbelmonte/Slack-free-backup-bot.git
cd Slack-free-backup-bot
```

## 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment

Create a `.env` file in the root directory:

```
SLACK_BOT_TOKEN=xoxb-your-token-here
```

⚠ Never commit this file to version control.

## 5. Run manually

```bash
set -a
source .env
set +a
python backup_slack.py
```

---

## Where Backups Are Stored (Linux/macOS)

Backups are saved in:

```
~/slack_backup
```

Example:

```
/home/youruser/slack_backup
```

---

# Windows (PowerShell)

## 1. Clone the repository

```powershell
git clone https://github.com/Karimbelmonte/Slack-free-backup-bot.git
cd Slack-free-backup-bot
```

If Git is not installed, download the repository as a ZIP from GitHub.

---

## 2. Create virtual environment

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again.

---

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Configure environment

### Option A (recommended for automation)

Create a `.env` file in the root directory:

```
SLACK_BOT_TOKEN=xoxb-your-token-here
```

### Option B (manual run only)

Set the variable in PowerShell:

```powershell
$env:SLACK_BOT_TOKEN="xoxb-your-token-here"
```

---

## 5. Run manually

```powershell
python backup_slack.py
```

---

## Where Backups Are Stored (Windows)

Backups are saved in:

```
C:\Users\YourUsername\slack_backup
```

Example:

```
C:\Users\aleja\slack_backup
```

---

# Output Structure

```
slack_backup/
├── data/      # Raw JSONL messages
├── md/        # Human-readable Markdown archives
├── files/     # Downloaded attachments
├── state.json
└── users.json
```

---

# Automation

---

## Linux (cron)

```bash
crontab -e
```

Add:

```
0 * * * * cd /path/to/repo && . ./.env && ./venv/bin/python backup_slack.py >> ~/slack_backup/cron.log 2>&1
```

Runs every hour.

---

## macOS (launchd)

Create:

```
~/Library/LaunchAgents/com.slackbackup.plist
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.slackbackup.plist
```

---

## Windows (Task Scheduler)

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Trigger → Daily
4. Repeat task every → 1 hour
5. Action → Start a Program

**Program/script:**

```
C:\Path\To\repo\venv\Scripts\python.exe
```

**Add arguments:**

```
backup_slack.py
```

**Start in:**

```
C:\Path\To\repo
```

Important:  
Task Scheduler does not inherit PowerShell environment variables.  
Use a `.env` file for automated runs.

---

# Limitations

- Only channels where the bot is invited are backed up.
- Direct Messages (1:1) are not supported.
- Slack Free plan may limit accessible message history.
- Deleted Slack messages are not removed locally.
- Thread replies are stored as normal messages (no thread hierarchy reconstruction).

---

# Security Notes

- The Slack bot token grants read access to channels where it is invited.
- Store the token securely.
- Never commit `.env` to version control.

---

# Troubleshooting

### `invalid_auth`

The token is incorrect or not loaded.

### `missing_scope`

Required permission was not added → reinstall the Slack app.

### `not_in_channel`

The bot is not invited to the channel.

### `rate_limited`

Slack rate limit reached → reduce execution frequency.
