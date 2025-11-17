# -- coding: utf-8 --
"""
core/data_pipe.py
-----------------
Multi-Sink Telemetry تتحكّم فيها عبر data/app_config.json:
{
  "app_version": "exp-0.3",
  "sinks": {
    "disk":   {"enabled": true,  "path": "./data/events.jsonl"},
    "webhook":{"enabled": false, "url": "https://hooks.zapier.com/..."},
    "gsheets":{"enabled": false, "sheet_id":"...", "service_account_json":"{...} أو مسار"}
  }
}
"""

from __future__ import annotations
import os, json, uuid, pathlib, datetime, logging
from typing import Any, Dict, Optional, List

from apps.app_config import get_config

UTC = datetime.timezone.utc


class BaseSink:
    name = "base"
    def send(self, event: Dict[str, Any]) -> bool:
        raise NotImplementedError


class DiskSink(BaseSink):
    name = "disk"

    def __init__(self, path: str = "./data/events.jsonl"):
        self.path = path
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

    def send(self, event: Dict[str, Any]) -> bool:
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            logging.warning(f"DiskSink failed: {e}")
            return False


class WebhookSink(BaseSink):
    name = "webhook"

    def __init__(self, url: str):
        self.url = url
        try:
            import requests  # noqa: F401
            self._ok = True
        except Exception:
            self._ok = False

    def send(self, event: Dict[str, Any]) -> bool:
        if not self._ok:
            return False
        try:
            import requests
            r = requests.post(self.url, json=event, timeout=8)
            return 200 <= r.status_code < 300
        except Exception as e:
            logging.warning(f"WebhookSink failed: {e}")
            return False


class GSheetsSink(BaseSink):
    name = "gsheets"

    def __init__(self, sheet_id: str, svc_json: Optional[str]):
        self.sheet_id = sheet_id
        self._ready = False
        try:
            import gspread  # noqa: F401
            from google.oauth2.service_account import Credentials

            if not svc_json:
                return

            # svc_json: JSON string أو مسار لملف JSON
            if isinstance(svc_json, str) and svc_json.strip().startswith("{"):
                creds_dict = json.loads(svc_json)
            else:
                with open(svc_json, "r", encoding="utf-8") as f:
                    creds_dict = json.load(f)

            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            import gspread
            self.gc = gspread.authorize(creds)
            self._ready = True
        except Exception as e:
            logging.warning(f"GSheets init failed: {e}")
            self._ready = False

    def _ensure_ws(self):
        sh = self.gc.open_by_key(self.sheet_id)
        try:
            ws = sh.worksheet("events")
        except Exception:
            ws = sh.add_worksheet(title="events", rows=1000, cols=20)
            ws.append_row([
                "ts_utc", "event_type", "user_id", "session_id",
                "lang", "model", "app_version", "payload_json"
            ])
        return ws

    def send(self, event: Dict[str, Any]) -> bool:
        if not self._ready:
            return False
        try:
            ws = self._ensure_ws()
            ws.append_row([
                event.get("ts_utc", ""),
                event.get("event_type", ""),
                event.get("user_id", ""),
                event.get("session_id", ""),
                event.get("lang", ""),
                event.get("model", ""),
                event.get("app_version", ""),
                json.dumps(event.get("payload", {}), ensure_ascii=False)
            ], value_input_option="RAW")
            return True
        except Exception as e:
            logging.warning(f"GSheets send failed: {e}")
            return False


class DataPipe:
    def __init__(self):
        self.sinks: List[BaseSink] = []
        self.app_version = "dev"
        self._build_sinks()

    def _build_sinks(self):
        cfg = get_config()
        self.app_version = cfg.get("app_version", "dev")
        sinks_cfg = cfg.get("sinks") or {}
        self.sinks = []

        # ترتيب: Sheets → Webhook → Disk
        g = sinks_cfg.get("gsheets", {})
        if g.get("enabled"):
            self.sinks.append(GSheetsSink(g.get("sheet_id", ""), g.get("service_account_json")))

        w = sinks_cfg.get("webhook", {})
        if w.get("enabled") and w.get("url"):
            self.sinks.append(WebhookSink(w["url"]))

        d = sinks_cfg.get("disk", {"enabled": True, "path": "./data/events.jsonl"})
        if d.get("enabled", True):
            self.sinks.append(DiskSink(d.get("path", "./data/events.jsonl")))

    def send(self, event_type: str, payload: Dict[str, Any],
             user_id: str = "anon", session_id: Optional[str] = None,
             lang: str = "العربية", model: str = "") -> bool:
        cfg = get_config()  # لو الإعدادات تغيرت أثناء التشغيل
        if not self.sinks:
            self._build_sinks()
        evt = {
            "ts_utc": datetime.datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "user_id": str(user_id or "anon"),
            "session_id": session_id or f"ss-{uuid.uuid4().hex[:10]}",
            "lang": lang,
            "model": model or (cfg.get("llm") or {}).get("model", ""),
            "app_version": cfg.get("app_version", "dev"),
            "payload": payload
        }
        ok = False
        for s in self.sinks:
            try:
                ok = s.send(evt) or ok
            except Exception as e:
                logging.warning(f"Sink {s.name} error: {e}")
        return ok


# Singleton
_PIPE: Optional[DataPipe] = None

def get_pipe() -> DataPipe:
    global _PIPE
    if _PIPE is None:
        _PIPE = DataPipe()
    return _PIPE
