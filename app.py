#!/usr/bin/env python3
"""auto-translator — a small, standalone, offline-first translation app.

Backend: Argos Translate (offline NMT), behind a small pluggable-engine layer.
Frontend: a local web UI served from stdlib http.server — type in the box and
it translates instantly. No external services.

Run:   python3 app.py        then open http://127.0.0.1:8765
"""

import collections
import datetime
import glob
import json
import os
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import detection
import engines
import settings
from languages import LANGUAGES

HOST = os.environ.get("AUTO_TRANSLATE_HOST", "127.0.0.1")
PORT = int(os.environ.get("AUTO_TRANSLATE_PORT", "8765"))
APP_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(APP_DIR, "web")

# ---- Auto-reload -------------------------------------------------------------
# A watcher thread fingerprints the source files; when they change on disk the
# process exits with RESTART_EXIT_CODE and the .app launch script restarts it,
# so edits take effect without re-adding the app to the Dock. Web-only changes
# don't need a restart (files are served from disk) — the page polls
# /api/version and reloads itself.
RESTART_EXIT_CODE = 87


def _fingerprint(patterns):
    """A cheap change-fingerprint (path/mtime/size of matching files)."""
    entries = []
    for pat in patterns:
        for p in sorted(glob.glob(os.path.join(APP_DIR, pat))):
            try:
                st = os.stat(p)
                entries.append(f"{p}:{st.st_mtime_ns}:{st.st_size}")
            except OSError:
                pass
    return str(hash("|".join(entries)))


def code_fingerprint():
    return _fingerprint(["*.py", "engines/*.py", "pyproject.toml"])


def web_fingerprint():
    return _fingerprint(["web/*"])


CODE_FP = code_fingerprint()  # what this process was started from


def watch_sources():
    """Poll the source files; on change, exit so the launcher restarts us with
    the new code. Re-checks once after a short pause so we don't restart in the
    middle of an editor's multi-file save."""
    while True:
        time.sleep(1.5)
        if code_fingerprint() == CODE_FP:
            continue
        time.sleep(0.7)   # let the save settle
        log("ソースコードの変更を検出しました。再起動します…")
        os._exit(RESTART_EXIT_CODE)

# ---- In-memory log buffer (shown in the UI, copyable for debugging) ---------
LOG_BUFFER = collections.deque(maxlen=2000)


def log(msg):
    """Record an app-level event (timestamped) and echo to the console."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"{ts}  {msg}"
    LOG_BUFFER.append(line)
    sys.__stdout__.write(line + "\n")
    sys.__stdout__.flush()


class _Tee:
    """Wrap stdout/stderr so library output (warnings, tracebacks, download
    progress) is also captured into LOG_BUFFER for the UI log panel."""

    def __init__(self, orig):
        self._orig = orig
        self._buf = ""

    def write(self, s):
        self._orig.write(s)
        self._buf += s.replace("\r", "\n")
        *lines, self._buf = self._buf.split("\n")
        for ln in lines:
            if ln.strip():
                LOG_BUFFER.append(ln)

    def flush(self):
        self._orig.flush()

    def isatty(self):
        return False




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
        elif self.path == "/api/logs":
            self._send_json({"lines": list(LOG_BUFFER)})
        elif self.path == "/api/version":
            # code: fixed at process start (changes only via restart);
            # web: live from disk, so the page can reload on frontend edits.
            self._send_json({"code": CODE_FP, "web": web_fingerprint()})
        elif self.path == "/api/settings":
            self._send_json({"settings": settings.get(), "defaults": settings.DEFAULTS})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path not in ("/api/translate", "/api/alternatives",
                             "/api/rephrase", "/api/settings"):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json({"error": "bad request"}, status=400)
            return

        if self.path == "/api/settings":
            patch = payload if isinstance(payload, dict) else {}
            new = settings.update(patch)
            log(f"settings updated: {patch}")
            self._send_json({"settings": new})
            return

        if self.path == "/api/alternatives":
            self._handle_alternatives(payload)
            return

        if self.path == "/api/rephrase":
            self._handle_rephrase(payload)
            return

        text = payload.get("text", "")
        src = payload.get("src", "auto")
        tgt = payload.get("tgt", "en")
        engine_name = payload.get("engine") or engines.default_engine_name()

        if not text.strip():
            self._send_json({"translation": "", "detected": src})
            return

        detected = None
        tgt_used = None
        if src == "auto":
            detected = detection.detect(text)
            src = detected or "en"
            if src == tgt:
                # Typing in the language you're translating INTO (e.g. Japanese
                # text with the default target 日本語) used to echo the input
                # back. Translate to the alternate language instead.
                tgt = "en" if tgt != "en" else "ja"
                tgt_used = tgt

        if src == tgt:  # user explicitly chose the same languages — echo as-is
            self._send_json({"translation": text, "detected": detected or src})
            return

        # Progress/preparation messages go to the log only (not the GUI status).
        def on_status(s):
            log(f"  … {s}")

        confirm_download = bool(payload.get("confirm_download"))
        log(f"translate engine={engine_name} {src}->{tgt} ({len(text)} chars)")
        try:
            engine = engines.get_engine(engine_name)
            if not engine.is_available():
                reason = getattr(engine, "unavailable_reason", lambda: None)()
                raise RuntimeError(
                    reason or f"エンジン '{engine_name}' は利用できません。"
                )
            # If using this engine needs a (large) model download, ask first.
            pending = getattr(engine, "pending_download", lambda: None)()
            if pending and not confirm_download:
                log(f"  download needed (~{pending.get('size_gb')}GB) — awaiting confirm")
                self._send_json(
                    {"needs_download": True, "engine": engine_name,
                     "size_gb": pending.get("size_gb"), "detected": detected or src}
                )
                return
            result = engine.translate(text, src, tgt, on_status=on_status)
            log(f"  ✓ ok ({len(result)} chars)")
            resp = {"translation": result, "detected": detected or src}
            if tgt_used:
                resp["tgt_used"] = tgt_used
            self._send_json(resp)
        except Exception as e:
            log(f"  ✗ ERROR [{engine_name}]: {type(e).__name__}: {e}")
            tb = traceback.format_exc()
            if tb and "NoneType: None" not in tb:
                log(tb)
            self._send_json(
                {"error": str(e), "detected": detected or src},
                status=200,
            )


    def _handle_alternatives(self, payload):
        """Post-edit helper: alternative wordings for a selected word/phrase in
        the translation. Only LLM engines (Gemma) support this; others (and a
        not-yet-downloaded model) return unsupported so the UI can say why."""
        sentence = payload.get("sentence", "")
        selection = payload.get("selection", "")
        src = payload.get("src", "auto")
        tgt = payload.get("tgt", "en")
        engine_name = payload.get("engine") or engines.default_engine_name()

        if not selection.strip():
            self._send_json({"alternatives": []})
            return
        try:
            engine = engines.get_engine(engine_name)
        except KeyError:
            self._send_json({"alternatives": [], "unsupported": True,
                             "reason": f"エンジン '{engine_name}' は利用できません。"})
            return

        fn = getattr(engine, "alternatives", None)
        if not fn or not engine.is_available():
            self._send_json(
                {"alternatives": [], "unsupported": True,
                 "reason": "言い換え候補は LLM エンジン（Gemma）を選択したときに利用できます。"}
            )
            return
        if getattr(engine, "pending_download", lambda: None)():
            self._send_json(
                {"alternatives": [], "unsupported": True,
                 "reason": "モデル未取得のため候補を出せません。先に翻訳してモデルを読み込んでください。"}
            )
            return

        log(f"alternatives engine={engine_name} tgt={tgt} sel='{selection[:40]}'")
        try:
            alts = fn(sentence, selection, src, tgt,
                      on_status=lambda s: log(f"  … {s}"))
            log(f"  ✓ {len(alts)} 候補")
            self._send_json({"alternatives": alts})
        except Exception as e:
            log(f"  ✗ alternatives ERROR [{engine_name}]: {type(e).__name__}: {e}")
            self._send_json({"alternatives": [], "error": str(e)})

    def _handle_rephrase(self, payload):
        """Post-edit step 2 (DeepL-style): after the user picks an alternative
        wording, ask the LLM to rewrite the whole translation so the choice
        fits naturally (grammar/agreement around it adjusts too)."""
        source_text = payload.get("text", "")
        sentence = payload.get("sentence", "")
        selection = payload.get("selection", "")
        replacement = payload.get("replacement", "")
        src = payload.get("src", "auto")
        tgt = payload.get("tgt", "en")
        engine_name = payload.get("engine") or engines.default_engine_name()

        if not (sentence.strip() and replacement.strip()):
            self._send_json({"translation": sentence})
            return
        try:
            engine = engines.get_engine(engine_name)
        except KeyError:
            self._send_json({"translation": sentence, "unsupported": True})
            return
        fn = getattr(engine, "rephrase", None)
        if (not fn or not engine.is_available()
                or getattr(engine, "pending_download", lambda: None)()):
            # No LLM to re-flow with — the UI keeps its local word swap.
            self._send_json({"translation": sentence, "unsupported": True})
            return

        log(f"rephrase engine={engine_name} tgt={tgt} "
            f"'{selection[:30]}' -> '{replacement[:30]}'")
        try:
            revised = fn(source_text, sentence, selection, replacement, src, tgt,
                         on_status=lambda s: log(f"  … {s}"))
            log(f"  ✓ ok ({len(revised)} chars)")
            self._send_json({"translation": revised})
        except Exception as e:
            log(f"  ✗ rephrase ERROR [{engine_name}]: {type(e).__name__}: {e}")
            self._send_json({"translation": sentence, "error": str(e)})


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # A client closing the connection mid-response is normal (browser tab
        # closed, request superseded) — don't dump a traceback for it.
        if sys.exc_info()[0] in (ConnectionResetError, BrokenPipeError):
            return
        super().handle_error(request, client_address)


def main():
    # Capture library output (warnings/tracebacks/download progress) for the UI.
    sys.stdout = _Tee(sys.__stdout__)
    sys.stderr = _Tee(sys.__stderr__)

    server = Server((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    log(f"auto-translator starting at {url}")
    for e in engines.list_engines():
        log(f"  engine {e['name']}: {'available' if e['available'] else 'unavailable'}"
            + (f" — {e['reason']}" if e.get('reason') else ""))
    log(f"  default engine: {engines.default_engine_name()}")
    # Load the language detector in the background so the first translation
    # doesn't pay for it (and concurrent first requests can't race the init).
    detection.prewarm()

    # Serve in the background; the GUI window (or browser) is the foreground.
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # Auto-reload: restart (via the launcher's loop) when the source changes.
    restarted = bool(os.environ.get("AUTO_TRANSLATE_RESTARTED"))
    if restarted:
        log("ソース変更により再起動しました。")
    threading.Thread(target=watch_sources, daemon=True).start()

    headless = "--no-window" in sys.argv or os.environ.get("AUTO_TRANSLATE_NO_WINDOW")
    # Browser mode: use the real default browser (reliable IME/日本語入力) instead
    # of the embedded WebView window. Enable with --browser or AUTO_TRANSLATE_BROWSER=1.
    use_browser = "--browser" in sys.argv or os.environ.get("AUTO_TRANSLATE_BROWSER")

    if not headless and not use_browser:
        try:
            import webview  # native window (macOS: WKWebView — no browser)
            log("opening application window")
            webview.create_window(
                "auto-translator", url,
                width=1024, height=700, min_size=(680, 460),
            )
            webview.start()          # blocks on the main thread until window closes
            log("window closed; exiting")
            return
        except Exception as e:
            log(f"native window unavailable ({type(e).__name__}: {e}); using browser")
            use_browser = True

    # Browser / headless: optionally open a browser, then keep serving.
    # After an auto-reload restart, don't open another tab — the already-open
    # page reconnects and reloads itself via /api/version polling.
    no_browser = ("--no-browser" in sys.argv
                  or os.environ.get("AUTO_TRANSLATE_NO_BROWSER") or restarted)
    if use_browser and not no_browser:
        log("opening in the default browser")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    print("  Ctrl-C to stop.")
    try:
        threading.Event().wait()     # block forever (server runs in the thread)
    except KeyboardInterrupt:
        print("\nbye.")


if __name__ == "__main__":
    main()
