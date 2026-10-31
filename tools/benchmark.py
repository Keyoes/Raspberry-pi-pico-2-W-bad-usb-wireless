#!/usr/bin/env python3
"""Measure the device's HTTP side, on the real board.

    python3 tools/benchmark.py http://192.168.1.100

Every performance figure in the README was worked out from the code --
arithmetic on constants, or measurements against a stub. None of it was
taken from a Pico. This points at a running board and measures the same
things for real, so the claims can be checked rather than trusted.

It also runs against tests/ui/mock_device.py, which is useful for checking
the benchmark itself but says nothing about the hardware.

What it does not measure: anything to do with sending keystrokes. This
exercises the web interface only.

Needs nothing outside the standard library.
"""

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request


def request(url, data=None, headers=None, timeout=10):
    """Send one request and return (seconds, status, body, headers)."""
    req = urllib.request.Request(url, data=data, headers=headers or {})
    if data is not None:
        req.add_header("Content-Type", "text/plain")

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            elapsed = time.perf_counter() - start
            return elapsed, response.status, body, dict(response.headers)
    except urllib.error.HTTPError as e:
        body = e.read()
        return time.perf_counter() - start, e.code, body, dict(e.headers)


def ms(seconds):
    return f"{seconds * 1000:.0f} ms"


def heading(text):
    print(f"\n{text}\n{'-' * len(text)}")


def free_memory(base):
    try:
        _t, _s, body, _h = request(f"{base}/wifi-status?t={time.time()}")
        return json.loads(body).get("free_memory")
    except Exception:
        return None


def bench_page(base):
    heading("Page")

    elapsed, status, body, headers = request(f"{base}/")
    encoding = headers.get("Content-Encoding", "none")
    etag = headers.get("ETag")
    print(f"  first load        {ms(elapsed):>10}  {len(body):>7} bytes  "
          f"encoding: {encoding}")

    if encoding != "gzip":
        print("    (not gzipped: run tools/build_www.py and copy the .gz "
              "to the device's /www)")

    if not etag:
        print("    (no ETag, so every reload re-sends the page)")
        return

    elapsed, status, body, _h = request(f"{base}/", headers={"If-None-Match": etag})
    if status == 304:
        print(f"  unchanged reload  {ms(elapsed):>10}  {len(body):>7} bytes  "
              f"(304, page not re-sent)")
    else:
        print(f"    (expected 304 for an unchanged page, got {status})")


def bench_latency(base, count):
    heading(f"Status endpoint latency, {count} requests")

    times = []
    for _ in range(count):
        elapsed, status, _b, _h = request(f"{base}/wifi-status?t={time.time()}")
        if status == 200:
            times.append(elapsed)

    if not times:
        print("  no successful responses")
        return

    times.sort()
    print(f"  fastest           {ms(times[0]):>10}")
    print(f"  median            {ms(statistics.median(times)):>10}")
    print(f"  slowest           {ms(times[-1]):>10}")
    print("\n  The serving loop backs off to a 100 ms pause when idle and")
    print("  tightens to 2 ms once requests arrive, so the first request")
    print("  after a quiet spell is the slow one and the rest should not be.")


def bench_memory(base):
    heading("Free memory around a page load")

    before = free_memory(base)
    if before is None:
        print("  endpoint did not report free_memory")
        return

    request(f"{base}/")
    after = free_memory(base)

    print(f"  before            {before:>10,} bytes")
    print(f"  after             {after:>10,} bytes")
    print(f"  difference        {after - before:>+10,} bytes")
    print("\n  The page is streamed rather than held in RAM, so this should")
    print("  be close to zero. A large drop means something is holding it.")


def bench_validate(base):
    heading("Script checking, by script length")

    for lines in (1, 10, 50, 200):
        script = "\n".join(["STRING hello"] * lines)
        elapsed, status, body, _h = request(
            f"{base}/validate", data=script.encode()
        )
        if status == 413:
            print(f"  {lines:>4} lines       refused (413, over the body limit)")
            continue
        if status != 200:
            print(f"  {lines:>4} lines       HTTP {status}")
            continue
        print(f"  {lines:>4} lines  {ms(elapsed):>10}  "
              f"({len(script):>5} bytes)")


def bench_body_limit(base):
    heading("Largest script the device accepts")

    accepted = 0
    for size in (512, 1024, 2048, 3072, 4096, 8192):
        script = "S" * size
        _t, status, _b, _h = request(f"{base}/validate", data=script.encode())
        verdict = {200: "accepted", 413: "refused (413)"}.get(status, f"HTTP {status}")
        print(f"  {size:>5} bytes      {verdict}")
        if status == 200:
            accepted = size
        elif status != 413:
            print("    (neither accepted nor a clean refusal: the request "
                  "buffer may be truncating it)")
            break

    print(f"\n  Largest accepted here: {accepted} bytes.")
    print("  If that is well under 3072, the server's request_buffer_size")
    print("  is the limit, not MAX_BODY_BYTES. Both are named constants;")
    print("  see the README's request size section.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="base URL of the device, e.g. http://192.168.1.100")
    parser.add_argument("--requests", type=int, default=20,
                        help="how many requests for the latency run (default 20)")
    args = parser.parse_args()

    base = args.url.rstrip("/")

    print(f"Benchmarking {base}")
    try:
        _t, status, _b, _h = request(f"{base}/wifi-status", timeout=5)
    except Exception as e:
        print(f"\nCould not reach the device: {e}")
        return 1
    if status != 200:
        print(f"\nDevice answered /wifi-status with HTTP {status}; is this the right URL?")
        return 1

    bench_page(base)
    bench_latency(base, args.requests)
    bench_memory(base)
    bench_validate(base)
    bench_body_limit(base)

    print("\nThis measures the web interface only. Nothing here touches "
          "keystroke sending.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
