import socket
import struct

def _recv_exact(sock: socket.socket, n: int) -> bytes:
  data = bytearray()
  while len(data) < n:
    chunk = sock.recv(n - len(data))
    if not chunk:
      raise ConnectionError("socket closed")
    data.extend(chunk)
  return bytes(data)

def parse_frame(sock: socket.socket):
  # returns (fin, opcode, payload)
  header = _recv_exact(sock, 2)
  b1, b2 = header[0], header[1]
  fin = (b1 & 0x80) != 0
  opcode = b1 & 0x0F
  masked = (b2 & 0x80) != 0
  length = b2 & 0x7F

  if length == 126:
    (length,) = struct.unpack("!H", _recv_exact(sock, 2))
  elif length == 127:
    (length,) = struct.unpack("!Q", _recv_exact(sock, 8))

  mask_key = b""
  if masked:
    mask_key = _recv_exact(sock, 4)

  payload = _recv_exact(sock, length) if length else b""
  if masked and payload:
    payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

  return fin, opcode, payload

def _build_frame(opcode: int, payload: bytes = b"") -> bytes:
  b1 = 0x80 | (opcode & 0x0F)
  length = len(payload)
  if length <= 125:
    head = bytes([b1, length])
  elif length <= 0xFFFF:
    head = bytes([b1, 126]) + struct.pack("!H", length)
  else:
    head = bytes([b1, 127]) + struct.pack("!Q", length)
  return head + payload

def send_text(sock: socket.socket, text: str):
  sock.sendall(_build_frame(0x1, text.encode("utf-8")))

def send_pong(sock: socket.socket, payload: bytes):
  sock.sendall(_build_frame(0xA, payload))

def send_close(sock: socket.socket, code: int = 1000, reason: str = ""):
  try:
    payload = struct.pack("!H", code) + reason.encode("utf-8")
  except Exception:
    payload = struct.pack("!H", code)
  try:
    sock.sendall(_build_frame(0x8, payload))
  except Exception:
    pass
