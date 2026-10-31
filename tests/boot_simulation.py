#!/usr/bin/env python3
"""Execute each build's code.py the way the board would, without a board.

    python3 tests/boot_simulation.py

This is the closest thing to "does it still boot" that can be checked
here. It runs each code.py from top to bottom against stubbed
CircuitPython modules, then calls setup_server() and reports the routes
that got registered. It catches the things that stop a board dead: a name
that no longer exists after a refactor, an import that moved, a route
decorator that raises.

It proves nothing about USB HID, the radio, or the real HTTP server --
all of those are stubs. A green run means the code holds together, not
that the firmware works.

Exits non-zero if either build fails, so CI can use it.
"""

import os
import sys
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "lib"))
sys.path.insert(0, os.path.join(REPO, "tests"))

import circuitpython_stubs as stubs  # noqa: E402


class AnyKeycode(type):
    """Hands out a distinct value for any attribute asked of it.

    The real Keycode has dozens of members and the two builds use
    different subsets. Generating them on demand means this simulation
    fails on the code under test rather than on gaps in the stub.
    """

    _next = 0

    def __getattr__(cls, name):
        AnyKeycode._next += 1
        setattr(cls, name, AnyKeycode._next)
        return AnyKeycode._next


def install_stubs():
    """Everything a build imports at module scope, beyond the shared stubs."""
    stubs.install()

    keycode = types.ModuleType("adafruit_hid.keycode")
    keycode.Keycode = AnyKeycode("Keycode", (), {})
    sys.modules["adafruit_hid.keycode"] = keycode

    usb_hid = types.ModuleType("usb_hid")
    usb_hid.devices = ("keyboard", "mouse", "consumer")
    sys.modules["usb_hid"] = usb_hid

    socketpool = types.ModuleType("socketpool")
    socketpool.SocketPool = lambda radio: "pool"
    sys.modules["socketpool"] = socketpool

    for module_name, class_name in (
        ("adafruit_hid.keyboard", "Keyboard"),
        ("adafruit_hid.keyboard_layout_us", "KeyboardLayoutUS"),
        ("adafruit_hid.mouse", "Mouse"),
    ):
        module = types.ModuleType(module_name)
        setattr(module, class_name, type(class_name, (), {
            "__init__": lambda self, *a, **k: None,
            "LEFT_BUTTON": 1, "RIGHT_BUTTON": 2, "MIDDLE_BUTTON": 4,
            "led_status": bytes([0]),
            "press": lambda self, *a: None,
            "release": lambda self, *a: None,
            "release_all": lambda self: None,
            "click": lambda self, *a: None,
            "move": lambda self, *a, **k: None,
            "write": lambda self, *a, **k: None,
        }))
        sys.modules[module_name] = module

    routes = []

    class Server:
        def __init__(self, pool, root_path=None, **kwargs):
            self.root_path = root_path
            self.request_buffer_size = 1024

        def route(self, path, method=None, **kwargs):
            def decorator(handler):
                routes.append((method, path))
                return handler
            return decorator

        def start(self, port=80):
            pass

        def stop(self):
            pass

        def poll(self):
            return "no_request"

    server_module = types.ModuleType("adafruit_httpserver.server")
    server_module.Server = Server
    sys.modules["adafruit_httpserver.server"] = server_module

    methods = types.ModuleType("adafruit_httpserver.methods")
    methods.GET, methods.POST = "GET", "POST"
    sys.modules["adafruit_httpserver.methods"] = methods

    return routes


def simulate(build_dir, label):
    """Import one build and bring its server up. True when both worked."""
    import importlib.util

    routes = install_stubs()
    path = os.path.join(build_dir, "code.py")

    try:
        spec = importlib.util.spec_from_file_location("badusb_build", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"  {label}: import FAILED -- {type(e).__name__}: {e}")
        return False

    try:
        module.setup_server()
    except Exception as e:
        print(f"  {label}: setup_server FAILED -- {type(e).__name__}: {e}")
        return False

    print(f"  {label}: imports and registers {len(routes)} routes")
    for method, route in routes:
        print(f"      {method:5} {route}")
    return True


def main():
    print("Simulated boot (stubbed CircuitPython, no hardware):\n")

    results = [
        simulate(REPO, "code.py"),
        simulate(os.path.join(REPO, "Mouse_control_test"), "Mouse_control_test/code.py"),
    ]

    if not all(results):
        print("\nAt least one build would not start.")
        return 1

    print("\nBoth builds hold together. This says nothing about USB HID, "
          "the radio or the real HTTP server.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
