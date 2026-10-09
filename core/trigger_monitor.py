import psutil

class TriggerMonitor:
    """Detects a configured process name/path using visible, local process metadata."""
    @staticmethod
    def is_running(trigger: str) -> bool:
        trigger = trigger.strip().lower()
        if not trigger:
            return False
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                name = (proc.info.get("name") or "").lower()
                exe = (proc.info.get("exe") or "").lower()
                if trigger == name or trigger == exe or ("/" not in trigger and "\\" not in trigger and trigger == name):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
