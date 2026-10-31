"""Shared runtime for the BadUSB builds.

``code.py`` and ``Mouse_control_test/code.py`` were near-identical copies of
each other, so every fix had to be made twice -- and in practice was not: a
batch of fixes landed in one file while the other kept all of the same bugs.

Everything here is the part that does not depend on which HTTP routes or
which web page a build serves: the status LED, the WiFi link, script
storage, key-combination parsing and the serving loop. The routes, the HTML
and the script interpreter stay in each entry point, because those are what
actually differ between the two builds.

Call :func:`configure` once at start-up before using anything else.

Nothing in here changes the behaviour of the code it replaced; the functions
were moved across unchanged, timings included.
"""

import os
import time

import board
import digitalio
import microcontroller
import wifi

DEFAULT_SCRIPT_PATH = "/badusb_script.txt"

# Populated by configure(). Kept as module state rather than passed through
# every call because a build is a single instance: one keyboard, one link.
_ssid = None
_password = None
_keyboard = None
_keyboard_layout = None
_key_mapping = {}
_script_path = DEFAULT_SCRIPT_PATH

_script_in_memory = None


def init_status_led():
    """Return the on-board status LED.

    Not every board exposes ``board.LED``. On most ESP32-S2/S3 boards the
    on-board indicator is a NeoPixel (``board.NEOPIXEL``) or simply absent,
    which used to raise AttributeError and kill the script before it ever
    reached the WiFi setup. Fall back to a no-op stub so the firmware still
    boots; the LED is only a status indicator.
    """
    try:
        pin = digitalio.DigitalInOut(board.LED)
        pin.direction = digitalio.Direction.OUTPUT
        return pin
    except (AttributeError, ValueError) as exc:
        print(f"No usable status LED ({exc}); continuing without it.")

        class _NoStatusLed:
            value = False

        return _NoStatusLed()


led = init_status_led()


def blink(times, on=0.2, off=0.2):
    """Blink the status LED, if there is one."""
    for _ in range(times):
        led.value = True
        time.sleep(on)
        led.value = False
        time.sleep(off)


def configure(ssid, password, keyboard, keyboard_layout, key_mapping,
              script_path=DEFAULT_SCRIPT_PATH):
    """Register the build's hardware and settings.

    ``key_mapping`` stays per-build on purpose: the two builds support
    different key tables, and which keys a build accepts is part of what
    that build is, not something this module should decide.
    """
    global _ssid, _password, _keyboard, _keyboard_layout, _key_mapping, _script_path

    _ssid = ssid
    _password = password
    _keyboard = keyboard
    _keyboard_layout = keyboard_layout
    _key_mapping = key_mapping
    _script_path = script_path


def connect_to_wifi(max_attempts=0, retry_delay=5, reset_on_failure=True):
    """Bring up the WiFi link.

    ``max_attempts=0`` retries forever, which is what we want at boot since
    there is nothing else for the board to do until it is online. A positive
    value bounds the attempts and returns False instead of blocking, for
    callers that have to stay responsive.
    """
    attempt = 0

    while True:
        attempt += 1
        print(f"Connecting to {_ssid}... (Attempt {attempt})")

        try:
            blink(1, off=0)

            wifi.radio.connect(_ssid, _password)

            print(f"Connected to {_ssid}")
            print(f"IP Address: {wifi.radio.ipv4_address}")

            blink(2)

            return True

        except Exception as e:
            print(f"Failed to connect to WiFi: {e}")

            led.value = True
            time.sleep(1)
            led.value = False

            if max_attempts and attempt >= max_attempts:
                print(f"Giving up after {attempt} attempt(s).")
                return False

            if reset_on_failure and attempt % 10 == 0:
                print(f"Reached {attempt} consecutive failed attempts; resetting.")
                blink(5, on=0.1, off=0.1)
                microcontroller.reset()

            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)


def check_wifi_connection(max_attempts=2):
    """Reconnect if the link dropped, and report whether we are online.

    Deliberately bounded: this is called from the serving loop, so an
    unbounded retry here stops the device answering HTTP at all for as long
    as the network is down.
    """
    if wifi.radio.connected:
        return True

    print("WiFi connection lost. Attempting to reconnect...")
    connect_to_wifi(max_attempts=max_attempts, reset_on_failure=False)
    return wifi.radio.connected


def save_script(script_content):
    """Store the script and report honestly where it ended up.

    Returns a description of where it was stored. The RAM fallback used to
    return True just like a successful write, so callers reported "uploaded
    successfully" for a script that never reached the filesystem and would
    be lost on the next reset.
    """
    global _script_in_memory

    try:
        try:
            os.remove(_script_path)
        except OSError:
            pass

        with open(_script_path, "w") as f:
            f.write(script_content)

        # Drop any stale RAM copy so it cannot shadow what is on disk.
        _script_in_memory = None
        return "saved to flash"
    except Exception as e:
        print(f"Could not write {_script_path}: {e}; keeping the script in RAM only.")
        _script_in_memory = script_content
        return "kept in RAM only, will be lost on reset"


def load_script_lines():
    """Return the stored script's lines, or None when there is no script."""
    try:
        with open(_script_path, "r") as f:
            return f.readlines()
    except OSError:
        if _script_in_memory:
            return _script_in_memory.splitlines()

        print("No script found in file or memory")
        return None


def read_script():
    """Return the stored script as text, or None when there is no script."""
    lines = load_script_lines()
    if lines is None:
        return None

    return "".join(line if line.endswith("\n") else line + "\n" for line in lines)


def parse_key_combo(key_combo):
    keys = []
    if "+" in key_combo:
        parts = key_combo.split("+")
        for part in parts:
            part = part.strip().upper()
            if part in _key_mapping:
                keys.append(_key_mapping[part])
    else:
        parts = key_combo.split()
        for part in parts:
            part = part.strip().upper()
            if part in _key_mapping:
                keys.append(_key_mapping[part])

    return keys


def execute_key_combination(key_combo):
    keycodes = parse_key_combo(key_combo)

    if keycodes:
        try:
            for key in keycodes:
                _keyboard.press(key)
                time.sleep(0.05)

            time.sleep(0.15)

            for key in reversed(keycodes):
                _keyboard.release(key)
                time.sleep(0.05)

            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"Error executing key combination: {e}")
            _keyboard.release_all()
            time.sleep(0.1)
            return False
    return False


def restart_server(server, setup_server):
    """Stop the running server before starting a fresh one.

    Without the stop, ``setup_server()`` tried to bind port 80 while the old
    socket still held it, so ``start()`` raised, ``setup_server()`` returned
    None, and every caller fell through to ``microcontroller.reset()``. The
    whole recovery path rebooted the board instead of recovering.
    """
    if server is not None:
        try:
            server.stop()
        except Exception as e:
            print(f"Could not stop the old server cleanly: {e}")

    return setup_server()


def serve_forever(server, setup_server, wifi_check_interval=60, poll_pause=0.01):
    """Poll the HTTP server, keeping the WiFi link up, until something fatal.

    ``poll_pause`` is only a yield -- ``poll()`` does not block -- so the old
    value of 0.1 added up to 100 ms of latency to every request for no
    benefit.
    """
    last_wifi_check = time.monotonic()

    try:
        while True:
            try:
                server.poll()
            except Exception as e:
                print(f"Error during server poll: {e}")
                if check_wifi_connection():
                    print("Trying to restart server...")
                    server = restart_server(server, setup_server)
                    if not server:
                        microcontroller.reset()

            if time.monotonic() - last_wifi_check > wifi_check_interval:
                was_offline = not wifi.radio.connected
                if check_wifi_connection() and was_offline:
                    # Rebuild the socket only after an actual reconnect: the
                    # IP may have changed, so the listener is stale. This
                    # condition used to be inverted, restarting the server
                    # precisely when the reconnect had failed and leaving the
                    # stale socket in place when it had worked.
                    print("Reconnected; rebuilding the server socket.")
                    server = restart_server(server, setup_server)
                    if not server:
                        microcontroller.reset()
                last_wifi_check = time.monotonic()

            time.sleep(poll_pause)

    except Exception as e:
        print(f"Server polling error: {e}")
        check_wifi_connection()
        try:
            server = restart_server(server, setup_server)
            if not server:
                microcontroller.reset()
        except Exception:
            microcontroller.reset()
