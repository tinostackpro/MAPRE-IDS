from pathlib import Path
from datetime import datetime, timedelta

class ScreenshotMonitor:
    """Optional, visible evidence capture. Requires explicit activation in the GUI."""
    def __init__(self, directory="evidence/screenshots", retention_days=7):
        self.directory = Path(directory)
        self.retention_days = max(1, int(retention_days))

    def capture(self):
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("Captura opcional exige instalar pyautogui e Pillow: pip install pyautogui Pillow") from exc
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"mapre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot().save(path)
        self.cleanup()
        return path

    def cleanup(self):
        cutoff = datetime.now().timestamp() - self.retention_days * 86400
        if self.directory.exists():
            for path in self.directory.glob("mapre_*.png"):
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink()
                except OSError:
                    pass
