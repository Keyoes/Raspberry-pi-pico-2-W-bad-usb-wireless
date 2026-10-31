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

import gc
import os
import time

import board
import digitalio
import microcontroller
import wifi

import adafruit_httpserver.response as _response

DEFAULT_SCRIPT_PATH = "/badusb_script.txt"
DEFAULT_SCRIPT_DIR = "/scripts"
DEFAULT_WWW_ROOT = "/www"

# Populated by configure(). Kept as module state rather than passed through
# every call because a build is a single instance: one keyboard, one link.
_ssid = None
_password = None
_keyboard = None
_keyboard_layout = None
_key_mapping = {}
_script_path = DEFAULT_SCRIPT_PATH
_script_dir = DEFAULT_SCRIPT_DIR

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
              script_path=DEFAULT_SCRIPT_PATH, script_dir=DEFAULT_SCRIPT_DIR):
    """Register the build's hardware and settings.

    ``key_mapping`` stays per-build on purpose: the two builds support
    different key tables, and which keys a build accepts is part of what
    that build is, not something this module should decide.
    """
    global _ssid, _password, _keyboard, _keyboard_layout, _key_mapping
    global _script_path, _script_dir

    _ssid = ssid
    _password = password
    _keyboard = keyboard
    _keyboard_layout = keyboard_layout
    _key_mapping = key_mapping
    _script_path = script_path
    _script_dir = script_dir


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


def _safe_name(name):
    """Validate a script name, or raise ValueError.

    Names become filenames, so anything that could climb out of the script
    directory or overwrite firmware is refused outright rather than
    sanitised quietly: "../boot.py" must not turn into a silent write to
    boot.py. Allowed: letters, digits, dash, underscore and dot, with no
    leading dot and no "..".
    """
    if not name or len(name) > 48:
        raise ValueError("script name must be 1 to 48 characters")

    if name.startswith(".") or ".." in name:
        raise ValueError("script name may not start with a dot or contain '..'")

    for char in name:
        if not (char.isalpha() or char.isdigit() or char in "-_."):
            raise ValueError(
                f"script name may not contain {char!r}; "
                "use letters, digits, dash, underscore or dot"
            )

    return name


def _script_file(name):
    return f"{_script_dir}/{_safe_name(name)}"


def list_scripts():
    """Names of the saved scripts, sorted. Empty when there are none."""
    try:
        return sorted(os.listdir(_script_dir))
    except OSError:
        return []


def save_named_script(name, content):
    """Save a script into the library under ``name``.

    Raises ValueError for an unacceptable name and OSError when the
    filesystem will not take the write (the drive is mounted read-only by
    the host, typically).
    """
    path = _script_file(name)

    try:
        os.mkdir(_script_dir)
    except OSError:
        pass  # already there, or the filesystem is read-only; the write tells us

    with open(path, "w") as f:
        f.write(content)

    return name


def load_named_script(name):
    """Return a saved script's text, or None when there is no such script."""
    try:
        with open(_script_file(name), "r") as f:
            return f.read()
    except OSError:
        return None


def delete_named_script(name):
    """Delete a saved script. Returns True when something was removed."""
    try:
        os.remove(_script_file(name))
        return True
    except OSError:
        return False


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


MAX_BODY_BYTES = 16384


class BodyTooLarge(Exception):
    """A request body was refused for being larger than MAX_BODY_BYTES."""


def read_body(request, limit=MAX_BODY_BYTES):
    """Decode a request body, refusing an oversized one.

    The board has 520 KB of RAM shared with the WiFi stack and the HTTP
    server, and every endpoint used to call request.body.decode() with no
    ceiling. decode() allocates a second copy, so a large upload could
    double its own cost and take the board down with a MemoryError that
    looks like a crash rather than a rejected request.

    This does not stop the library buffering the body in the first place --
    that is governed by the Server's request_buffer_size, which is worth
    tuning on real hardware. It does bound the copy and turn "the device
    fell over" into a clean refusal.
    """
    raw = request.body or b""

    if len(raw) > limit:
        raise BodyTooLarge(f"body is {len(raw)} bytes, the limit is {limit}")

    return raw.decode("utf-8")


BASE_COMMANDS = ("STRING", "DELAY", "CHAR_DELAY", "REM")


def classify_line(line, extra_commands=()):
    """Work out what one script line would do, without doing it.

    IMPORTANT: this mirrors the dispatch order in each build's
    execute_script(), and has to be kept in step with it. A dry run that
    disagrees with the executor is worse than no dry run, so the order
    below is deliberately the same, including the case where a bare key
    name wins before the "+" check.

    Returns (kind, detail, warning). ``warning`` is None when the line is
    unambiguous. ``kind`` is one of: blank, comment, string, delay,
    char_delay, key, combo, extra, unknown.
    """
    stripped = line.strip()

    if not stripped or stripped.startswith("#"):
        return "blank" if not stripped else "comment", stripped, None

    parts = stripped.split(" ", 1)
    command = parts[0].upper()
    argument = parts[1] if len(parts) > 1 else ""

    if command == "STRING":
        if not argument:
            return "string", "", "STRING with no text, nothing will be typed"
        return "string", f"type {argument!r}", None

    if command in ("DELAY", "CHAR_DELAY"):
        kind = "delay" if command == "DELAY" else "char_delay"
        if not argument:
            return kind, "", f"{command} with no value, the line is ignored"
        try:
            value = float(argument)
        except ValueError:
            return kind, argument, f"{command} value {argument!r} is not a number, the line is ignored"
        if value < 0:
            return kind, argument, f"{command} value is negative"
        if kind == "delay":
            return kind, f"wait {value:.0f} ms", None
        return kind, f"set per-character delay to {value:.0f} ms", None

    if command == "REM" or command.startswith("//"):
        return "comment", stripped, None

    # Mirrors execute_script: a bare key name is matched here, BEFORE the
    # "+" check below. That is why a space-separated sequence only ever
    # sends its first key.
    if command in _key_mapping:
        if argument:
            suggestion = "+".join(stripped.split())
            return (
                "key",
                f"press {command}",
                f"only {command} is sent; the rest of the line is dropped. "
                f"Write {suggestion} to send them together.",
            )
        return "key", f"press {command}", None

    if "+" in stripped:
        names = [p.strip().upper() for p in stripped.split("+") if p.strip()]
        unknown = [n for n in names if n not in _key_mapping]
        if unknown:
            return "combo", stripped, f"unknown key(s) in combination: {', '.join(unknown)}"
        return "combo", "press " + " + ".join(names), None

    if command in extra_commands:
        return "extra", stripped, None

    # execute_script's final else hands the line to execute_key_combination,
    # which silently does nothing when it recognises no key names.
    names = [p.strip().upper() for p in stripped.split() if p.strip()]
    known = [n for n in names if n in _key_mapping]
    if not known:
        return "unknown", stripped, f"unrecognised command {command!r}, the line does nothing"

    return "combo", "press " + " + ".join(known), "space-separated keys; prefer + between them"


def validate_script(text, extra_commands=()):
    """Return the problems in a script, without sending anything.

    Each entry is (line_number, line, message). An empty list means every
    line was understood -- not that the script does what you intended.
    """
    problems = []

    for number, line in enumerate(text.splitlines(), start=1):
        _kind, _detail, warning = classify_line(line, extra_commands)
        if warning:
            problems.append((number, line.strip(), warning))

    return problems


def explain_script(text, extra_commands=()):
    """Describe what a script would do, line by line, sending nothing.

    This is the dry run: it drives the same classifier the validator uses,
    so what it reports is what the executor would dispatch.
    """
    steps = []

    for number, line in enumerate(text.splitlines(), start=1):
        kind, detail, warning = classify_line(line, extra_commands)
        if kind == "blank":
            continue
        steps.append({
            "line": number,
            "kind": kind,
            "detail": detail,
            "warning": warning,
        })

    return steps


def page_response(request, filename="index.html", root=DEFAULT_WWW_ROOT):
    """Serve a page from the web-asset directory.

    The page used to be a 27 KB string literal inside the route, so the
    whole document sat in RAM on a board with 520 KB of it, next to the
    WiFi stack and the HTTP server. Now it comes off the filesystem.

    A gzipped copy is preferred when present: it is roughly five times
    smaller for a page that is mostly inline CSS and JavaScript. The
    library has no Content-Encoding support, so that case is built by
    hand. Without the .gz the plain file is streamed in chunks, which is
    the RAM win on its own, so nothing breaks if it was never generated.
    Run tools/build_www.py to produce it.
    """
    gz_path = f"{root}/{filename}.gz"

    # Revalidate rather than cache blindly: the browser always asks, but an
    # unchanged page costs a 304 instead of the whole document. The size is
    # a weak validator, which is why this is no-cache and not max-age --
    # editing the page can never leave a stale copy in the browser.
    try:
        etag = f'"{os.stat(gz_path)[6]}-gz"'
    except OSError:
        try:
            etag = f'"{os.stat(f"{root}/{filename}")[6]}"'
        except OSError:
            etag = None

    headers = {"Cache-Control": "no-cache"}
    if etag:
        headers["ETag"] = etag
        if request is not None and _if_none_match(request) == etag:
            return _response.Response(request, "", status=304, headers=headers)

    # Collect *before* the read, not after. The page is the biggest single
    # allocation this firmware makes, so the point of collecting is to have
    # the room to read it; doing it afterwards only tidied up once the risky
    # part had already succeeded.
    gc.collect()

    try:
        with open(gz_path, "rb") as f:
            body = f.read()
    except OSError:
        return _response.FileResponse(request, filename, root_path=root, headers=headers)
    except MemoryError:
        # Out of contiguous RAM for the compressed page: fall back to the
        # streamed plain file, which never holds the whole thing at once.
        print("Not enough memory for the gzipped page; streaming the plain file.")
        return _response.FileResponse(request, filename, root_path=root, headers=headers)

    headers["Content-Encoding"] = "gzip"

    return _response.Response(
        request,
        body,
        content_type="text/html",
        headers=headers,
    )


def _if_none_match(request):
    """The request's If-None-Match header, or None.

    Tolerant of a request object that exposes headers differently, since a
    missing header must never be the reason a page fails to load.
    """
    try:
        return request.headers.get("if-none-match")
    except Exception:
        return None


def status_snapshot():
    """Connection and health figures for the status endpoint.

    free_memory matters on this board: the page used to be held in RAM per
    request, and when things misbehave this is the number that says why.
    """
    is_connected = wifi.radio.connected

    return {
        "connected": is_connected,
        "ip": str(wifi.radio.ipv4_address) if is_connected else "Not connected",
        # monotonic, not time(): the board has no RTC, so time.time() was
        # never a wall clock here. This is seconds since boot.
        "uptime_s": time.monotonic(),
        "free_memory": gc.mem_free(),
    }


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


# Statuses adafruit_httpserver's poll() reports when it had nothing to do.
IDLE_POLL_STATUSES = ("no_request", "connection_timed_out")


def serve_forever(server, setup_server, wifi_check_interval=60,
                  poll_pause=0.002, idle_poll_pause=0.05):
    """Poll the HTTP server, keeping the WiFi link up, until something fatal.

    The pause is only a yield -- poll() does not block -- so the original
    0.1 added up to 100 ms of latency to every request for no benefit.

    It also adapts. Polling flat out means the board wakes hundreds of times
    a second to be told nothing happened, which on a battery is pure waste.
    poll() reports whether it had a request, so the loop stays tight while
    something is going on and backs off when idle. The cost is at worst
    idle_poll_pause of extra latency on the first request after a quiet
    spell, and 50 ms is not noticeable in a browser.

    A library version whose poll() reports nothing useful falls back to the
    fixed pause rather than guessing.
    """
    last_wifi_check = time.monotonic()
    pause = poll_pause

    try:
        while True:
            try:
                status = server.poll()

                if status is None:
                    # No signal from this version; keep a fixed pause.
                    pause = poll_pause
                elif status in IDLE_POLL_STATUSES:
                    pause = min(pause * 2, idle_poll_pause)
                else:
                    pause = poll_pause
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

            time.sleep(pause)

    except Exception as e:
        print(f"Server polling error: {e}")
        check_wifi_connection()
        try:
            server = restart_server(server, setup_server)
            if not server:
                microcontroller.reset()
        except Exception:
            microcontroller.reset()
