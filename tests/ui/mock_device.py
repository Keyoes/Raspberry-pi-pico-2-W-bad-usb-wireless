"""A stand-in for the device, so the web page can be driven in a browser.

Serves the real www/index.html and implements the endpoints the page calls,
backed by the real lib/badusb_core.py rather than canned responses -- so
what the page gets back is what the firmware would send.

    python3 tests/ui/mock_device.py        # then open http://127.0.0.1:8111

Used by ui_test.js. It stubs CircuitPython, so it says nothing about USB
HID or the radio; it exercises the page, not the hardware.
"""
import json, os, sys, tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "lib"))
sys.path.insert(0, os.path.join(REPO, "tests"))
import circuitpython_stubs as stubs
stubs.install()
import badusb_core as core

STATE = tempfile.mkdtemp(prefix="badusb-ui-test-")

core.configure("Net", "pw", stubs.FakeKeyboard(), None, stubs.KEY_MAPPING,
               script_path=os.path.join(STATE, "active.txt"),
               script_dir=os.path.join(STATE, "scripts"))

def PAGE_BYTES():
    return open(os.path.join(REPO, "www/index.html"), "rb").read()

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)): body = json.dumps(body)
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n).decode("utf-8")

    def do_GET(self):
        if self.path.startswith("/wifi-status"):
            return self._send(200, core.status_snapshot())
        if self.path == "/scripts":
            return self._send(200, {"scripts": core.list_scripts()})
        return self._send(200, PAGE_BYTES(), "text/html")

    def do_POST(self):
        body = self._body()
        if self.path == "/validate":
            problems = core.validate_script(body)
            return self._send(200, {"ok": not problems, "problems": [
                {"line": n, "text": t, "message": m} for n, t, m in problems]})
        if self.path == "/dry-run":
            text = body or core.read_script()
            if not text: return self._send(404, {"error": "no script"})
            return self._send(200, {"steps": core.explain_script(text)})
        if self.path == "/scripts":
            d = json.loads(body); a, name = d.get("action"), d.get("name", "")
            try:
                if a == "save":
                    core.save_named_script(name, d.get("script", ""))
                    return self._send(200, {"status": "success", "name": name})
                if a == "load":
                    c = core.load_named_script(name)
                    if c is None: return self._send(404, {"error": "no such script"})
                    return self._send(200, {"status": "success", "name": name,
                                            "detail": core.save_script(c)})
                if a == "delete":
                    if not core.delete_named_script(name):
                        return self._send(404, {"error": "no such script"})
                    return self._send(200, {"status": "success", "name": name})
            except ValueError as e:
                return self._send(400, {"error": str(e)})
            return self._send(400, {"error": "unknown action"})
        if self.path == "/upload":
            return self._send(200, "Script uploaded: " + core.save_script(body), "text/plain")
        if self.path == "/execute":
            return self._send(200, "executed", "text/plain")
        return self._send(404, {"error": "nope"})

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8111), H).serve_forever()
