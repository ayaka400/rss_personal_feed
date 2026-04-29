import json
import logging
import os
import sys
from pathlib import Path

import feedparser
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent / "config.json"
STATE_FILE = Path(__file__).parent.parent / "state.json"
MAX_URLS_PER_USER = 50

State = dict[str, dict[str, list[str]]]


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        logger.warning("config.json not found — no users configured")
        return {"services": []}
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)  # 設定ファイルをpythonの辞書型に変換して返す
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load config.json: %s", e)
        return {"services": []}


def load_state() -> State:
    if not STATE_FILE.exists():
        return {"qiita": {}, "zenn": {}}
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)  # 状態ファイルをpythonの辞書型に変換して返す
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load state.json: %s", e)
        return {"qiita": {}, "zenn": {}}


def save_state(state: State) -> None:
    try:
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)  # 状態をjson形式で保存する
    except OSError as e:
        logger.error("Failed to save state.json: %s", e)


def fetch_urls(feed_url: str) -> list[str]:
    try:
        feed = feedparser.parse(feed_url)
        return [e.get("link", "") for e in feed.entries if e.get("link")]
    except Exception as e:
        logger.error("Error fetching feed %s: %s", feed_url, e)
        return []


def notify(service: str, url: str) -> bool:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.error("SLACK_WEBHOOK_URL is not set")
        return False
    try:
        text = f"{service}に新着記事があります\n{url}"
        response = requests.post(webhook_url, json={"text": text}, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Failed to send Slack notification: %s", e)
        return False


def process(service_key: str, service_label: str, feed_url: str,
            username: str, state: State) -> None:
    urls = fetch_urls(feed_url)
    known = state.setdefault(service_key, {}).setdefault(username, [])

    if not known:
        logger.info("First run for %s/%s — saving without notification", service_key, username)
        known.extend(urls)
        return

    for url in urls:
        if url in known:
            continue
        if notify(service_label, url):
            known.append(url)
            if len(known) > MAX_URLS_PER_USER:
                state[service_key][username] = known[-MAX_URLS_PER_USER:]


def main() -> None:
    config = load_config()
    state = load_state()

    for service in config.get("services", []):
        for username in service.get("usernames", []):
            feed_url = service["feed_url"].format(username=username)
            process(service["key"], service["label"], feed_url, username, state)

    save_state(state)


if __name__ == "__main__":
    main()
