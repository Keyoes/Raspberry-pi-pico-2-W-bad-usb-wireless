# KEYOES BadUSB Controller

A powerful BadUSB controller for Raspberry Pi Pico 2 W with a web interface for remote payload management.

## 🔥 Features

- **Web-based interface** for uploading and executing BadUSB payloads
- **WiFi connectivity** for remote control
- **Persistent connection** - The device will automatically reconnect to WiFi if the connection is lost
- **Fully responsive design** for both mobile and desktop devices
- **Enhanced keyboard simulation** with improved timing control
- **Command history** in the browser for the current session (it is held in
  the page, not on the device, so a reload clears it)
- **Script library** on the device, with save, load and delete
- **Validation and dry run** that inspect a script without sending keystrokes
- **Kali Linux-inspired terminal UI** with modern cybersecurity aesthetics
- **RESTful API** for programmatic control
- **Keyboard support** for EN (US) layout

## ⚠️ If you are updating from an earlier version

The layout changed, and copying `code.py` alone is no longer enough. The
board will not start without all three:

| | where it goes on the device |
|---|---|
| `code.py`, `boot.py` | the root of CIRCUITPY, as before |
| `lib/badusb_core.py` | `lib/`, next to the Adafruit libraries |
| `www/index.html` | a new `www/` directory |

`badusb_core.py` holds the code both builds share, so a fix lands once
instead of twice. The page moved out of `code.py` into `www/` so it is no
longer a 27 KB string the board has to hold in RAM for every request.

Optionally run `python3 tools/build_www.py` and copy the generated
`www/index.html.gz` as well; it is about 80% smaller and the firmware
prefers it, falling back to the plain file when it is absent.

### What else changed

- The recovery path now recovers. A dropped WiFi link used to end in a
  reboot, because the server was restarted without releasing port 80
  first, and the scheduled check had its condition inverted.
- Uploads report where the script actually went. A write that failed and
  fell back to RAM used to answer "uploaded successfully".
- Scripts can be checked before they run, with `/validate` and `/dry-run`
  and the CHECK and DRY RUN buttons. Neither sends a keystroke. Among
  other things they catch `CTRL ALT DELETE`, which only ever sent Ctrl.
- Longer scripts work. The server's request buffer was left at the
  library's 1024-byte default, so anything much over a kilobyte never
  reached the handler.
- The page keeps its terminal background effect, which the boot animation
  used to delete about 100 ms after load, and no longer wipes a command's
  output during the first 2.4 seconds.
- Start-up takes 0.78 s instead of 2.20 s before the first request.

Everything here was verified in simulation and by a browser test, not on
hardware. See **Running the tests**.

## 📋 Prerequisites

Before getting started, you'll need:

- Raspberry Pi Pico 2 W
- Micro USB cable
- Computer with CircuitPython installation capability

## 🛠️ Installation Guide

### Step 1: Install CircuitPython on your Pico

#### Removing Existing Firmware (if necessary)

If your Raspberry Pi Pico 2 W already has MicroPython or other firmware installed:

1. Download the reset utility for Raspberry Pi Pico 2 W (flash_nuke.uf2)
2. Press and hold the BOOTSEL button while connecting the Pico to your computer
3. Release the button once connected
4. Your Pico should mount as a USB drive named "RPI-RP2"
5. Drag and drop the flash_nuke.uf2 file onto the RPI-RP2 drive
6. The Pico will automatically restart, erasing its memory completely
7. After a brief pause, it will remount as "RPI-RP2" again, ready for new firmware

#### Installing CircuitPython

1. Press and hold the **BOOTSEL** button on your Raspberry Pi Pico 2 W
2. While holding the button, connect the Pico to your computer via USB
3. Release the button once connected
4. Your Pico should mount as a USB drive named "RPI-RP2"
5. Download the latest [CircuitPython UF2 file for Raspberry Pi Pico 2 W](https://circuitpython.org/board/raspberry_pi_pico2_w/)
6. Drag and drop the .UF2 file onto the RPI-RP2 drive
7. The Pico will automatically restart and mount as a new drive named "CIRCUITPY"

### Step 2: Install Required Libraries

1. Download the CircuitPython library bundle that matches your CircuitPython version from the [CircuitPython libraries page](https://circuitpython.org/libraries)
2. Extract the bundle and copy the following libraries to the `lib` folder on your CIRCUITPY drive:
   - adafruit_hid (folder)
   - adafruit_httpserver (folder)
   - adafruit_requests.mpy
   - adafruit_ticks.mpy
   - adafruit_connection_manager.mpy

3. Copy `badusb_core.py` from this repository's `lib` folder to the `lib`
   folder on your CIRCUITPY drive. This one is not part of the Adafruit
   bundle: it is this project's own shared code, used by both builds, and
   `code.py` will not start without it.

### Step 3: Copy the Code Files

1. Create `boot.py` in the root of your CIRCUITPY drive and copy the code from the provided boot.py file
2. Create `code.py` in the root of your CIRCUITPY drive and copy the code from the provided code.py file
3. Create a `www` directory in the root of your CIRCUITPY drive and copy
   `www/index.html` into it. The web page is served from there rather than
   being embedded in `code.py`, so it does not have to sit in RAM on every
   request.

   Optionally, run `python3 tools/build_www.py` first and copy the generated
   `www/index.html.gz` as well. It is about 80% smaller and the firmware
   prefers it; without it the plain file is streamed instead.
4. Edit the WiFi credentials in `code.py`:
   ```python
   WIFI_SSID = "YourWiFiName"
   WIFI_PASSWORD = "YourWiFiPassword"
   ```

### Step 4: Safe Ejection and First Boot

1. Safely eject the CIRCUITPY drive
2. Disconnect and reconnect your Pico
3. The device will boot and run the BadUSB controller script

#### LED Status Indicators
- **3 quick blinks at start**: System initialization
- **Rapid blinking (10 times)**: WiFi connection failed
- **One longer blink**: Server started successfully
- **5 quick blinks**: Server failed to start
- **LED on during command execution**: Command being executed

The start-up and server-ready signals are deliberately brief. They used to
hold the board for 2.2 seconds in total before it could answer its first
request, which is now 0.78 seconds for the same sequence.

## 📱 Connecting to the Web Interface

1. Connect your Raspberry Pi Pico 2 W to a USB power source
2. The device will connect to your configured WiFi network
3. Find the IP address of your device:
   - Check your router's connected devices list
   - Use an IP scanner on your network
4. Open a web browser and navigate to the IP address (e.g., `http://192.168.1.100`)
5. The KEYOES BadUSB Controller interface should load, featuring a sleek Kali Linux-inspired terminal design

## 💻 Using the Controller

### Web Interface

The web interface provides a sophisticated terminal-like experience with the following features:

- **Script Editor**: A central textarea for writing or pasting your BadUSB scripts
- **Upload Button**: Saves the script to the device without executing it
- **Execute Button**: Runs the saved script through the connected USB interface
- **Clear Button**: Erases the script editor content
- **Command History**: Shows previously executed commands and their status
- **Payloads Log**: Records executed payloads with timestamps (accessed via the "Payloads Log" tab)

### Script Syntax

The BadUSB controller supports an extended version of the Ducky Script language:

```
STRING <text>           # Types the specified text
DELAY <milliseconds>    # Waits for the specified time in milliseconds
CHAR_DELAY <ms>         # Sets the delay between keystrokes (default: 10ms)
REM <comment>           # Comment (not executed)
// <comment>            # Alternative comment syntax

# Key commands
<key>                   # Presses a single key (e.g., ENTER, SPACE, TAB)
<key1>+<key2>+<key3>    # Presses a key combination (e.g., CTRL+ALT+T)
```

#### Supported Special Keys

The controller supports a comprehensive range of keys including:

- Modifiers: `CTRL`, `SHIFT`, `ALT`, `GUI` (Windows/Command key)
- Function keys: `F1` through `F12`
- Navigation: `UP`, `DOWN`, `LEFT`, `RIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN`
- System keys: `ESC`, `TAB`, `CAPSLOCK`, `PRINTSCREEN`, `DELETE`, etc.

### Example Script

```
REM Open command prompt in Windows
GUI+r
DELAY 500
STRING cmd
ENTER
DELAY 1000
STRING echo Hello, this is a BadUSB example!
ENTER
```

### Checking a script before running it

Two endpoints inspect a script without sending a single keystroke. Both take
the script as the request body.

`POST /validate` reports what is wrong with it:

```json
{
  "ok": false,
  "problems": [
    {"line": 2, "text": "CTRL ALT DELETE",
     "message": "only CTRL is sent; the rest of the line is dropped. Write CTRL+ALT+DELETE to send them together."}
  ]
}
```

That particular warning is worth knowing about: a space-separated key
sequence only ever sends its first key, because a bare key name is matched
before the `+` form is considered. The validator also catches unknown
commands, which otherwise fail silently, and `DELAY` values that are not
numbers.

`POST /dry-run` describes what the script would do, line by line. With an
empty body it describes the script currently stored on the device, so you
can check what is loaded before firing it:

```json
{"steps": [{"line": 1, "kind": "string", "detail": "type 'hello'", "warning": null}]}
```

### Script library

The device keeps one active script, which is what `/execute` runs, plus a
library of saved ones.

```
GET  /scripts                      -> {"scripts": ["recon", "setup-demo"]}
POST /scripts  {"action": "save",   "name": "recon", "script": "..."}
POST /scripts  {"action": "load",   "name": "recon"}   # makes it the active script
POST /scripts  {"action": "delete", "name": "recon"}
```

Names may contain letters, digits, dash, underscore and dot, up to 48
characters. Anything else is refused rather than quietly rewritten, so a
name like `../boot.py` cannot reach outside the script directory.

### Request size limit

Scripts are capped at 3 KB, and anything larger gets a `413`.

That ceiling is not arbitrary. `adafruit_httpserver` buffers an incoming
request into `Server.request_buffer_size`, which
[defaults to 1024 bytes](https://docs.circuitpython.org/projects/httpserver/en/latest/api.html)
and holds the headers too, so before this was set explicitly a script much
over a kilobyte never reached the handler at all. Both builds now set it to
4096 and cap bodies at 3072, leaving room for headers.

To allow longer scripts, raise `REQUEST_BUFFER_SIZE` in the build's
`code.py` and `MAX_BODY_BYTES` in `lib/badusb_core.py` together, keeping
the body limit below the buffer. The buffer costs that many bytes of RAM
for as long as the server runs, so it is a trade against everything else
on a 520 KB board, not a free win.

### Device status

`GET /wifi-status` reports the link, the uptime and the free memory:

```json
{"connected": true, "ip": "192.168.1.100", "uptime_s": 1423.8, "free_memory": 164512}
```

`free_memory` is worth watching on this board. It has 520 KB of RAM shared
between the WiFi stack, the HTTP server and everything else, and it is the
number that explains most odd behaviour.

### API Access

For programmatic control, you can use the RESTful API endpoint:

```
POST http://<pico-ip>/api/badusb
```

With JSON payload for uploading a script:
```json
{
  "action": "upload",
  "script": "STRING Hello World\nDELAY 500\nENTER"
}
```

For executing a previously uploaded script:
```json
{
  "action": "execute"
}
```

You can also send a raw script as the request body to upload and immediately execute it:
```
POST http://<pico-ip>/api/badusb
Content-Type: text/plain

STRING Hello World
DELAY 500
ENTER
```

### WiFi Status Monitoring

The web interface includes a real-time WiFi status indicator that shows:
- Connection status (connected/disconnected)
- Current IP address
- Connection losses or timeout issues

You can also query the WiFi status programmatically:
```
GET http://<pico-ip>/wifi-status
```

## Payload Development Best Practices

### Timing Optimization

Fine-tune your attack payloads with strategic timing for maximum reliability:

```
CHAR_DELAY 30    # IMPORTANT: Minimum recommended delay for reliable keystroke registration
STRING cd /tmp && mkdir test
ENTER
DELAY 500        # Allow system time to process command before continuing
```

### Target-Specific Adaptations

Adjust your payloads based on the target operating system:

- **Windows**: Use `GUI+r` to open Run dialog, then execute commands
- **macOS**: Use `GUI+SPACE` to open Spotlight, then launch applications
- **Linux**: Use `CTRL+ALT+T` to open terminal on many distributions

### Multi-phase Payloads

For complex attacks, structure your payloads into logical phases:

```
REM Phase 1: Establish access
GUI+r
DELAY 200
STRING cmd.exe
ENTER
DELAY 500

REM Phase 2: Execute primary payload
STRING echo Executing primary payload...
ENTER
```

## Known Issues

### Dropped characters: why they happened, and what changed

Characters used to go missing during a payload, more often with a low
`CHAR_DELAY`, and the usual advice was to raise it to 30 ms. That treated
the symptom. The cause was elsewhere.

USB HID is polled by the host once per 1 ms frame, and the device is never
told whether a report was read. `adafruit_hid` presses a key and calls
`release_all()` immediately, with nothing in between, so when both reports
land between two polls the host reads the endpoint once, sees nothing
held, and the character never existed as far as it is concerned. It was
not dropped in transit — it was overwritten before anyone looked.

`CHAR_DELAY` could not fix this, because it is the pause *between*
characters; the press and release within one character stayed back to
back. Neither could the `delay` argument to `write()`, which sleeps after
`release_all()` for the same reason.

The keyboard now holds each key for `KEY_HOLD_SECONDS` (4 ms, four poll
frames) before releasing it, by wrapping `release_all()` so the library
keeps ownership of the keycode, shift and AltGr handling.

That hold costs nothing in throughput, because it comes **out of**
`CHAR_DELAY` rather than on top of it. What paces the target is the
character rate, not where the time sits inside each character:

| | period per character | key held |
|---|---|---|
| before | `CHAR_DELAY` | 0 ms — the host can miss it |
| hold added on top | `CHAR_DELAY` + 4 ms | 4 ms, but 40% slower |
| what it does now | `CHAR_DELAY` | 4 ms, same rate as before |

With `CHAR_DELAY` below 4 ms there is nothing left to subtract and the
hold becomes the floor, so very short delays give roughly 4 ms per
character. Getting 4 ms when you asked for 1 ms is the honest outcome;
getting nothing typed was the old one.

`tests/test_badusb_core.py` checks both halves: a simulated host polling
at 1 ms misses the key without the hold and sees it across several frames
with it, and typing five characters still takes five character delays.

Set `KEY_HOLD_SECONDS = 0` in `lib/badusb_core.py` for the old behaviour.
Raising `CHAR_DELAY` is still worth doing on a slow or loaded target — it
paces the host's input handling, which is a different bottleneck from the
polling one.

There is no per-keystroke acknowledgement. USB HID does not give the
device one, so nothing can confirm that a particular character landed.

There is, however, exactly one backchannel: the host sends the device its
keyboard LED state. `POST /verify`, and the **VERIFY HOST** button, press
Num Lock, wait for that state to come back changed, and press it again so
the target ends as it started. If it comes back, the host received a
keystroke, acted on it and reported the result — end to end, for real.

That tells you the channel works, not that a given character arrived. It
is a pre-flight check, not something to run per keystroke: it costs a
round trip and it blinks a light on the user's keyboard.

```json
{"ok": true,  "message": "host acknowledged a keystroke",
 "round_trip_s": 0.012, "suggested_char_delay_ms": 12}
{"ok": false, "message": "no response from the host within 0.5s; keystrokes are probably not arriving"}
{"ok": null,  "message": "this build does not report LED state (...)"}
```

`round_trip_s` is how long that machine took to process a key and report
back, and `suggested_char_delay_ms` is a starting point derived from it:
a host that answers slowly is a host that drops characters sooner, so
pace to it instead of guessing. It is a rule of thumb, floored at the key
hold since nothing below that is achievable.

It does **not** reveal the host's keyboard layout, and no timing can. The
device sends scancodes; the layout is the mapping the host applies after
they arrive, and it is identical in timing whichever layout is set. Two
machines, one US and one Romanian, are indistinguishable from here.

`ok: null` means the answer is not knowable, which is not the same as a
failure, and the UI says so differently.

Relatedly, `/execute` now refuses with a `503` when no USB host is
attached. Running a payload into a charger, or into nothing, used to
report that it had executed successfully.

This is also the clearest reason a rewrite in a faster language would not
help here: it would push the two reports closer together and lose more
characters, not fewer.

### Space-separated key combinations only send their first key

`CTRL ALT DELETE` presses Ctrl and drops the rest. The interpreter matches
a bare key name before it considers the `+` form, so the remainder of the
line never gets looked at. Write `CTRL+ALT+DELETE`.

`/validate` and the CHECK button report this, with the corrected line, so
you do not have to remember it.

### MOUSE_MOVE and MOUSE_DRAG undershoot

Both split the movement into steps and truncate each one with `int()`, so
the leftover fraction is lost on every step and the pointer always lands
short, never past. A 199 px move arrives at 190 px, about 5%. Smaller and
round distances are usually exact; the error is worst at values that do
not divide evenly.

### Keyboard layout is EN (US) only

Only `keyboard_layout_us.mpy` ships in `lib/`, so `STRING` produces the
wrong characters on any other physical layout.

### Saving scripts needs a writable filesystem

`boot.py` calls `storage.disable_usb_drive()`, which is what lets the board
write to its own filesystem. If you have undone that to edit the code — see
**Safely Editing the Python Code** — saved scripts fall back to RAM and are
lost on reset. The upload response says which happened rather than
reporting success either way.

### The web interface has no authentication

Anyone who can reach the device on the network can upload and run a
payload. There is no login, and `adafruit_httpserver` ships a `Basic`
helper that would close this. Worth doing before putting the device on a
network you do not control.

## Keyboard Shortcuts

The web interface supports several keyboard shortcuts:
- `Ctrl+T`: Switch to Terminal tab
- `Ctrl+P`: Switch to Payloads Log tab
- `Ctrl+Enter`: Execute current script
- `Ctrl+S`: Upload current script

## Safely Editing the Python Code

To edit the `code.py` file without risking automatic execution:

1. Enter BOOTSEL mode (hold the BOOTSEL button when connecting the device)
2. Temporarily modify the `boot.py` file to prevent automatic execution:
   ```python
   # Comment out these lines to disable keyboard simulation
   # usb_cdc.disable()
   # storage.disable_usb_drive()
   
   # Add this line to enable USB drive mode
   storage.enable_usb_drive()
   ```
3. Save the changes and safely eject
4. Now when you connect the Pico normally, it will mount as a storage device
5. Edit `code.py` as needed
6. Remember to revert the `boot.py` changes when finished

While `boot.py` is in this state the board cannot write to its own
filesystem, so anything the device tries to save — the active script, the
script library — stays in RAM and is lost on reset. The upload response
says so rather than claiming success, but it is easy to forget why.

A GPIO jumper read at boot is a tidier way to do this than editing
`boot.py` back and forth, if you find yourself doing it often.

## Technical Details

### Key Mapping System
The device uses a comprehensive key mapping system that translates string commands to USB HID keycodes:

```python
KEY_MAPPING = {
    "CTRL": Keycode.CONTROL, "SHIFT": Keycode.SHIFT, "ALT": Keycode.ALT,
    "GUI": Keycode.GUI, "WINDOWS": Keycode.GUI, "WIN": Keycode.GUI,
    # ... additional mappings for all supported keys
}
```

### Project layout

```
code.py                      keyboard build: routes and the script interpreter
Mouse_control_test/code.py   same, plus mouse commands
lib/badusb_core.py           shared: LED, WiFi, storage, validation, serving loop
www/index.html               the web page, served from the device's /www
tools/build_www.py           pre-compresses the page to .html.gz
tools/check_versions.py      vendored libraries vs current releases
tests/                       runs on a desktop, no board required
tests/boot_simulation.py     executes both builds against stubs
.github/workflows/tests.yml  runs all of it on every push
```

The two builds were near-identical copies, so a fix had to be made twice and
in practice was not. Everything that does not depend on which routes or which
page a build serves now lives in `lib/badusb_core.py`. What stays per build is
the page, the routes, the script interpreter and `KEY_MAPPING` — the mouse
build supports a larger key table, and which keys a build accepts is part of
what that build is.

### WiFi reconnection

`connect_to_wifi()` retries indefinitely at boot, since there is nothing else
for the board to do until it is online, and resets after ten consecutive
failures. The serving loop instead calls `check_wifi_connection()`, which is
bounded: an unbounded retry there would stop the device answering HTTP for as
long as the network was down.

After a successful reconnect the listening socket is rebuilt, because the IP
may have changed. The restart stops the old server first — otherwise the new
one cannot bind port 80 and the board reboots instead of recovering.

### Script storage

The active script is written to the filesystem. If that write fails, usually
because the host has the drive mounted and CircuitPython cannot write to it,
it is kept in RAM instead and the response says so rather than reporting
success:

```python
detail = badusb_core.save_script(content)
# -> "saved to flash"  or  "kept in RAM only, will be lost on reset"
```

Saved scripts live in `/scripts` on the device. Names are validated, not
sanitised: an unacceptable name is refused outright so it cannot become a
write somewhere else on the filesystem.

### Performance notes

What was changed and what it bought, measured against the version before
any of this:

| | before | now |
|---|---|---|
| page held in RAM per request | 27 KB | streamed, never whole |
| bytes sent for the page | 27 KB | 7.1 KB gzipped |
| start-up before the first request | 2.20 s | 0.78 s |
| poll pause while serving | 100 ms | 2 ms |
| poll wakeups per second when idle | 10 | 10 |

The page moved out of `code.py` into `/www` and is streamed by
`FileResponse`, gzipped when `tools/build_www.py` has been run. It carries
an ETag, so a reload that changes nothing costs a `304` rather than the
document.

The serving loop adapts its pause: tight while requests are arriving,
backing off to the original 100 ms when idle, so it is better than the old
fixed pause under load without waking more often at rest.

Those figures were worked out from the code, not taken from a board. To
check them on your own device once it is flashed:

```bash
python3 tools/benchmark.py http://192.168.1.100
```

It reports the page size and whether the gzip and the 304 are working,
status-endpoint latency, free memory either side of a page load, how long
script checking takes as scripts grow, and the largest body the device
actually accepts — which is the quickest way to tell whether
`request_buffer_size` or `MAX_BODY_BYTES` is your real limit. It needs
only the standard library, and it does not touch keystroke sending.

It also runs against `tests/ui/mock_device.py`, which is how the benchmark
itself gets checked; that says nothing about the hardware.

Two things measured and deliberately not done:

- **Minifying the page before gzip.** It takes the raw file from 35.6 KB to
  24.0 KB, but gzip already captures nearly all of that: 7.1 KB against
  6.6 KB. 579 bytes is not worth the risk of mangling inline JavaScript.
- **Precompiling `badusb_core.py` to `.mpy`.** Adafruit's
  [memory-saving guide](https://learn.adafruit.com/memory-saving-tips-for-circuitpython)
  notes this roughly halves the file's storage and cuts the memory needed
  to import it. It is a real saving, but `mpy-cross` output must match your
  CircuitPython version exactly, and a mismatch stops the board booting.
  Worth doing yourself if you are short on RAM, once you know your version;
  delete the `.py` if you add the `.mpy`, or they conflict.

### Versions and compatibility

`lib/` vendors a copy of the Adafruit bundle so the project works without
hunting for libraries, which also means it goes stale quietly. To see how
far behind it is:

```bash
python3 tools/check_versions.py
```

At the time of writing:

| library | vendored here | current |
|---|---|---|
| adafruit_hid | 6.1.5 | 6.1.10 |
| adafruit_httpserver | 4.6.2 | 4.8.2 |
| adafruit_requests | 4.1.10 | 4.1.18 |
| adafruit_ticks | 1.1.2 | 1.1.7 |
| adafruit_connection_manager | 3.1.3 | 3.1.8 |

All are patch or minor updates within the same major version, so nothing
here is urgent.

**CircuitPython.** `flash_board/` ships 9.2.7; the current stable for the
Pico 2 W is
[10.2.1](https://circuitpython.org/board/raspberry_pi_pico2_w/). The
`.mpy` format
[did not change between 9 and 10](https://circuitpython.org/libraries), so
the vendored libraries load on either — the format changed at 9, which is
why 8.x libraries do not. All the files in `lib/` are ABI 6, and
`check_versions.py` reports this, since a mismatch there is the failure
that stops a board rather than merely degrading it.

**If you do update the libraries,** four APIs this firmware depends on
were verified against the vendored copies rather than assumed, and should
be re-checked: `Server.request_buffer_size`, the `"no_request"` poll
status, `FileResponse` accepting `content_type` and `headers`, and
`Keyboard.led_status`. `check_versions.py` checks all four and names what
each is for, so a missing one is visible before you flash rather than
after.

### Running the tests

The logic in `lib/badusb_core.py` can be exercised on a desktop, with
CircuitPython's hardware modules stubbed out:

```bash
python3 -m unittest discover -s tests
```

Among other things this covers where a script actually got stored, what the
validator makes of each kind of line, that a dry run sends nothing, that a
script name cannot escape its directory, and that the serving loop rebuilds
its socket after a reconnect and not when the reconnect failed.

There is also a simulated boot, which runs each build's `code.py` from top
to bottom against stubbed CircuitPython modules and then brings its server
up:

```bash
python3 tests/boot_simulation.py
```

It catches what stops a board dead after a refactor — a name that no
longer exists, an import that moved, a route that raises — and is the
closest check available without flashing.

A green run means the logic holds. It says nothing about USB HID, the radio
or the HTTP server, which are stubbed — those still need a real board.

All of this runs on every push through `.github/workflows/tests.yml`: lint,
the unit tests, the simulated boot, and the browser suite against the
stand-in device.

There is also a browser test for the web page itself, which needs Playwright
and a Chromium:

```bash
python3 tests/ui/mock_device.py &
node tests/ui/ui_test.js
```

`mock_device.py` serves the real page and answers its requests using the
real `badusb_core`, so the page gets what the firmware would send. Worth
running after touching the page: it is what caught the boot animation wiping
command output and deleting the terminal background effect.

## Ethics Statement

KEYOES BadUSB Controller is designed for legitimate security testing, system administration, and educational purposes only. Users bear full responsibility for ensuring their usage complies with applicable laws, regulations, and organizational policies. Always obtain proper authorization before conducting any security testing.
