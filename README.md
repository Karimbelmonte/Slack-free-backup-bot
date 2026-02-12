# Slack-free-backup-bot

Lightweight, incremental Slack backup tool that stores conversations, files, and readable Markdown archives locally.

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
   - Saves raw data
   - Downloads files
   - Regenerates Markdown output
4. A cron job runs the script automatically.

---

## Step 1 — Create a Slack App

Go to:

https://api.slack.com/apps

Click **Create New App → From scratch**

Add the following **Bot Token Scopes** under:

**OAuth & Permissions → Bot Token Scopes**

<img width="664" height="757" alt="Captura desde 2026-02-12 13-08-02" src="https://github.com/user-attachments/assets/a0dd73f6-c2f8-42c8-b4c4-f0ed44921980" />


Then:

- Click **Install App**
- Copy the **Bot User OAuth Token (xoxb-...)**

---

## Step 2 — Invite the Bot to Channels

In Slack, for each channel you want to back up:

`/invite @your-bot-name`


Only channels where the bot is a member will be archived.

---

## Step 3 — Installation

### Clone the Repository

```bash
git clone https://github.com/yourname/slack-local-backup.git
cd slack-local-backup
---

### Linux / macOS Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


