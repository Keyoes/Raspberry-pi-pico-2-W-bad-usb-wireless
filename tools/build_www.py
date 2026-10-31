#!/usr/bin/env python3
"""Pre-compress the web assets, so the device does not have to.

The page is mostly inline CSS and JavaScript, which compresses to roughly a
fifth of its size. CircuitPython cannot gzip at runtime, so it is done here
and the device just serves the bytes with a Content-Encoding header.

    python3 tools/build_www.py

Run it again after editing any HTML. The .gz files are build output and are
not committed: without them the firmware streams the plain file instead, so
nothing breaks if you never run this.
"""

import gzip
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TARGETS = ["www/index.html", "Mouse_control_test/www/index.html"]


def build(relative_path):
    source = REPO / relative_path
    if not source.exists():
        print(f"  skipped {relative_path} (not found)")
        return False

    destination = source.with_suffix(source.suffix + ".gz")
    raw = source.read_bytes()

    # mtime=0 keeps the output byte-identical between runs for unchanged
    # input, so re-running this does not produce a spurious diff.
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)

    destination.write_bytes(compressed)
    saved = 100 - (100 * len(compressed) // len(raw))
    print(f"  {relative_path}: {len(raw) / 1024:.1f} KB -> "
          f"{len(compressed) / 1024:.1f} KB ({saved}% smaller)")
    return True


def main():
    print("Compressing web assets:")
    built = sum(build(target) for target in TARGETS)

    if not built:
        print("Nothing to do.")
        return 1

    print("\nDone. Copy the .gz next to its .html in the device's /www "
          "directory;\nthe firmware prefers it and falls back to the plain "
          "file when absent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
