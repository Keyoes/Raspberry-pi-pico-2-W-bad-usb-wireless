#!/usr/bin/env python3
"""Compare the vendored CircuitPython libraries against what is current.

    python3 tools/check_versions.py

`lib/` holds a copy of the Adafruit bundle so the project works out of the
box, which means it goes stale quietly. This reads the version out of each
.mpy, asks PyPI what the current one is, and says how far behind they are.

It also reports the .mpy ABI version, which is the thing that actually
breaks a board: a library built for the wrong one will not import at all.

It changes nothing. Updating means downloading the bundle that matches
your CircuitPython version from circuitpython.org/libraries and copying
the files in yourself.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Vendored path -> PyPI package name.
LIBRARIES = {
    "lib/adafruit_hid/__init__.mpy": "adafruit-circuitpython-hid",
    "lib/adafruit_httpserver/__init__.mpy": "adafruit-circuitpython-httpserver",
    "lib/adafruit_requests.mpy": "adafruit-circuitpython-requests",
    "lib/adafruit_ticks.mpy": "adafruit-circuitpython-ticks",
    "lib/adafruit_connection_manager.mpy": "adafruit-circuitpython-connectionmanager",
}

# APIs this firmware relies on. If a library is updated, these are what to
# re-check before trusting the board -- each one was verified against the
# vendored copy, not assumed.
DEPENDED_ON = {
    "lib/adafruit_httpserver/server.mpy": [
        ("request_buffer_size", "raised from the 1024 default; scripts rely on it"),
        ("no_request", "the idle status the serving loop backs off on"),
    ],
    "lib/adafruit_httpserver/response.mpy": [
        ("FileResponse", "streams the page; must accept content_type and headers"),
    ],
    "lib/adafruit_hid/keyboard.mpy": [
        ("led_status", "the host backchannel /verify depends on"),
    ],
}

VERSION_PATTERN = re.compile(rb"\b(\d+\.\d+\.\d+)\b")


def vendored_version(path):
    """The version string baked into a .mpy, or None."""
    try:
        with open(os.path.join(REPO, path), "rb") as f:
            blob = f.read()
    except OSError:
        return None

    matches = VERSION_PATTERN.findall(blob)
    return matches[0].decode() if matches else None


def mpy_abi(path):
    """The .mpy format version. CircuitPython 9 and 10 both use 6."""
    try:
        with open(os.path.join(REPO, path), "rb") as f:
            header = f.read(2)
    except OSError:
        return None

    if len(header) < 2 or header[0:1] != b"C":
        return None
    return header[1]


def latest_version(package):
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.load(response)["info"]["version"]
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError):
        return None


def as_tuple(version):
    try:
        return tuple(int(part) for part in version.split("."))
    except (AttributeError, ValueError):
        return ()


def main():
    print("Vendored libraries in lib/\n")
    print(f"  {'library':<34} {'here':>10} {'current':>10}   status")
    print(f"  {'-' * 34} {'-' * 10} {'-' * 10}   ------")

    behind = []
    unreachable = False

    for path, package in LIBRARIES.items():
        here = vendored_version(path) or "?"
        current = latest_version(package)

        if current is None:
            unreachable = True
            status = "could not reach PyPI"
        elif here == current:
            status = "up to date"
        elif as_tuple(here)[:2] != as_tuple(current)[:2]:
            status = "behind, minor version differs"
            behind.append((package, here, current, True))
        else:
            status = "behind, patches only"
            behind.append((package, here, current, False))

        name = path.replace("lib/", "").replace("/__init__.mpy", "")
        print(f"  {name:<34} {here:>10} {current or '?':>10}   {status}")

    abis = {mpy_abi(path) for path in LIBRARIES}
    abis.discard(None)
    print(f"\n  .mpy ABI version: {', '.join(str(a) for a in sorted(abis)) or 'unknown'}")
    if abis == {6}:
        print("  ABI 6 is what CircuitPython 9 and 10 both read, so these load "
              "on either.")
    elif len(abis) > 1:
        print("  Mixed ABI versions: these did not come from one bundle, and "
              "some will fail to import.")

    if behind:
        print("\nTo update: download the bundle matching your CircuitPython "
              "version\nfrom https://circuitpython.org/libraries and copy the "
              "files into lib/.")

        if any(is_minor for *_rest, is_minor in behind):
            print("\nA minor version moved, so re-check the APIs this firmware "
                  "relies on\nbefore trusting a board with it:\n")
            for path, entries in DEPENDED_ON.items():
                for symbol, why in entries:
                    present = symbol.encode() in open(
                        os.path.join(REPO, path), "rb").read()
                    mark = "present" if present else "MISSING"
                    print(f"    {symbol:<22} {mark:<8} {why}")
            print("\n  (checked against the copy in lib/ right now; run this "
                  "again after\n   updating and anything that reads MISSING "
                  "will break the firmware)")
    elif not unreachable:
        print("\nEverything matches the current release.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
