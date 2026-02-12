#!/usr/bin/env python3
import os
import json
import time
import re
from pathlib import Path
from datetime import datetime
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Paths
BASE = Path.home() / "slack_backup"
DATA_DIR = BASE / "data"
MD_DIR = BASE / "md"
FILES_DIR = BASE / "files"
STATE_FILE = BASE / "state.json"
USERS_FILE = BASE / "users.json"

# Tuning
SLEEP_BETWEEN_CALLS_SEC = 0.35
REQUEST_TIMEOUT_SEC = 90

# Slack formatting regex
MENTION_RE = re.compile(r"<@([A-Z0-9]+)>")
CHANNEL_REF_RE = re.compile(r"<#([A-Z0-9]+)\|([^>]+)>")
LINK_RE = re.compile(r"<(https?://[^>|]+)\|([^>]+)>")
BARE_LINK_RE = re.compile(r"<(https?://[^>]+)>")

SKIP_SUBTYPES = {"channel_join", "channel_leave"}

def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def safe_name(name: str) -> str:
    name = name.strip()
    cleaned = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return cleaned.strip("_") or "channel"

def ts_to_dt(ts: str) -> datetime:
    return datetime.fromtimestamp(float(ts))

def paginate(client_call, **kwargs):
    cursor = None
    while True:
        resp = client_call(cursor=cursor, **kwargs) if cursor else client_call(**kwargs)
        yield resp
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break

def fetch_users_map(client: WebClient) -> dict:
    """
    Needs users:read. Returns user_id -> display_name (fallback to real name / username).
    """
    users = {}
    for resp in paginate(client.users_list, limit=200):
        for m in resp.get("members", []):
            uid = m.get("id")
            if not uid:
                continue
            profile = m.get("profile", {}) or {}
            display = (profile.get("display_name") or "").strip()
            real = (profile.get("real_name") or "").strip()
            uname = (m.get("name") or "").strip()
            users[uid] = display or real or uname or uid
    return users

def fetch_member_channels(client: WebClient):
    chans = []
    for resp in paginate(
        client.conversations_list,
        types="public_channel,private_channel",
        limit=200
    ):
        for ch in resp.get("channels", []):
            if ch.get("is_member"):
                chans.append(ch)
    return chans

def fetch_new_messages(client: WebClient, channel_id: str, oldest: str):
    msgs = []
    for resp in paginate(
        client.conversations_history,
        channel=channel_id,
        oldest=oldest,
        inclusive=False,
        limit=200
    ):
        msgs.extend(resp.get("messages", []))
    msgs.reverse()  # chronological
    return msgs

def append_jsonl(path: Path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def clean_slack_text(text: str, users_map: dict) -> str:
    if not text:
        return ""

    # <@U123> -> @Name
    text = MENTION_RE.sub(lambda m: "@" + users_map.get(m.group(1), m.group(1)), text)

    # <#C123|channel> -> #channel
    text = CHANNEL_REF_RE.sub(lambda m: "#" + m.group(2), text)

    # <url|label> -> label (url)
    text = LINK_RE.sub(lambda m: f"{m.group(2)} ({m.group(1)})", text)

    # <url> -> url
    text = BARE_LINK_RE.sub(lambda m: m.group(1), text)

    # Special mentions
    text = text.replace("<!channel>", "@channel").replace("<!here>", "@here").replace("<!everyone>", "@everyone")

    return text

def sender_name(msg: dict, users_map: dict) -> str:
    uid = msg.get("user")
    if uid:
        return users_map.get(uid, uid)
    if msg.get("username"):
        return msg["username"]
    if msg.get("bot_id"):
        return f"bot:{msg['bot_id']}"
    return "unknown"

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def download_file(file_obj: dict, channel_safe: str, token: str):
    """
    Downloads Slack file using url_private_download/url_private.
    Needs files:read.
    """
    url = file_obj.get("url_private_download") or file_obj.get("url_private")
    if not url:
        return None

    file_id = file_obj.get("id", "file")
    orig_name = file_obj.get("name") or file_obj.get("title") or file_id
    out_dir = FILES_DIR / channel_safe
    ensure_dir(out_dir)

    out_path = out_dir / f"{file_id}__{safe_name(orig_name)}"

    # Avoid redownload
    if out_path.exists() and out_path.stat().st_size > 0:
        return str(out_path)

    # Download
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
        timeout=REQUEST_TIMEOUT_SEC,
    )
    r.raise_for_status()

    with out_path.open("wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)

    return str(out_path)

def render_markdown(channel_safe: str, users_map: dict):
    """
    Reads the full jsonl for a channel and writes a grouped-by-day Markdown.
    Includes file links if present.
    """
    jsonl_path = DATA_DIR / f"{channel_safe}.jsonl"
    md_path = MD_DIR / f"{channel_safe}.md"

    if not jsonl_path.exists():
        return

    # Load and sort
    messages = []
    with jsonl_path.open("r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = m.get("ts")
            if not ts:
                continue
            messages.append(m)

    messages.sort(key=lambda m: float(m["ts"]))

    ensure_dir(MD_DIR)
    with md_path.open("w", encoding="utf-8") as out:
        out.write(f"# {channel_safe}\n")

        current_day = None
        for m in messages:
            if m.get("subtype") in SKIP_SUBTYPES:
                continue

            dt = ts_to_dt(m["ts"])
            day = dt.strftime("%Y-%m-%d")
            if day != current_day:
                current_day = day
                out.write(f"\n## {current_day}\n\n")

            t = dt.strftime("%H:%M")
            who = sender_name(m, users_map)
            text = clean_slack_text(m.get("text", ""), users_map).strip()
            if not text:
                text = "(sin texto)"

            # Attachments / files
            file_lines = []
            for fobj in (m.get("files") or []):
                title = fobj.get("title") or fobj.get("name") or fobj.get("id", "file")
                mimetype = fobj.get("mimetype") or ""
                url_public = fobj.get("permalink") or fobj.get("url_private")
                if url_public:
                    file_lines.append(f"    - 📎 {title} [{mimetype}] — {url_public}")
                else:
                    file_lines.append(f"    - 📎 {title} [{mimetype}]")

            out.write(f"- **{t}** · **{who}**: {text}\n")
            if file_lines:
                out.write("\n".join(file_lines) + "\n")

def main():
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise SystemExit("Falta SLACK_BOT_TOKEN (export SLACK_BOT_TOKEN='xoxb-...').")

    client = WebClient(token=token)

    ensure_dir(DATA_DIR)
    ensure_dir(MD_DIR)
    ensure_dir(FILES_DIR)

    state = load_json(STATE_FILE, {"channels": {}})
    users_map = load_json(USERS_FILE, {})

    # Update users map if permitted
    try:
        users_map = fetch_users_map(client)
        save_json(USERS_FILE, users_map)
    except SlackApiError:
        # If missing_scope users:read, keep IDs
        pass

    channels = fetch_member_channels(client)
    changed = []

    for ch in channels:
        ch_id = ch["id"]
        ch_safe = safe_name(ch.get("name", ch_id))
        oldest = state["channels"].get(ch_id, "0")

        try:
            new_msgs = fetch_new_messages(client, ch_id, oldest)
        except SlackApiError as e:
            # If rate limited, Slack SDK raises SlackApiError with response headers sometimes.
            # We'll just skip and continue.
            time.sleep(SLEEP_BETWEEN_CALLS_SEC)
            continue

        if new_msgs:
            # Append new messages to jsonl
            jsonl_path = DATA_DIR / f"{ch_safe}.jsonl"
            append_jsonl(jsonl_path, new_msgs)
            state["channels"][ch_id] = new_msgs[-1]["ts"]
            changed.append(ch_safe)

            # Download files from new messages (if scope files:read exists)
            for m in new_msgs:
                for fobj in (m.get("files") or []):
                    try:
                        download_file(fobj, ch_safe, token)
                    except Exception:
                        # If missing_scope or download fails, ignore
                        pass

        time.sleep(SLEEP_BETWEEN_CALLS_SEC)

    save_json(STATE_FILE, state)

    # Regenerate markdown only for channels that changed
    for ch_safe in changed:
        render_markdown(ch_safe, users_map)

    print(f"✔ Backup completado. Canales actualizados: {len(changed)}")
    if changed:
        print("  - " + "\n  - ".join(changed))

if __name__ == "__main__":
    main()
