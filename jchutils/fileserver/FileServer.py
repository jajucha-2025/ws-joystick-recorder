# 파일 HTTP 정적 서빙 + 업로드

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading
import os, re, shutil, time

DEFAULT_MAX_UPLOAD: int = 1 *1024 *1024 *1024 # 1GB

def safe_name(name: str) -> str:
    name = os.path.basename(name)
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', name)
    return name or f'upload_{int(time.time())}'

def unique_path(root: str, name: str) -> str:
    path = os.path.join(root, name)
    if not os.path.exists(path):
        return path
    stem, dot, ext = name.partition('.')
    i = 1
    while True:
        cand = f"{stem}_{i}{dot}{ext}" if dot else f"{stem}_{i}"
        path = os.path.join(root, cand)
        if not os.path.exists(path):
            return path
        i += 1

def make_handler(directory: str, max_upload: int = DEFAULT_MAX_UPLOAD):
    class UploadHandler(SimpleHTTPRequestHandler):
        # 업로드 페이지
        def do_GET(self):
            if self.path.rstrip('/') == '/upload':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"""<!doctype html><meta charset="utf-8">
<title>Upload</title>
<input id=f type=file multiple>
<button id=btn>Upload\</button>
<script>
document.getElementById('btn').onclick = async () => {
const fs = document.getElementById('f').files;
for (const f of fs) {
    const res = await fetch('/' + encodeURIComponent(f.name), {method:'PUT', body:f});
    console.log(f.name, await res.text());
}
alert('PUT upload done');
};
</script>""")
                return
            return super().do_GET()

        # PUT 업로드
        def do_PUT(self):
            length = self.headers.get('Content-Length')
            if length and int(length) > max_upload:
                self.send_error(413, f"Upload too large (> {max_upload} bytes)")
                return

            name = safe_name(os.path.basename(self.path))
            if not name:
                self.send_error(400, "Invalid filename")
                return
            path = unique_path(self.directory, name)

            remaining = int(length) if length else None
            with open(path, 'wb') as f:
                if remaining is None:
                    shutil.copyfileobj(self.rfile, f)
                else:
                    buf = 64 * 1024
                    while remaining > 0:
                        chunk = self.rfile.read(min(buf, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)

            self.send_response(201, "Created")
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Saved to {os.path.basename(path)}\n".encode('utf-8'))
    
    UploadHandler.directory = os.path.abspath(directory)
    return UploadHandler

class FileServer:
    """정적 서빙 + 업로드 서버를 쓰레드로 돌리거나 블로킹 실행하는 헬퍼."""
    def __init__(self, directory: str, host: str = "0.0.0.0", port: int = 8000, max_upload: int = DEFAULT_MAX_UPLOAD):
        self.directory = os.path.abspath(directory)
        self.host = host
        self.port = port
        handler = make_handler(self.directory, max_upload)
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = None

    def start(self) -> "FileServer":
        if self._thread and self._thread.is_alive():
            return self
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        print(f"Serving {self.directory} at http://{self.host}:{self.port} (threaded)")
        return self

    def stop(self) -> None:
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        finally:
            if self._thread:
                self._thread.join(timeout=2)
    
    def runForever(self) -> None:
        with self._httpd as httpd:
            print(f"Serving {self.directory} at http://{self.host}:{self.port}  (Ctrl+C to quit)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass

__all__ = [FileServer.__name__]
