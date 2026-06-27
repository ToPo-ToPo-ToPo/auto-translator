#!/usr/bin/env python3
"""auto-translator — a small, standalone, offline-first translation app.

Backend: Argos Translate (offline NMT), behind a small pluggable-engine layer.
Frontend: a local web UI served from stdlib http.server — type in the box and
it translates instantly. No external services.

Run:   python3 app.py        then open http://127.0.0.1:8765
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import engines
from languages import LANGUAGES, normalize_code

HOST = os.environ.get("AUTO_TRANSLATE_HOST", "127.0.0.1")
PORT = int(os.environ.get("AUTO_TRANSLATE_PORT", "8765"))
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


def detect_language(text):
    """Best-effort source detection. Returns an ISO code or None."""
    try:
        from langdetect import detect
        return normalize_code(detect(text))
    except Exception:
        return None


class Handler(BaseHTTPRequestHandler):
    # ---- helpers -------------------------------------------------------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quieter console
        pass

    # ---- routing -------------------------------------------------------
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_file(os.path.join(WEB_DIR, "index.html"), "text/html; charset=utf-8")
        elif self.path == "/api/config":
            self._send_json(
                {
                    "languages": [
                        {"code": c, "name": n, "native": native}
                        for c, n, native in LANGUAGES
                    ],
                    "engines": engines.list_engines(),
                    "default_engine": engines.default_engine_name(),
                }
            )
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/translate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json({"error": "bad request"}, status=400)
            return

        text = payload.get("text", "")
        src = payload.get("src", "auto")
        tgt = payload.get("tgt", "en")
        engine_name = payload.get("engine") or engines.default_engine_name()

        if not text.strip():
            self._send_json({"translation": "", "detected": src})
            return

        detected = None
        if src == "auto":
            detected = detect_language(text)
            src = detected or "en"

        if src == tgt:
            self._send_json({"translation": text, "detected": detected or src})
            return

        statuses = []
        try:
            engine = engines.get_engine(engine_name)
            if not engine.is_available():
                reason = getattr(engine, "unavailable_reason", lambda: None)()
                raise RuntimeError(
                    reason or f"エンジン '{engine_name}' は利用できません。"
                )
            result = engine.translate(
                text, src, tgt, on_status=statuses.append
            )
            self._send_json(
                {"translation": result, "detected": detected or src, "status": statuses}
            )
        except Exception as e:
            self._send_json(
                {"error": str(e), "detected": detected or src, "status": statuses},
                status=200,
            )


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # A client closing the connection mid-response is normal (browser tab
        # closed, request superseded) — don't dump a traceback for it.
        if sys.exc_info()[0] in (ConnectionResetError, BrokenPipeError):
            return
        super().handle_error(request, client_address)


def main():
    server = Server((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    avail = [e["name"] for e in engines.list_engines() if e["available"]]
    print(f"auto-translator running at {url}")
    print(f"  available engines : {', '.join(avail) or '(none — run: pip install argostranslate)'}")
    print(f"  default engine    : {engines.default_engine_name()}")
    print("  Ctrl-C to stop.")
    no_browser = "--no-browser" in sys.argv or os.environ.get("AUTO_TRANSLATE_NO_BROWSER")
    if not no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye.")
        server.shutdown()


if __name__ == "__main__":
    main()
