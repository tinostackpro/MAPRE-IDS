from datetime import datetime

class SessionManager:
    def __init__(self):
        self.active = False
        self.started_at = None
        self.reason = ""

    def start(self, reason="manual"):
        if self.active:
            return False
        self.active = True
        self.started_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self.reason = reason
        return True

    def stop(self):
        if not self.active:
            return False
        self.active = False
        self.reason = ""
        return True
