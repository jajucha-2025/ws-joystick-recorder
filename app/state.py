import threading, time
from jchutils.math import pd_rk2
import math

_lock = threading.Lock()

_state = {"angleDeg": 0.0, "strength": 0.0, "x": 0.0, "y": 0.0, "ts": 0.0}

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

_car = {"wheelbase": 1, "pos": (0.0, 0.0, 0.0)}

def get_pos(wheelbase, dt, pos, steer_deg, v):
  return pd_rk2(pos, v, math.radians(steer_deg), wheelbase, dt)

def set_car(wheelbase, pos):
  with _lock:
    _car["wheelbase"] = float(wheelbase)
    _car["pos"] = (float(pos[0]), float(pos[1]), float(pos[2]))
