from pathlib import Path
from datetime import datetime

class WebcamMonitor:
    """Visible, explicitly enabled webcam evidence capture for authorized testing."""
    def __init__(self, directory='evidence/webcam', retention_days=7, camera_index=0):
        self.directory = Path(directory)
        self.retention_days = max(1, int(retention_days))
        self.camera_index = int(camera_index)
        self._camera = None

    @property
    def active(self):
        return self._camera is not None and self._camera.isOpened()

    def start(self):
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError('Webcam exige OpenCV. Instale com: pip install opencv-python') from exc
        if self.active:
            return True
        camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(self.camera_index)
        if not camera.isOpened():
            camera.release()
            raise RuntimeError('Não foi possível acessar a webcam. Verifique conexão, permissões e se outro aplicativo a está usando.')
        self._camera = camera
        return True

    def capture(self):
        if not self.active:
            raise RuntimeError('Webcam não está ativa. Inicie a captura pela interface autorizada.')
        ok, frame = self._camera.read()
        if not ok:
            raise RuntimeError('A webcam não forneceu uma imagem válida.')
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f'mapre_webcam_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.jpg'
        try:
            import cv2
            if not cv2.imwrite(str(path), frame):
                raise RuntimeError('Não foi possível salvar a imagem da webcam.')
        except Exception:
            try: path.unlink(missing_ok=True)
            except OSError: pass
            raise
        self.cleanup()
        return path

    def stop(self):
        if self._camera is not None:
            self._camera.release()
            self._camera = None

    def cleanup(self):
        cutoff = datetime.now().timestamp() - self.retention_days * 86400
        if self.directory.exists():
            for path in self.directory.glob('mapre_webcam_*.jpg'):
                try:
                    if path.stat().st_mtime < cutoff: path.unlink()
                except OSError:
                    pass
