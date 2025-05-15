import os, time, json, board, digitalio, microcontroller, wifi, socketpool
import adafruit_httpserver.server as httpserver
import adafruit_httpserver.request as httprequest
import adafruit_httpserver.response as httpresponse
import adafruit_httpserver.methods as httpmethods
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
import usb_hid

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

for _ in range(3):
    led.value = True
    time.sleep(0.2)
    led.value = False
    time.sleep(0.2)

WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SCRIPT_PATH = "/badusb_script.txt"

KEY_MAPPING = {
    "CTRL": Keycode.CONTROL, "SHIFT": Keycode.SHIFT, "ALT": Keycode.ALT,
    "GUI": Keycode.GUI, "WINDOWS": Keycode.GUI, "WIN": Keycode.GUI,
    "ENTER": Keycode.ENTER, "RETURN": Keycode.RETURN,
    "ESC": Keycode.ESCAPE, "ESCAPE": Keycode.ESCAPE,
    "BACKSPACE": Keycode.BACKSPACE, "TAB": Keycode.TAB, "SPACE": Keycode.SPACE,
    "CAPSLOCK": Keycode.CAPS_LOCK, "DELETE": Keycode.DELETE,
    "END": Keycode.END, "HOME": Keycode.HOME, "INSERT": Keycode.INSERT,
    "NUMLOCK": Keycode.KEYPAD_NUMLOCK,
    "PAGEUP": Keycode.PAGE_UP, "PAGEDOWN": Keycode.PAGE_DOWN,
    "PRINTSCREEN": Keycode.PRINT_SCREEN, "SCROLLLOCK": Keycode.SCROLL_LOCK,
    "PAUSE": Keycode.PAUSE,
    "UP": Keycode.UP_ARROW, "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW, "RIGHT": Keycode.RIGHT_ARROW,
    "F1": Keycode.F1, "F2": Keycode.F2, "F3": Keycode.F3, "F4": Keycode.F4,
    "F5": Keycode.F5, "F6": Keycode.F6, "F7": Keycode.F7, "F8": Keycode.F8,
    "F9": Keycode.F9, "F10": Keycode.F10, "F11": Keycode.F11, "F12": Keycode.F12,
    "MENU": Keycode.APPLICATION, "APP": Keycode.APPLICATION,
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D, "E": Keycode.E,
    "F": Keycode.F, "G": Keycode.G, "H": Keycode.H, "I": Keycode.I, "J": Keycode.J,
    "K": Keycode.K, "L": Keycode.L, "M": Keycode.M, "N": Keycode.N, "O": Keycode.O,
    "P": Keycode.P, "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X, "Y": Keycode.Y, "Z": Keycode.Z
}

keyboard = Keyboard(usb_hid.devices[0])
keyboard_layout = KeyboardLayoutUS(keyboard)
script_in_memory = None

def check_wifi_connection():
    if not wifi.radio.connected:
        print("WiFi connection lost. Attempting to reconnect...")
        connect_to_wifi()
        return wifi.radio.connected
    return True

def connect_to_wifi():
    max_attempts, retry_delay, attempt = 10, 5, 0
    
    while True:
        attempt += 1
        print(f"Connecting to {WIFI_SSID}... (Attempt {attempt})")
        
        try:
            led.value = True
            time.sleep(0.2)
            led.value = False
            
            wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
            
            print(f"Connected to {WIFI_SSID}")
            print(f"IP Address: {wifi.radio.ipv4_address}")
            
            for _ in range(2):
                led.value = True
                time.sleep(0.2)
                led.value = False
                time.sleep(0.2)
                
            return True
            
        except Exception as e:
            print(f"Failed to connect to WiFi: {e}")
            
            led.value = True
            time.sleep(1)
            led.value = False
            
            if attempt % max_attempts == 0:
                print(f"Reached {max_attempts} consecutive failed attempts.")
                for _ in range(5):
                    led.value = True
                    time.sleep(0.1)
                    led.value = False
                    time.sleep(0.1)
                
                try:
                    microcontroller.reset()
                except:
                    pass
            
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
def save_script(script_content):
    try:
        try:
            os.remove(SCRIPT_PATH)
        except OSError:
            pass
        
        with open(SCRIPT_PATH, "w") as f:
            f.write(script_content)
        return True
    except Exception as e:
        print(f"Error saving script: {e}")
        global script_in_memory
        script_in_memory = script_content
        return True
    
def parse_key_combo(key_combo):
    keys = []
    if "+" in key_combo:
        parts = key_combo.split("+")
        for part in parts:
            part = part.strip().upper()
            if part in KEY_MAPPING:
                keys.append(KEY_MAPPING[part])
    else:
        parts = key_combo.split()
        for part in parts:
            part = part.strip().upper()
            if part in KEY_MAPPING:
                keys.append(KEY_MAPPING[part])
    
    return keys
def execute_key_combination(key_combo):
    keycodes = parse_key_combo(key_combo)
    
    if keycodes:
        try:
            for key in keycodes:
                keyboard.press(key)
                time.sleep(0.05)
            
            time.sleep(0.15)
            
            for key in reversed(keycodes):
                keyboard.release(key)
                time.sleep(0.05)
            
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"Error executing key combination: {e}")
            keyboard.release_all()
            time.sleep(0.1)
            return False
    return False

def execute_script():
    global script_in_memory
    
    try:
        try:
            with open(SCRIPT_PATH, "r") as f:
                script_lines = f.readlines()
        except OSError:
            if script_in_memory:
                script_lines = script_in_memory.splitlines()
            else:
                print("No script found in file or memory")
                return False
        
        char_delay = 0.01
        
        for line in script_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            led.value = True
            
            parts = line.split(" ", 1)
            command = parts[0].upper()
            
            if command == "STRING":
                if len(parts) > 1:
                    text = parts[1]
                    for char in text:
                        keyboard_layout.write(char)
                        time.sleep(char_delay)
                    time.sleep(0.05)
            elif command == "DELAY":
                if len(parts) > 1:
                    try:
                        delay_ms = int(parts[1])
                        time.sleep(delay_ms / 1000.0)
                    except ValueError:
                        print(f"Invalid delay value: {parts[1]}")
            elif command == "CHAR_DELAY":
                if len(parts) > 1:
                    try:
                        char_delay = float(parts[1]) / 1000.0
                        print(f"Character delay set to {char_delay}s")
                    except ValueError:
                        print(f"Invalid CHAR_DELAY value: {parts[1]}")
            elif command == "REM" or command.startswith("//"):
                pass
            elif command in KEY_MAPPING:
                keyboard.press(KEY_MAPPING[command])
                time.sleep(0.1)
                keyboard.release(KEY_MAPPING[command])
                time.sleep(0.05)
            elif "+" in line:
                execute_key_combination(line)
                time.sleep(0.1)
            else:
                execute_key_combination(line)
                time.sleep(0.05)
            
            led.value = False
            time.sleep(0.1)
        
        return True
    except Exception as e:
        print(f"Error executing script: {e}")
        led.value = False
        return False
def setup_server():
    pool = socketpool.SocketPool(wifi.radio)
    server = httpserver.Server(pool, "/static")
    
    payload_history = []
    wifi_status = {"connected": True, "ip": str(wifi.radio.ipv4_address) if wifi.radio.connected else "Not connected"}
    
    @server.route("/", httpmethods.GET)
    def base(request):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Keyoes BadUSB Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --kali-bg: #0a0a12;
            --kali-terminal-bg: #050510;
            --kali-border: #1a3a5a;
            --kali-text: #d8e1f2;
            --kali-accent: #3584e4;
            --kali-accent2: #2250a9;
            --kali-header: #0f1628;
            --kali-button: #1b2a47;
            --kali-button-hover: #2b4068;
            --kali-shadow: rgba(0, 10, 30, 0.5);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body { 
            font-family: 'JetBrains Mono', 'Ubuntu Mono', 'Courier New', monospace; 
            background-color: var(--kali-bg);
            color: var(--kali-text);
            margin: 0; 
            padding: 0;
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 15px;
        }
        
        .header {
            background-color: var(--kali-header);
            border-bottom: 1px solid var(--kali-border);
            padding: 15px 0;
            margin-bottom: 20px;
            text-align: center;
            position: relative;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }
        
        .logo {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
        }
        
        .logo-top {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 5px;
        }
        
        .logo img {
            width: 30px;
            height: 30px;
            margin-right: 10px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #3584e4;
            letter-spacing: 1px;
            text-transform: uppercase;
            border: 1px solid #3584e4;
            padding: 3px 10px;
            border-radius: 3px;
            background-color: rgba(53, 132, 228, 0.1);
        }
        
        .rgb-text {
            background-image: linear-gradient(90deg, 
                #0066ff, #00ccff, #00ffcc, #00cc66, #3584e4, #2b4068, #00ccff, #0066ff);
            background-size: 200% auto;
            color: #000;
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: rgb-animation 3s linear infinite;
            text-shadow: 
                0 0 10px rgba(0, 102, 255, 0.5),
                0 0 20px rgba(53, 132, 228, 0.3),
                0 0 30px rgba(0, 102, 255, 0.2);
            font-weight: bold;
            font-size: 34px;
            letter-spacing: 2px;
            filter: brightness(1.2) contrast(1.2);
        }
        
        .wifi-status {
            position: absolute;
            top: 15px;
            right: 15px;
            display: flex;
            align-items: center;
            font-size: 12px;
            background-color: var(--kali-terminal-bg);
            padding: 5px 10px;
            border-radius: 20px;
            border: 1px solid var(--kali-border);
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        @media (max-width: 768px) {
            .wifi-status {
                position: static;
                margin-top: 10px;
                justify-content: center;
                width: 100%;
            }
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        .status-connected {
            background-color: #3584e4;
            box-shadow: 0 0 5px #3584e4;
        }
        
        @keyframes rgb-animation {
            to {
                background-position: 200% center;
            }
        }
        
        .terminal-window {
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-radius: 5px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 5px 15px var(--kali-shadow);
        }
        
        .terminal-header {
            background: linear-gradient(to right, #1b2a47, #0f1628);
            padding: 10px 15px;
            border-bottom: 1px solid var(--kali-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .terminal-title {
            color: #ffffff;
            font-size: 14px;
            display: flex;
            align-items: center;
        }
        
        .terminal-icon {
            width: 16px;
            height: 16px;
            background-color: var(--kali-accent);
            border-radius: 3px;
            margin-right: 8px;
        }
        
        .terminal-controls {
            display: flex;
        }
        
        .terminal-button {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 8px;
        }
        
        .close { background-color: #ff5f56; }
        .minimize { background-color: #ffbd2e; }
        .maximize { background-color: #27c93f; }
        
        .terminal-editor {
            padding: 15px;
            position: relative;
        }
        
        #script {
            width: 100%;
            min-height: 350px;
            background-color: transparent;
            color: var(--kali-text);
            border: none;
            font-family: 'JetBrains Mono', 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
            outline: none;
            padding: 15px;
            white-space: pre-wrap;
            line-height: 1.5;
        }
        
        .button-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
            margin: 20px 0;
        }
        
        button {
            background-color: var(--kali-button);
            color: var(--kali-text);
            border: 1px solid var(--kali-border);
            border-radius: 4px;
            padding: 12px 20px;
            font-family: 'JetBrains Mono', 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 130px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        button:hover {
            background-color: var(--kali-button-hover);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            transform: translateY(-2px);
        }
        
        .output-window {
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-radius: 5px;
            padding: 15px 15px 15px 10px;
            margin-top: 20px;
            height: 80px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            position: relative;
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
        }
        
        .output-window::before {
            content: "root@kali:~# ";
            color: var(--kali-accent);
            margin-right: 5px;
        }
        
        .cursor {
            display: inline-block;
            width: 8px;
            height: 16px;
            background-color: var(--kali-accent);
            animation: blink 1s step-end infinite;
            vertical-align: middle;
            margin-left: 5px;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 15px 0;
            font-size: 12px;
            color: #6e87b0;
            border-top: 1px solid var(--kali-border);
        }
        
        @media (max-width: 768px) {
            .container {padding: 10px;}
            .button-container {flex-direction: column;align-items: stretch;}
            button {width: 100%;margin-bottom: 10px;}
            #script {min-height: 250px;}
            .logo-top {flex-direction: column;}
            .rgb-text {font-size: 28px;margin-bottom: 5px;}
            .tab-panel {flex-direction: column;}
            .tab {margin-right: 0;margin-bottom: 5px;width: 100%;text-align: center;}
            .terminal-header {padding: 8px;}
            .terminal-title {font-size: 12px;}
            .output-window {font-size: 12px;}
        }
        
        .command-history {
            margin-top: 20px;
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-radius: 5px;
            padding: 15px;
            max-height: 180px;
            overflow-y: auto;
            box-shadow: 0 3px 10px var(--kali-shadow);
        }
        
        .history-title {
            color: var(--kali-accent);
            font-size: 14px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--kali-border);
            padding-bottom: 8px;
            font-weight: bold;
            letter-spacing: 1px;
        }
        
        .history-item {
            font-size: 12px;
            padding: 5px 0;
            border-bottom: 1px dotted var(--kali-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .history-item:last-child {border-bottom: none;}
        
        .history-left {
            display: flex;
            align-items: center;
        }
        
        .history-timestamp {
            color: #6e87b0;
            margin-right: 10px;
            font-family: monospace;
        }
        
        .history-command {color: var(--kali-text);}
        
        .history-status {
            color: var(--kali-accent);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            background-color: rgba(53, 132, 228, 0.1);
        }
        
        .history-status.fail {
            color: #ff5f56;
            background-color: rgba(255, 95, 86, 0.1);
        }
        
        .tab-panel {
            display: flex;
            margin-top: 20px;
            border-bottom: 1px solid var(--kali-border);
        }
        
        .tab {
            padding: 10px 18px;
            background-color: var(--kali-button);
            border: 1px solid var(--kali-border);
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: bold;
            letter-spacing: 0.5px;
        }
        
        .tab.active {
            background-color: var(--kali-accent);
            color: #ffffff;
        }
        
        .tab:hover {
            background-color: var(--kali-button-hover);
            transform: translateY(-2px);
        }
        
        .tab.active:hover {background-color: var(--kali-accent);}
        
        .tab-content {
            display: none;
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-top: none;
            border-radius: 0 0 5px 5px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px var(--kali-shadow);
        }
        
        .tab-content.active {display: block;}
        
        .payloads-container {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .payload-item {
            background-color: rgba(53, 132, 228, 0.05);
            border-left: 3px solid var(--kali-accent);
            margin-bottom: 15px;
            padding: 12px;
            font-size: 13px;
            word-break: break-all;
            border-radius: 0 4px 4px 0;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .payload-timestamp {
            font-weight: bold;
            color: var(--kali-accent);
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 1px dotted var(--kali-border);
        }
        
        .payload-content {
            white-space: pre-wrap;
            font-family: 'JetBrains Mono', 'Ubuntu Mono', 'Courier New', monospace;
            line-height: 1.4;
        }
        
        .keyboard-shortcut {
            background-color: var(--kali-button);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 5px;
            border: 1px solid var(--kali-border);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        #prompt-prefix {
            color: var(--kali-accent);
            font-weight: bold;
        }
        
        #prompt-separator {color: #767f96;}
        
        .terminal-bg-effect {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(180deg, 
                rgba(53, 132, 228, 0.03) 0%, 
                rgba(0, 20, 50, 0.01) 50%,
                rgba(53, 132, 228, 0.02) 100%);
            pointer-events: none;
            z-index: -1;
        }
        
        .scan-line {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: rgba(53, 132, 228, 0.1);
            opacity: 0.5;
            pointer-events: none;
            z-index: 1;
            animation: scan 8s linear infinite;
        }
        
        @keyframes scan {
            0% { top: 0; }
            100% { top: 100%; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-top">
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 10px;">
                    <path d="M12 2L2 7V15L12 20L22 15V7L12 2Z" stroke="#3584e4" stroke-width="2" fill="#111827"/>
                    <path d="M12 6L7 8.5V13.5L12 16L17 13.5V8.5L12 6Z" fill="#3584e4"/>
                </svg>
                <span class="rgb-text">KEYOES</span>
            </div>
            <div class="subtitle">SECURITY IS AN ILLUSION</div>
        </div>
        <div class="wifi-status">
            <div class="status-indicator status-connected"></div>
            <span>WiFi Connected</span>
        </div>
    </div>
    
    <div class="container">
        <div class="tab-panel">
            <div class="tab active" onclick="switchTab('terminal')">Terminal</div>
            <div class="tab" onclick="switchTab('payloads')">Payloads Log <span class="keyboard-shortcut">Ctrl+P</span></div>
        </div>
        
        <div id="terminal-tab" class="tab-content active">
            <div class="terminal-window">
                <div class="terminal-header">
                    <div class="terminal-title">
                        <div class="terminal-icon"></div>
                        <span id="prompt-prefix">root@kali</span><span id="prompt-separator">:</span> ~/bad_usb_W                    </div>
                    <div class="terminal-controls">
                        <div class="terminal-button minimize"></div>
                        <div class="terminal-button maximize"></div>
                        <div class="terminal-button close"></div>
                    </div>
                </div>
                <div class="terminal-editor">
                    <div class="terminal-bg-effect"></div>
                    <div class="scan-line"></div>
                    <textarea id="script" placeholder="Type here  ..."></textarea>
                </div>
            </div>
            
            <div class="button-container">
                <button onclick="sendScript()">UPLOAD</button>
                <button onclick="executeScript()">EXECUTE</button>
                <button onclick="clearScript()">CLEAR</button>
            </div>
            
            <div class="output-window">
                <div class="terminal-bg-effect"></div>
                <span id="status">System ready. Waiting for command...</span><span class="cursor"></span>
            </div>
            
            <div class="command-history">
                <div class="history-title">COMMAND HISTORY</div>
                <div id="history-content"></div>
            </div>
        </div>
        
        <div id="payloads-tab" class="tab-content">
            <div class="history-title">EXECUTED PAYLOADS <small>(Session only)</small></div>
            <div class="payloads-container" id="payloads-content">
                <div class="payload-item">
                    <div class="payload-timestamp">No payloads executed yet</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><span class="rgb-text" style="font-size: 14px;">KEYOES</span> BadUSB Controller v2.5 | Raspberry Pi Pico 2 W | Kali Interface style</p>
        </div>
    </div>

    <script>
        let commandHistory = [], payloadHistory = [], lastPingTime = Date.now(), connectionLost = false, connectionCheckInterval;
        
        function addToHistory(command, status) {
            const now = new Date(), timestamp = now.toLocaleTimeString();
            commandHistory.unshift({time: timestamp, command: command, status: status});
            if (commandHistory.length > 10) commandHistory.pop();
            updateHistoryDisplay();
        }
        
        function updateHistoryDisplay() {
            const historyContent = document.getElementById('history-content');
            historyContent.innerHTML = '';
            
            commandHistory.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                const statusClass = item.status.includes('success') ? '' : 'fail';
                historyItem.innerHTML = `
                    <div class="history-left">
                        <span class="history-timestamp">[${item.time}]</span>
                        <span class="history-command">${item.command}</span>
                    </div>
                    <span class="history-status ${statusClass}">${item.status}</span>
                `;
                historyContent.appendChild(historyItem);
            });
        }
        
        function addToPayloadHistory(scriptContent) {
            const now = new Date();
            const timestamp = now.toLocaleTimeString() + ' ' + now.toLocaleDateString();
            payloadHistory.unshift({time: timestamp, content: scriptContent});
            if (payloadHistory.length > 20) payloadHistory.pop();
            updatePayloadDisplay();
        }
        
        function updatePayloadDisplay() {
            const payloadsContent = document.getElementById('payloads-content');
            payloadsContent.innerHTML = '';
            
            if (payloadHistory.length === 0) {
                const emptyItem = document.createElement('div');
                emptyItem.className = 'payload-item';
                emptyItem.innerHTML = '<div class="payload-timestamp">No payloads executed yet</div>';
                payloadsContent.appendChild(emptyItem);
                return;
            }
            
            payloadHistory.forEach(item => {
                const payloadItem = document.createElement('div');
                payloadItem.className = 'payload-item';
                payloadItem.innerHTML = `
                    <div class="payload-timestamp">${item.time}</div>
                    <div class="payload-content">${escapeHtml(item.content)}</div>
                `;
                payloadsContent.appendChild(payloadItem);
            });
        }
        
        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            if (tabName === 'terminal') {
                document.querySelector('.tab:nth-child(1)').classList.add('active');
                document.getElementById('terminal-tab').classList.add('active');
            } else if (tabName === 'payloads') {
                document.querySelector('.tab:nth-child(2)').classList.add('active');
                document.getElementById('payloads-tab').classList.add('active');
            }
        }
        
        function sendScript() {
            const script = document.getElementById('script').value;
            document.getElementById('status').innerHTML = "Uploading script...";
            
            fetch('/upload', {
                method: 'POST',
                body: script,
                headers: {'Content-Type': 'text/plain'}
            })
            .then(response => response.text())
            .then(data => {
                document.getElementById('status').innerHTML = data;
                addToHistory("UPLOAD", "success");
            })
            .catch(error => {
                document.getElementById('status').innerHTML = 'Error: ' + error;
                addToHistory("UPLOAD", "failed: " + error);
            });
        }

        function executeScript() {
            const script = document.getElementById('script').value;
            document.getElementById('status').innerHTML = "Executing attack...";
            
            fetch('/execute', {method: 'POST'})
            .then(response => response.text())
            .then(data => {
                document.getElementById('status').innerHTML = data;
                addToHistory("EXECUTE", "success");
                if (script && script.trim() !== '') addToPayloadHistory(script);
            })
            .catch(error => {
                document.getElementById('status').innerHTML = 'Error: ' + error;
                addToHistory("EXECUTE", "failed: " + error);
            });
        }
        
        function clearScript() {
            document.getElementById('script').value = '';
            document.getElementById('status').innerHTML = "Terminal cleared";
            addToHistory("CLEAR", "success");
        }
        
        function checkWifiStatus() {
            fetch('/wifi-status?t=' + Date.now(), {signal: AbortSignal.timeout(3000)})
            .then(response => response.json())
            .then(data => {
                lastPingTime = Date.now();
                connectionLost = false;
                
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.wifi-status span');
                
                if (data.connected) {
                    indicator.className = 'status-indicator status-connected';
                    statusText.textContent = `WiFi: ${data.ip}`;
                    indicator.style.backgroundColor = '#3584e4';
                } else {
                    indicator.className = 'status-indicator';
                    indicator.style.backgroundColor = '#ff5f56';
                    statusText.textContent = 'WiFi: Disconnected';
                }
            })
            .catch(error => {
                console.error('Error checking WiFi status:', error);
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.wifi-status span');
                
                connectionLost = true;
                indicator.className = 'status-indicator';
                indicator.style.backgroundColor = '#ff5f56';
                statusText.textContent = 'Connection Lost';
            });
        }
        
        function checkOfflineStatus() {
            if (Date.now() - lastPingTime > 20000 && !connectionLost) {
                connectionLost = true;
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.wifi-status span');
                
                indicator.className = 'status-indicator';
                indicator.style.backgroundColor = '#ff5f56';
                statusText.textContent = 'Device Offline';
            }
        }
        
        connectionCheckInterval = setInterval(checkWifiStatus, 60000);
        setInterval(checkOfflineStatus, 5000);
        
        document.addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'p') {
                event.preventDefault();
                switchTab('payloads');
            }
            if (event.ctrlKey && event.key === 't') {
                event.preventDefault();
                switchTab('terminal');
            }
            if (event.ctrlKey && event.key === 'Enter') {
                event.preventDefault();
                executeScript();
            }
            if (event.ctrlKey && event.key === 's') {
                event.preventDefault();
                sendScript();
            }
        });
        
        document.querySelectorAll('button').forEach(button => {
            button.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(1px)';
            });
            button.addEventListener('mouseup', function() {
                this.style.transform = '';
            });
            button.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
        });
        
        window.onload = function() {
            addToHistory("SYSTEM BOOT", "success");
            checkWifiStatus();
            
            let initialChecks = 0;
            const initialInterval = setInterval(() => {
                checkWifiStatus();
                initialChecks++;
                if (initialChecks >= 12) clearInterval(initialInterval);
            }, 10000);
            
            const outputWindow = document.querySelector('.output-window');
            outputWindow.innerHTML = '<span id="status">Initializing Keyoes BadUSB Controller...</span><span class="cursor"></span>';
            
            setTimeout(() => {
                outputWindow.innerHTML = '<span id="status">Loading system modules...</span><span class="cursor"></span>';
            }, 800);
            
            setTimeout(() => {
                outputWindow.innerHTML = '<span id="status">Establishing connection...</span><span class="cursor"></span>';
            }, 1600);
            
            setTimeout(() => {
                outputWindow.innerHTML = '<span id="status">System ready. Waiting for command...</span><span class="cursor"></span>';
            }, 2400);
        };
    </script>
</body>
</html>"""
        return httpresponse.Response(request, html, content_type="text/html")
    
    @server.route("/upload", httpmethods.POST)
    def upload_script(request):
        try:
            content = request.body.decode("utf-8")
            if save_script(content):
                return httpresponse.Response(request, "Script uploaded successfully")
            else:
                return httpresponse.Response(request, "Failed to save script", status=500)
        except Exception as e:
            return httpresponse.Response(request, f"Error: {str(e)}", status=500)
    
    @server.route("/execute", httpmethods.POST)
    def execute_badusb(request):
        try:
            if execute_script():
                return httpresponse.Response(request, "Attack executed successfully")
            else:
                return httpresponse.Response(request, "Failed to execute script", status=500)
        except Exception as e:
            return httpresponse.Response(request, f"Error: {str(e)}", status=500)

    @server.route("/wifi-status", httpmethods.GET)
    def wifi_status_check(request):
        try:
            is_connected = wifi.radio.connected
            status = {
                "connected": is_connected,
                "ip": str(wifi.radio.ipv4_address) if is_connected else "Not connected",
                "timestamp": time.time()
            }
            headers = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
            return httpresponse.Response(request, json.dumps(status),
                                       content_type="application/json",
                                       headers=headers)
        except Exception as e:
            return httpresponse.Response(request, json.dumps({
                "connected": False,
                "error": str(e),
                "timestamp": time.time()
            }), content_type="application/json")
    
    @server.route("/api/badusb", httpmethods.POST)
    def api_badusb(request):
        try:
            content = request.body.decode("utf-8")
            
            try:
                data = json.loads(content)
                action = data.get("action", "")
                
                if action == "upload" and "script" in data:
                    if save_script(data["script"]):
                        return httpresponse.Response(request, '{"status": "success", "message": "Script uploaded"}', 
                                                  content_type="application/json")
                    else:
                        return httpresponse.Response(request, '{"status": "error", "message": "Failed to save script"}', 
                                                  status=500, content_type="application/json")
                
                elif action == "execute":
                    if execute_script():
                        return httpresponse.Response(request, '{"status": "success", "message": "Script executed"}', 
                                                  content_type="application/json")
                    else:
                        return httpresponse.Response(request, '{"status": "error", "message": "Failed to execute script"}', 
                                                  status=500, content_type="application/json")
                
                else:
                    return httpresponse.Response(request, '{"status": "error", "message": "Invalid action"}', 
                                              status=400, content_type="application/json")
                
            except ValueError:
                if save_script(content):
                    if execute_script():
                        return httpresponse.Response(request, "Script uploaded and executed successfully")
                    else:
                        return httpresponse.Response(request, "Script uploaded but execution failed", status=500)
                else:
                    return httpresponse.Response(request, "Failed to save script", status=500)
                
        except Exception as e:
            return httpresponse.Response(request, f'{{"status": "error", "message": "{str(e)}"}}', 
                                      status=500, content_type="application/json")
    
    print("Starting server on port 80...")
    try:
        server.start(port=80)
        return server
    except Exception as e:
        print(f"Server error: {e}")
        return None
def main():
    connect_to_wifi()
    server = setup_server()
    
    last_wifi_check = time.monotonic()
    wifi_check_interval = 60
    
    if server:
        led.value = True
        time.sleep(1)
        led.value = False
        
        try:
            while True:
                try:
                    server.poll()
                except Exception as e:
                    print(f"Error during server poll: {e}")
                    if check_wifi_connection():
                        print("Trying to restart server...")
                        server = setup_server()
                        if not server:
                            microcontroller.reset()
                
                current_time = time.monotonic()
                if current_time - last_wifi_check > wifi_check_interval:
                    print("Running scheduled WiFi connection check...")
                    if not check_wifi_connection():
                        print("Server may need restart after WiFi reconnection...")
                        server = setup_server()
                        if not server:
                            microcontroller.reset()
                    last_wifi_check = time.monotonic()
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Server polling error: {e}")
            check_wifi_connection()
            try:
                server = setup_server()
                if not server:
                    microcontroller.reset()
            except:
                microcontroller.reset()
    else:
        for _ in range(5):
            led.value = True
            time.sleep(0.1)
            led.value = False
            time.sleep(0.1)
        microcontroller.reset()

if __name__ == "__main__":
    main()
