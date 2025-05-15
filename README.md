# KEYOES BadUSB Controller

A powerful BadUSB controller for Raspberry Pi Pico 2 W with a web interface for remote payload management.

## 🔥 Features

- **Web-based interface** for uploading and executing BadUSB payloads
- **WiFi connectivity** for remote control
- **Persistent connection** - The device will automatically reconnect to WiFi if the connection is lost
- **Fully responsive design** for both mobile and desktop devices
- **Enhanced keyboard simulation** with improved timing control
- **Command history** and payload logging
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
   - adafruit_request.mpy
   - adafruit_ticks.mpy
   - adafruit_connection_manager.mpy

### Step 3: Copy the Code Files

1. Create `boot.py` in the root of your CIRCUITPY drive and copy the code from the provided boot.py file
2. Create `code.py` in the root of your CIRCUITPY drive and copy the code from the provided code.py file
3. Edit the WiFi credentials in `code.py`:
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

### WiFi Reconnection Logic
The device implements a robust WiFi connection system with automatic retries:

```python
def connect_to_wifi():
    max_attempts, retry_delay, attempt = 10, 5, 0
    
    while True:
        attempt += 1
        # ... connection logic
        
        if attempt % max_attempts == 0:
            # Reset the device after multiple failed attempts
            try:
                microcontroller.reset()
            except:
                pass
```

### Script Storage
Scripts can be stored either in the device's filesystem or in memory if file operations fail:

```python
def save_script(script_content):
    try:
        # ... file operations
    except Exception as e:
        print(f"Error saving script: {e}")
        global script_in_memory
        script_in_memory = script_content
        return True
```

## Ethics Statement

KEYOES BadUSB Controller is designed for legitimate security testing, system administration, and educational purposes only. Users bear full responsibility for ensuring their usage complies with applicable laws, regulations, and organizational policies. Always obtain proper authorization before conducting any security testing.
