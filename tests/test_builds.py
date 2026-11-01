"""Tests for the build files themselves: code.py and the mouse variant.

    python3 -m unittest discover -s tests

tests/test_badusb_core.py covers the shared module. Nothing covered the
build files, which hold every route handler, the script interpreter and
the mouse commands -- the boot simulation only checked that they import
and register, and tests/ui/ drives a mock that reimplements the routes
rather than calling these. So the code that actually answers requests on
the device had no tests at all.

These import the real code.py with CircuitPython stubbed, capture the
handlers off the server as they register, and call them.

The differential test matters most. The dry run's usefulness rests
entirely on classify_line agreeing with what execute_script does, and a
dry run that disagrees is worse than none: it would tell you a script is
fine when it is not. That is checked here by running both over the same
lines and comparing.
"""

import importlib.util
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.dirname(__file__))

import boot_simulation  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Request:
    """Stands in for an adafruit_httpserver Request."""

    def __init__(self, body=b"", headers=None):
        self.body = body
        self.headers = headers or {}


class RecordingKeyboard:
    def press(self, key):
        EVENTS.append(("press", key))

    def release(self, key):
        EVENTS.append(("release", key))

    def release_all(self):
        EVENTS.append(("release_all", None))


class RecordingLayout:
    def write(self, char, delay=None):
        EVENTS.append(("type", char))


class RecordingMouse:
    LEFT_BUTTON, RIGHT_BUTTON, MIDDLE_BUTTON = 1, 2, 4

    def click(self, button):
        EVENTS.append(("click", button))

    def press(self, button):
        EVENTS.append(("press", button))

    def release(self, button):
        EVENTS.append(("release", button))

    def release_all(self):
        EVENTS.append(("release_all", None))

    def move(self, x=0, y=0, wheel=0):
        EVENTS.append(("move", (x, y, wheel)))


EVENTS = []


class NoClock:
    """Sleeps instantly, so a script with delays runs in no time."""

    @staticmethod
    def sleep(seconds):
        pass

    @staticmethod
    def monotonic():
        return 0.0


def load_build(build_dir, tmp):
    """Import a build and hand back its module, core and route handlers."""
    boot_simulation.install_stubs()

    routes = {}

    class CapturingServer:
        def __init__(self, pool, root_path=None, **kwargs):
            self.request_buffer_size = 1024

        def route(self, path, method=None, **kwargs):
            def register(handler):
                routes[(method, path)] = handler
                return handler
            return register

        def start(self, port=80):
            pass

        def stop(self):
            pass

        def poll(self):
            return "no_request"

    import adafruit_httpserver.server as server_module
    server_module.Server = CapturingServer

    # Patch the clock before the build runs: its start-up blink sleeps for
    # real, which costs half a second per load and adds up across the suite.
    import badusb_core

    badusb_core.time = NoClock

    spec = importlib.util.spec_from_file_location(
        "badusb_build_under_test", os.path.join(build_dir, "code.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.setup_server()

    module.time = NoClock
    module.led = type("Led", (), {"value": False})()

    keyboard, layout = RecordingKeyboard(), RecordingLayout()
    module.keyboard, module.keyboard_layout = keyboard, layout
    if hasattr(module, "mouse"):
        module.mouse = RecordingMouse()

    badusb_core.configure(
        ssid="net", password="pw", keyboard=keyboard, keyboard_layout=layout,
        key_mapping=module.KEY_MAPPING,
        script_path=os.path.join(tmp, "active.txt"),
        script_dir=os.path.join(tmp, "scripts"),
    )
    return module, badusb_core, routes


def body_text(response):
    body = getattr(response, "body", None)
    return body.decode() if isinstance(body, bytes) else body


class BuildTestCase(unittest.TestCase):
    BUILD = REPO

    def setUp(self):
        import tempfile

        self.tmp = tempfile.mkdtemp()
        EVENTS.clear()
        self.module, self.core, self.routes = load_build(self.BUILD, self.tmp)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def call(self, method, path, request=None):
        handler = self.routes.get((method, path))
        self.assertIsNotNone(handler, f"no route for {method} {path}")
        return handler(request or Request())

    def json_body(self, response):
        return json.loads(body_text(response))


class TestRoutes(BuildTestCase):
    def test_every_expected_route_is_registered(self):
        for method, path in [
            ("GET", "/"), ("POST", "/validate"), ("POST", "/dry-run"),
            ("GET", "/scripts"), ("POST", "/scripts"), ("POST", "/upload"),
            ("POST", "/execute"), ("POST", "/verify"),
            ("GET", "/wifi-status"), ("POST", "/api/badusb"),
        ]:
            with self.subTest(route=f"{method} {path}"):
                self.assertIn((method, path), self.routes)

    def test_validate_reports_the_space_separated_trap(self):
        response = self.call("POST", "/validate",
                             Request(b"STRING hi\nCTRL ALT DELETE"))
        problems = self.json_body(response)["problems"]
        self.assertEqual(problems[0]["line"], 2)
        self.assertIn("only CTRL is sent", problems[0]["message"])

    def test_dry_run_without_a_script_anywhere_is_a_404(self):
        response = self.call("POST", "/dry-run", Request(b""))
        self.assertEqual(response.status, 404)

    def test_malformed_json_is_a_400_not_a_500(self):
        response = self.call("POST", "/scripts", Request(b"not json"))
        self.assertEqual(response.status, 400)

    def test_a_traversing_script_name_is_refused(self):
        response = self.call("POST", "/scripts", Request(json.dumps(
            {"action": "save", "name": "../boot.py", "script": "x"}).encode()))
        self.assertEqual(response.status, 400)

    def test_an_oversized_upload_is_a_413(self):
        response = self.call("POST", "/upload", Request(b"x" * 99999))
        self.assertEqual(response.status, 413)

    def test_status_reports_memory_and_uptime(self):
        payload = self.json_body(self.call("GET", "/wifi-status"))
        for key in ("connected", "ip", "uptime_s", "free_memory"):
            self.assertIn(key, payload)

    def test_inspecting_a_script_sends_no_keystrokes(self):
        self.call("POST", "/validate", Request(b"STRING hello\nENTER"))
        self.call("POST", "/dry-run", Request(b"STRING hello\nENTER"))
        self.assertEqual(EVENTS, [])


class TestDryRunMatchesExecution(BuildTestCase):
    """The dry run is only worth having if it agrees with the executor."""

    LINES = [
        "STRING hello", "ENTER", "CTRL+ALT+DELETE", "CTRL ALT DELETE",
        "GUI R", "DELAY 100", "CHAR_DELAY 5", "REM note", "# note",
        "BOGUS_COMMAND", "", "   ", "STRING", "DELAY abc", "CTRL+NOPE", "A",
    ]

    def run_line(self, line):
        EVENTS.clear()
        self.core.save_script(line + "\n")
        self.module.execute_script()
        return list(EVENTS)

    def test_quiet_classifications_really_are_quiet(self):
        for line in self.LINES:
            kind, _detail, _warning = self.core.classify_line(line)
            if kind not in ("blank", "comment", "unknown", "delay", "char_delay"):
                continue
            with self.subTest(line=line, kind=kind):
                self.assertEqual(
                    self.run_line(line), [],
                    f"classified {kind}, so it must send nothing")

    def test_a_line_classified_as_typing_types(self):
        events = self.run_line("STRING hello")
        self.assertEqual("".join(k for a, k in events if a == "type"), "hello")

    def test_a_line_classified_as_a_key_presses_one(self):
        self.assertTrue(any(a == "press" for a, _k in self.run_line("ENTER")))

    def test_a_combination_presses_all_of_its_keys(self):
        pressed = [k for a, k in self.run_line("CTRL+ALT+DELETE") if a == "press"]
        self.assertEqual(len(pressed), 3)

    def test_the_reported_trap_is_what_actually_happens(self):
        """classify_line warns that only the first key is sent. If the
        executor ever stops behaving that way, the warning becomes a lie
        and this fails."""
        pressed = [k for a, k in self.run_line("CTRL ALT DELETE") if a == "press"]
        self.assertEqual(len(pressed), 1,
                         "the validator promises only one key is sent")


class TestMouseBuild(BuildTestCase):
    BUILD = os.path.join(REPO, "Mouse_control_test")

    def run_mouse(self, command, params=""):
        EVENTS.clear()
        result = self.module.execute_mouse_command(command, params, 0.0, 1)
        return result, list(EVENTS)

    def test_the_mouse_routes_exist_too(self):
        self.assertIn(("GET", "/script"), self.routes)
        self.assertIn(("POST", "/verify"), self.routes)

    def test_an_unknown_button_is_refused_rather_than_claimed(self):
        for command in ("MOUSE_CLICK", "MOUSE_PRESS", "MOUSE_RELEASE"):
            with self.subTest(command=command):
                result, events = self.run_mouse(command, "BOGUS")
                self.assertFalse(result)
                self.assertEqual(events, [],
                                 "reporting success for nothing was the bug")

    def test_scrolling_backwards_is_refused(self):
        result, events = self.run_mouse("SCROLL_UP", "-5")
        self.assertFalse(result)
        self.assertEqual(events, [])

    def test_an_enormous_scroll_is_clamped(self):
        _result, events = self.run_mouse("SCROLL_UP", "99999")
        self.assertLessEqual(len(events), self.module.MAX_SCROLL_STEPS)

    def test_scroll_directions_are_opposite(self):
        _r, up = self.run_mouse("SCROLL_UP", "2")
        _r, down = self.run_mouse("SCROLL_DOWN", "2")
        self.assertGreater(sum(e[1][2] for e in up), 0)
        self.assertLess(sum(e[1][2] for e in down), 0)

    def test_a_drag_always_releases_the_button(self):
        _result, events = self.run_mouse("MOUSE_DRAG", "100 100")
        self.assertTrue(any(a == "release" for a, _b in events),
                        "a drag that never releases leaves the target stuck")

    def test_bad_coordinates_are_refused(self):
        for params in ("abc def", "10", ""):
            with self.subTest(params=params):
                result, events = self.run_mouse("MOUSE_MOVE", params)
                self.assertFalse(result)
                self.assertEqual(events, [])

    def test_movement_undershoots_which_is_a_known_issue(self):
        """Documented in the README rather than fixed: each step is
        truncated with int(), so the pointer lands short. Pinned here so
        the extent is known and a change to it is deliberate."""
        _result, events = self.run_mouse("MOUSE_DRAG", "100 100")
        travelled = sum(e[1][0] for e in events if e[0] == "move")
        self.assertLessEqual(travelled, 100)
        self.assertGreater(travelled, 90, "undershoot should be small")


if __name__ == "__main__":
    unittest.main()
