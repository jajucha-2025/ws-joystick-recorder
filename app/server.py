from http.server import HTTPServer
from socketserver import ThreadingMixIn
from .handler import WSHTTPHandler

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
  daemon_threads = True
  allow_reuse_address = True

def create_server(host: str, port: int) -> HTTPServer:
  return ThreadingHTTPServer((host, port), WSHTTPHandler)
