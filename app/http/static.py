import mimetypes
from pathlib import Path
from urllib.parse import urlparse

# app/http/static.py -> .../app/http/
# project root = parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = PROJECT_ROOT / "public"

def serve(handler, request_path: str):
  parsed = urlparse(request_path)
  rel = parsed.path.lstrip("/") or "index.html"
  if rel.endswith("/"):
    rel += "index.html"

  safe = (PUBLIC_DIR / rel).resolve()
  if not str(safe).startswith(str(PUBLIC_DIR)):
    handler.send_error(403, "Forbidden")
    return

  if not safe.exists() or not safe.is_file():
    handler.send_error(404, "Not Found")
    return

  ctype, _ = mimetypes.guess_type(str(safe))
  ctype = ctype or "application/octet-stream"
  data = safe.read_bytes()

  handler.send_response(200)
  handler.send_header("Content-Type", ctype)
  handler.send_header("Content-Length", str(len(data)))
  handler.end_headers()
  handler.wfile.write(data)
