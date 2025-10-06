import base64, sqlite3, threading, time
import cv2
from jchutils.camera import Camera, CameraMode
from .ws.hub import broadcast_json
from .state import get_joystick, is_recording

class CaptureWorker:
  def __init__(self, mode=CameraMode.JAJUCHA, device="center", fps=10, jpg_quality=80, db_path="capture.sqlite3", realtime_show_quality=80):
    self.device = device
    self.mode = mode
    self.fps = int(fps)
    self.dt = 1.0 / self.fps
    self.jpg_quality = int(jpg_quality)
    self.realtime_show_quality = int(realtime_show_quality)
    self.db_path = db_path
    self._stop = threading.Event()

  def start(self):
    self._th = threading.Thread(target=self._run, daemon=True)
    self._th.start()

  def stop(self):
    self._stop.set()
    if hasattr(self, "_th"):
      self._th.join(timeout=2)

  def _run(self):
    conn = sqlite3.connect(self.db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
      CREATE TABLE IF NOT EXISTS frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        jpeg BLOB NOT NULL
      )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_frames_ts ON frames(ts)")
    conn.commit()

    camera = Camera(mode=self.mode, device=self.device)
    next_frame = time.perf_counter()
    enc_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpg_quality]

    try:
      while not self._stop.is_set():
        next_frame += self.dt
        now = time.perf_counter()
        if now < next_frame:
          time.sleep(next_frame - now)
        else:
          missed = int((now - next_frame) // self.dt) + 1
          next_frame += missed * self.dt

        img = camera.getFrame()

        ok, buf = cv2.imencode(".jpg", img, enc_param)
        if not ok:
          continue
        jpeg_bytes = buf.tobytes()

        js = get_joystick()
        ts = time.time()

        # 녹화 중일 때만 벡터(x,y) 저장
        if is_recording():
          conn.execute(
            "INSERT INTO frames (ts, x, y, jpeg) VALUES (?, ?, ?, ?)",
            (ts, js["x"], js["y"], sqlite3.Binary(jpeg_bytes))
          )
          conn.commit()

        b64 = base64.b64encode(jpeg_bytes).decode("ascii")
        broadcast_json(None, {
          "type": "frame",
          "ts": ts,
          "angleDeg": js["angleDeg"],
          "strength": js["strength"],
          "x": js["x"],
          "y": js["y"],
          "jpegBase64": b64
        })
    finally:
      try:
        conn.close()
      except Exception:
        pass
