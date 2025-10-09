import argparse
from .server import create_server
from .ws.hub import close_all
from .capture import CaptureWorker
from jchutils.camera import CameraMode

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--host", default="0.0.0.0")
  ap.add_argument("--port", type=int, default=8765)
  args = ap.parse_args()

  worker = CaptureWorker(
    device="center",
    mode=CameraMode.JAJUCHA,
    fps=10,
    jpg_quality=80,
    db_path="capture.sqlite3",
    realtime_show_quality=80
  )
  worker.start()

  httpd = create_server(args.host, args.port)
  print(f"Serving on http://{args.host}:{args.port}  (WebSocket at ws://{args.host}:{args.port}/ws)")
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print("\nShutting down...")
  finally:
    try:
      httpd.server_close()
    finally:
      close_all()
      worker.stop()

if __name__ == "__main__":
  main()
