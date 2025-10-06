import threading, time

_state = {"angleDeg": 0.0, "strength": 0.0, "x": 0.0, "y": 0.0, "ts": 0.0}
_lock = threading.Lock()

def set_joystick(angleDeg, strength, x, y, ts=None):
  with _lock:
    _state["angleDeg"] = float(angleDeg)
    _state["strength"] = float(strength)
    _state["x"] = float(x)
    _state["y"] = float(y)
    _state["ts"] = float(ts if ts is not None else time.time())

def get_joystick():
  with _lock:
    return dict(_state)

_recording = False

def set_recording(on: bool):
  global _recording
  with _lock:
    _recording = bool(on)

def is_recording() -> bool:
  with _lock:
    return _recording
