# ─────────────────────────────────────────────
# ARI v2.1 — anchors.py
# ─────────────────────────────────────────────

import time
from datetime import datetime

import psutil


def get_anchors() -> dict:
    """
    Реальний стан зовнішнього світу.
    Це "тіло" ARI — обмеженість ресурсів у реальному часі.
    Без цього система флотує у вакуумі.
    """
    now = datetime.now()
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    mem = psutil.virtual_memory()

    return {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": now.strftime("%A"),
        "hour": now.hour,
        "cpu_percent": psutil.cpu_percent(interval=0.3),
        "ram_percent": mem.percent,
        "ram_used_gb": round(mem.used / 1e9, 2),
        "ram_available_gb": round(mem.available / 1e9, 2),
        "uptime_hours": round(uptime_seconds / 3600, 1),
    }


def format_anchors(a: dict) -> str:
    return (
        f"time={a['time']} ({a['weekday']}, hour={a['hour']}) | "
        f"cpu={a['cpu_percent']}% | "
        f"ram={a['ram_percent']}% ({a['ram_used_gb']}GB used) | "
        f"uptime={a['uptime_hours']}h"
    )
