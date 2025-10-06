import json
import threading
from typing import Set
import socket
from .protocol import send_text

_CLIENTS: Set[socket.socket] = set()
_LOCK = threading.Lock()

def add_client(ws: socket.socket):
  with _LOCK:
    _CLIENTS.add(ws)

def remove_client(ws: socket.socket):
  with _LOCK:
    _CLIENTS.discard(ws)

def broadcast_text(sender: socket.socket, text: str):
  dead = []
  with _LOCK:
    targets = list(_CLIENTS)
  for ws in targets:
    try:
      send_text(ws, text)
    except Exception:
      dead.append(ws)
  if dead:
    with _LOCK:
      for ws in dead:
        _CLIENTS.discard(ws)
        try:
          ws.close()
        except Exception:
          pass

def broadcast_json(sender: socket.socket, obj: dict):
  broadcast_text(sender, json.dumps(obj, separators=(",", ":")))

def close_all():
  with _LOCK:
    targets = list(_CLIENTS)
    _CLIENTS.clear()
  for ws in targets:
    try:
      ws.close()
    except Exception:
      pass
