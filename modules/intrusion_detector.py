from collections import defaultdict, deque
from datetime import datetime

class IntrusionDetector:
    """Simple transparent heuristics; alerts are leads, not proof of intrusion."""
    def __init__(self, threshold=8, window_seconds=60):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.attempts = defaultdict(deque)

    def observe(self, source, destination, description="Conexão observada"):
        now = datetime.now().timestamp()
        q = self.attempts[source]
        q.append(now)
        while q and now - q[0] > self.window_seconds:
            q.popleft()
        if len(q) == self.threshold:
            return {"category": "Possível anomalia", "severity": "Média", "description": f"Múltiplas conexões originadas em {source}",
                    "source": source, "destination": destination, "details": f"{len(q)} eventos/{self.window_seconds}s; regra heurística"}
        return None
