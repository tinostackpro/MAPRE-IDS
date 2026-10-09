import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "settings.json"
DEFAULTS = {"trigger_process":"notepad.exe", "poll_interval_seconds":3, "screenshot_enabled":False,
            "screenshot_interval_seconds":10, "screenshot_retention_days":7, "screenshot_directory":"evidence/screenshots",
            "webcam_enabled":False, "webcam_directory":"evidence/webcam",
            "alert_connection_threshold":30, "alert_window_seconds":60}

def load_config():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    except (OSError, json.JSONDecodeError):
        return DEFAULTS.copy()

def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
