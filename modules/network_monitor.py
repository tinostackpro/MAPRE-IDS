import psutil
from collections import Counter
from datetime import datetime

class NetworkMonitor:
    """Collects connection metadata exposed by the OS; it does not capture packet payloads."""
    def __init__(self):
        self._previous = set()
        self._seen_times = []

    def snapshot(self):
        rows = []
        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, OSError):
            connections = []
        for c in connections:
            if not c.laddr:
                continue
            local = f"{c.laddr.ip}:{c.laddr.port}"
            remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
            try:
                proc = psutil.Process(c.pid).name() if c.pid else "—"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc = "—"
            rows.append({"protocol": "TCP" if c.type == 1 else "UDP", "status": c.status or "—", "local": local,
                         "remote": remote, "pid": c.pid or "—", "process": proc})
        return rows

    def new_events(self, rows, threshold=30, window_seconds=60):
        now = datetime.now().timestamp()
        current = {(r['protocol'], r['local'], r['remote'], r['pid'], r['process']) for r in rows}
        added = current - self._previous
        self._previous = current
        self._seen_times.extend([now] * len(added))
        self._seen_times = [t for t in self._seen_times if now - t <= window_seconds]
        events = [{"category": "Conexão", "severity": "Info", "description": "Nova conexão observada",
                   "source": r[1], "destination": r[2], "details": f"{r[0]} · PID {r[3]} · {r[4]}"}
                  for r in added]
        if len(self._seen_times) >= threshold and added:
            events.append({"category": "Anomalia", "severity": "Média", "description": f"Volume elevado: {len(self._seen_times)} novas conexões em {window_seconds}s",
                           "source": "Sistema", "destination": "—", "details": "Regra heurística; requer validação"})
            self._seen_times.clear()
        return events
