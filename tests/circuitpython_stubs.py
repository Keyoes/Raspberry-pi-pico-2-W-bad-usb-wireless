"""Just enough fake CircuitPython to import badusb_core on a desktop.

CircuitPython's ``board``, ``digitalio``, ``wifi``, ``usb_hid`` and the
Adafruit libraries only exist on the device, so none of this code can
normally be run or tested without flashing a board. These stubs stand in
for them so the logic in ``lib/badusb_core.py`` -- script storage, script
validation, the dry run, the reconnect policy, the server restart -- can be
exercised with plain CPython.

They deliberately do not emulate hardware behaviour. Anything that depends
on real USB HID or a real radio still has to be checked on a board.
"""

import sys
import types


class FakeKeyboard:
    """Records presses and releases instead of sending them over USB."""

    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))

    def release_all(self):
        self.events.append(("release_all", None))

    @property
    def pressed(self):
        return [key for action, key in self.events if action == "press"]


class FakeRadio:
    def __init__(self):
        self.connected = True
        self.ipv4_address = "192.168.1.50"
        self.attempts = 0
        self.connect_succeeds = True

    def connect(self, ssid, password):
        self.attempts += 1
        if not self.connect_succeeds:
            raise OSError("network unreachable")
        self.connected = True


class FakeResponse:
    def __init__(self, request, body=None, status=200, content_type=None, headers=None):
        self.request = request
        self.body = body
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}


class FakeFileResponse:
    def __init__(self, request, filename, root_path=None, **kwargs):
        self.request = request
        self.filename = filename
        self.root_path = root_path


def install(with_led=True, free_memory=180000):
    """Install the stub modules and return handles to the useful ones.

    Call this before importing ``badusb_core``; it clears the module from
    the import cache so each test gets a fresh one.
    """
    for name in list(sys.modules):
        if name == "badusb_core" or name.split(".")[0] in (
            "board", "digitalio", "microcontroller", "wifi", "usb_hid",
            "adafruit_hid", "adafruit_httpserver",
        ):
            del sys.modules[name]

    board = types.ModuleType("board")
    if with_led:
        board.LED = "GP25"

    class DigitalInOut:
        def __init__(self, pin):
            self.pin = pin
            self.value = False
            self.direction = None

    digitalio = types.ModuleType("digitalio")
    digitalio.DigitalInOut = DigitalInOut
    digitalio.Direction = types.SimpleNamespace(OUTPUT=1)

    microcontroller = types.ModuleType("microcontroller")
    microcontroller.reset_count = 0

    def _reset():
        microcontroller.reset_count += 1
        raise SystemExit("microcontroller.reset()")

    microcontroller.reset = _reset

    radio = FakeRadio()
    wifi = types.ModuleType("wifi")
    wifi.radio = radio

    gc_mod = types.ModuleType("gc")
    gc_mod.mem_free = lambda: free_memory
    gc_mod.collect = lambda: None

    hid = types.ModuleType("adafruit_hid")
    keycode = types.ModuleType("adafruit_hid.keycode")

    class Keycode:
        CONTROL = 1
        SHIFT = 2
        ALT = 3
        GUI = 4
        ENTER = 5
        DELETE = 6
        A = 7
        R = 8

    keycode.Keycode = Keycode

    httpserver = types.ModuleType("adafruit_httpserver")
    response = types.ModuleType("adafruit_httpserver.response")
    response.Response = FakeResponse
    response.FileResponse = FakeFileResponse

    for name, module in [
        ("board", board),
        ("digitalio", digitalio),
        ("microcontroller", microcontroller),
        ("wifi", wifi),
        ("gc", gc_mod),
        ("adafruit_hid", hid),
        ("adafruit_hid.keycode", keycode),
        ("adafruit_httpserver", httpserver),
        ("adafruit_httpserver.response", response),
    ]:
        sys.modules[name] = module

    return types.SimpleNamespace(
        board=board,
        radio=radio,
        microcontroller=microcontroller,
        Keycode=Keycode,
        Response=FakeResponse,
        FileResponse=FakeFileResponse,
    )


def instant_clock(core, start=0.0):
    """Replace the module's time so tests do not actually sleep.

    Every sleep advances a fake clock instead, which also lets a test drive
    the serving loop's scheduled WiFi check without waiting a minute.
    """
    state = {"t": start}

    class Clock:
        @staticmethod
        def sleep(seconds):
            state["t"] += seconds

        @staticmethod
        def monotonic():
            return state["t"]

    core.time = Clock
    return state


KEY_MAPPING = {
    "CTRL": 1, "SHIFT": 2, "ALT": 3, "GUI": 4,
    "ENTER": 5, "DELETE": 6, "A": 7, "R": 8,
}
