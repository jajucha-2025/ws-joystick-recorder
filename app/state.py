import threading, time
from jchutils.math import pd_euler, pd_rk2, pd_rk4
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

_car = {"wheelbase": 18, "trackspacing": 15, "pos": (0.0, 0.0, 0.0), "isFirst": True}

def get_pos(wheelbase, dt, pos, steerL_deg, steerR_deg, v):
  pos = pd_euler(pos, v, math.radians(steerL_deg), math.radians(steerR_deg), wheelbase, dt)
  return pos

def set_car(wheelbase, trackspacing, pos):
  with _lock:
    _car["wheelbase"] = float(wheelbase)
    _car["trackspacing"] = float(trackspacing)
    _car["pos"] = (float(pos[0]), float(pos[1]), float(pos[2]))
