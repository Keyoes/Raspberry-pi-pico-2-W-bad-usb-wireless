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
- **One long blink**: Server started successfully
- **5 quick blinks**: Server failed to start
- **LED on during command execution**: Command being executed

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

### Bug: CHAR_DELAY should have a minimum of 30ms to prevent data loss

#### Description
When executing BadUSB payloads through the KEYOES controller, the current default character delay of 10ms (`char_delay = 0.01` in the code) causes reliability issues. Characters are frequently dropped or misinterpreted during payload execution, especially with longer commands or when targeting systems under load.

#### Current Implementation
In the current code (`execute_script()` function), the default setting is:
```python
char_delay = 0.01  # 10ms between characters
```

The `CHAR_DELAY` command exists but has no minimum value enforcement.

#### Recommended Fix
Always use `CHAR_DELAY 30` (or higher) at the beginning of your scripts to ensure reliable execution. For example:

```
REM Set a safer character delay first
CHAR_DELAY 30
STRING echo This script will execute reliably
ENTER
```

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
tests/                       runs on a desktop, no board required
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

A green run means the logic holds. It says nothing about USB HID, the radio
or the HTTP server, which are stubbed — those still need a real board.

## Ethics Statement

KEYOES BadUSB Controller is designed for legitimate security testing, system administration, and educational purposes only. Users bear full responsibility for ensuring their usage complies with applicable laws, regulations, and organizational policies. Always obtain proper authorization before conducting any security testing.
