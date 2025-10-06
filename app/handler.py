import base64
import hashlib
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from .http.static import serve as serve_static
from .ws.handshake import MAGIC_GUID
from .ws.protocol import parse_frame, send_text, send_pong, send_close
from .ws.hub import add_client, remove_client, broadcast_text, broadcast_json
import time
from .state import set_joystick, set_recording
from . import control

class WSHTTPHandler(BaseHTTPRequestHandler):
  server_version = "PyWS/0.2"

  def log_message(self, *args, **kwargs):
    # keep quiet
    return

  def do_GET(self):
    path = urlparse(self.path).path
    if self._is_websocket_request() and path == "/ws":
      self._handle_websocket()
    else:
      serve_static(self, self.path)

  def _is_websocket_request(self) -> bool:
    upgrade = (self.headers.get("Upgrade") or "").lower()
    connection = (self.headers.get("Connection") or "").lower()
    return upgrade == "websocket" and "upgrade" in connection

  def _compute_accept(self, key: str) -> str:
    s = (key.strip() + MAGIC_GUID).encode("utf-8")
    sha1 = hashlib.sha1(s).digest()
    return base64.b64encode(sha1).decode("ascii")

  def _handle_websocket(self):
    # validate
    key = self.headers.get("Sec-WebSocket-Key")
    version = self.headers.get("Sec-WebSocket-Version")
    if not key or version != "13":
      self.send_response(426, "Upgrade Required")
      self.send_header("Sec-WebSocket-Version", "13")
      self.end_headers()
      return

    # handshake (RFC 6455)
    accept_val = self._compute_accept(key)
    self.send_response(101, "Switching Protocols")
    self.send_header("Upgrade", "websocket")
    self.send_header("Connection", "Upgrade")
    self.send_header("Sec-WebSocket-Accept", accept_val)
    self.end_headers()

    ws = self.connection
    add_client(ws)
    try:
      send_text(ws, "Connected. Send joystick JSON packets.")
      while True:
        fin, opcode, payload = parse_frame(ws)

        if opcode == 0x9:  # ping
          send_pong(ws, payload)
          continue
        if opcode == 0xA:  # pong
          continue
        if opcode == 0x8:  # close
          send_close(ws)
          break

        if opcode == 0x1:  # text
          txt = payload.decode("utf-8", errors="replace")
          try:
            obj = json.loads(txt)
          except Exception:
            broadcast_text(ws, f"[{self.client_address[0]}] {txt}")
          else:
            if obj.get("type") == "joystick":
              obj["from"] = self.client_address[0]

              # 최신 조이스틱 상태 업데이트 (DB/스트리밍용)
              set_joystick(
                obj.get("angleDeg", 0),
                obj.get("strength", 0),
                obj.get("x", 0),
                obj.get("y", 0),
                obj.get("t", time.time())
              )

              control.on_joystick(
                float(obj.get("angleDeg", 0)),
                float(obj.get("strength", 0)),
                float(obj.get("x", 0)),
                float(obj.get("y", 0)),
                float(obj.get("t", time.time()))
              )

              # (기존) 콘솔 출력 및 브로드캐스트 유지
              print(
                f"[joystick] from={obj['from']} angleDeg={float(obj.get('angleDeg', 0)):.1f} "
                f"strength={float(obj.get('strength', 0)):.2f} x={float(obj.get('x', 0)):.2f} y={float(obj.get('y', 0)):.2f}",
                flush=True
              )
              broadcast_json(ws, obj)
            else:
              if obj.get("type") == "rec":
                on = bool(obj.get("on"))
                set_recording(on)
                # 현재 상태를 모든 클라이언트에 알려줌
                broadcast_json(ws, {"type": "rec", "on": on})
                print(f"[rec] recording={'ON' if on else 'OFF'}", flush=True)
              else:
                broadcast_text(ws, f"[{self.client_address[0]}] {txt}")
        elif opcode == 0x2:
          broadcast_text(ws, f"[{self.client_address[0]}] <{len(payload)} bytes>")
        else:
          send_close(ws, 1003, "Unsupported opcode")
          break
    except Exception:
      pass
    finally:
      remove_client(ws)
      try:
        ws.close()
      except Exception:
        pass
