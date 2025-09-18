import os, time, json, board, digitalio, microcontroller, wifi, socketpool
import adafruit_httpserver.server as httpserver
import adafruit_httpserver.request as httprequest
import adafruit_httpserver.response as httpresponse
import adafruit_httpserver.methods as httpmethods
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
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
    "CTRL": Keycode.CONTROL, "CONTROL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT, "ALT": Keycode.ALT,
    "GUI": Keycode.GUI, "WINDOWS": Keycode.GUI, "WIN": Keycode.GUI,
    "COMMAND": Keycode.GUI, "CMD": Keycode.GUI,
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
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X, "Y": Keycode.Y, "Z": Keycode.Z,
    "0": Keycode.ZERO, "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE,
    "4": Keycode.FOUR, "5": Keycode.FIVE, "6": Keycode.SIX, "7": Keycode.SEVEN,
    "8": Keycode.EIGHT, "9": Keycode.NINE,
    "MINUS": Keycode.MINUS, "EQUALS": Keycode.EQUALS,
    "LEFT_BRACKET": Keycode.LEFT_BRACKET, "RIGHT_BRACKET": Keycode.RIGHT_BRACKET,
    "BACKSLASH": Keycode.BACKSLASH, "SEMICOLON": Keycode.SEMICOLON,
    "QUOTE": Keycode.QUOTE, "GRAVE_ACCENT": Keycode.GRAVE_ACCENT,
    "COMMA": Keycode.COMMA, "PERIOD": Keycode.PERIOD, "FORWARD_SLASH": Keycode.FORWARD_SLASH
}

COMMAND_SHORTCUTS = {
    "COPY": "CTRL+C", "PASTE": "CTRL+V", "CUT": "CTRL+X",
    "UNDO": "CTRL+Z", "REDO": "CTRL+Y", "SELECT_ALL": "CTRL+A",
    "SAVE": "CTRL+S", "OPEN": "CTRL+O", "NEW": "CTRL+N",
    "FIND": "CTRL+F", "REPLACE": "CTRL+H", "PRINT": "CTRL+P",
    "REFRESH": "F5", "FULLSCREEN": "F11",
    "TASK_MANAGER": "CTRL+SHIFT+ESC", "ALT_TAB": "ALT+TAB",
    "WIN_L": "GUI+L", "WIN_R": "GUI+R", "WIN_X": "GUI+X",
    "WIN_D": "GUI+D", "WIN_E": "GUI+E", "WIN_I": "GUI+I",
    "WIN_S": "GUI+S", "WIN_TAB": "GUI+TAB",
    "CTRL_ALT_DEL": "CTRL+ALT+DELETE", "CLOSE_WINDOW": "ALT+F4",
    "MINIMIZE": "GUI+M", "MAXIMIZE": "GUI+UP", "RESTORE": "GUI+DOWN",
    "SNAP_LEFT": "GUI+LEFT", "SNAP_RIGHT": "GUI+RIGHT"
}

keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)
mouse = Mouse(usb_hid.devices)
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

def execute_mouse_command(command, params, char_delay, mouse_speed=1):
    try:
        if command == "MOUSE_CLICK":
            if params:
                button = params.upper()
                if button == "LEFT":
                    mouse.click(Mouse.LEFT_BUTTON)
                elif button == "RIGHT":
                    mouse.click(Mouse.RIGHT_BUTTON)
                elif button == "MIDDLE":
                    mouse.click(Mouse.MIDDLE_BUTTON)
                else:
                    print(f"Unknown mouse button: {button}")
                    return False
            else:
                mouse.click(Mouse.LEFT_BUTTON)
            time.sleep(char_delay)
            return True
            
        elif command == "MOUSE_MOVE":
            if params:
                coords = params.split()
                if len(coords) >= 2:
                    try:
                        target_x = int(coords[0])
                        target_y = int(coords[1])
                        
                        steps = max(1, int(max(abs(target_x), abs(target_y)) / (mouse_speed * 10)))
                        
                        if steps > 1:
                            step_x = target_x / steps
                            step_y = target_y / steps
                            
                            for i in range(steps):
                                mouse.move(int(step_x), int(step_y))
                                time.sleep(char_delay / 2)
                        else:
                            mouse.move(target_x, target_y)
                            
                        time.sleep(char_delay)
                        return True
                    except ValueError:
                        print(f"Invalid coordinates: {params}")
                        return False
            print("MOUSE_MOVE requires x y coordinates")
            return False
            
        elif command == "SCROLL_UP":
            scroll_amount = 1
            if params:
                try:
                    scroll_amount = int(params)
                except ValueError:
                    pass
            
            for _ in range(scroll_amount):
                mouse.move(0, 0, 1)
                time.sleep(char_delay / 2)
            time.sleep(char_delay)
            return True
            
        elif command == "SCROLL_DOWN":
            scroll_amount = 1
            if params:
                try:
                    scroll_amount = int(params)
                except ValueError:
                    pass
                    
            for _ in range(scroll_amount):
                mouse.move(0, 0, -1)
                time.sleep(char_delay / 2)
            time.sleep(char_delay)
            return True
            
        elif command == "MOUSE_PRESS":
            if params:
                button = params.upper()
                if button == "LEFT":
                    mouse.press(Mouse.LEFT_BUTTON)
                elif button == "RIGHT":
                    mouse.press(Mouse.RIGHT_BUTTON)
                elif button == "MIDDLE":
                    mouse.press(Mouse.MIDDLE_BUTTON)
                time.sleep(char_delay)
                return True
            return False
            
        elif command == "MOUSE_RELEASE":
            if params:
                button = params.upper()
                if button == "LEFT":
                    mouse.release(Mouse.LEFT_BUTTON)
                elif button == "RIGHT":
                    mouse.release(Mouse.RIGHT_BUTTON)
                elif button == "MIDDLE":
                    mouse.release(Mouse.MIDDLE_BUTTON)
                elif button == "ALL":
                    mouse.release_all()
            else:
                mouse.release_all()
            time.sleep(char_delay)
            return True
            
        elif command == "MOUSE_DRAG":
            if params:
                coords = params.split()
                if len(coords) >= 2:
                    try:
                        target_x = int(coords[0])
                        target_y = int(coords[1])
                        
                        mouse.press(Mouse.LEFT_BUTTON)
                        time.sleep(char_delay)
                        
                        steps = max(1, int(max(abs(target_x), abs(target_y)) / (mouse_speed * 8)))
                        
                        if steps > 1:
                            step_x = target_x / steps
                            step_y = target_y / steps
                            
                            for i in range(steps):
                                mouse.move(int(step_x), int(step_y))
                                time.sleep(char_delay / 3)
                        else:
                            mouse.move(target_x, target_y)
                            
                        time.sleep(char_delay)
                        
                        mouse.release(Mouse.LEFT_BUTTON)
                        time.sleep(char_delay)
                        return True
                    except ValueError:
                        print(f"Invalid drag coordinates: {params}")
                        return False
            return False
            
        else:
            print(f"Unknown mouse command: {command}")
            return False
            
    except Exception as e:
        print(f"Error executing mouse command {command}: {e}")
        mouse.release_all()
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
        
        char_delay = 0.03
        mouse_speed = 1
        
        for line in script_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            led.value = True
            
            parts = line.split(" ", 1)
            command = parts[0].upper()
            
            if command in COMMAND_SHORTCUTS:
                print(f"Executing shortcut: {command} -> {COMMAND_SHORTCUTS[command]}")
                execute_key_combination(COMMAND_SHORTCUTS[command])
                time.sleep(char_delay)
                
            elif command == "STRING":
                if len(parts) > 1:
                    text = parts[1]
                    for char in text:
                        keyboard_layout.write(char)
                        time.sleep(char_delay)
                    time.sleep(char_delay)
                    
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
                        char_delay = max(0.001, float(parts[1]) / 1000.0)
                        print(f"Character delay set to {int(char_delay * 1000)}ms")
                    except ValueError:
                        print(f"Invalid CHAR_DELAY value: {parts[1]}")
                        
            elif command == "MOUSE_SPEED":
                if len(parts) > 1:
                    try:
                        mouse_speed = max(0.1, min(10.0, float(parts[1])))
                        print(f"Mouse speed set to {mouse_speed}x")
                    except ValueError:
                        print(f"Invalid MOUSE_SPEED value: {parts[1]}")
                        
            elif command == "REM" or command.startswith("//"):
                pass
                
            elif command.startswith("MOUSE_") or command in ["SCROLL_UP", "SCROLL_DOWN"]:
                if execute_mouse_command(command, parts[1] if len(parts) > 1 else "", char_delay, mouse_speed):
                    print(f"Mouse command executed: {line}")
                else:
                    print(f"Failed to execute mouse command: {line}")
                    
            elif command in KEY_MAPPING:
                keyboard.press(KEY_MAPPING[command])
                time.sleep(char_delay)
                keyboard.release(KEY_MAPPING[command])
                time.sleep(char_delay)
                
            elif "+" in line:
                execute_key_combination(line)
                time.sleep(char_delay)
                
            else:
                execute_key_combination(line)
                time.sleep(char_delay)
            
            led.value = False
            time.sleep(char_delay / 2)
        
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
    <title>Keyoes BadUSB Controller Enhanced</title>
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
            .terminal-header {padding: 8px;}
            .terminal-title {font-size: 12px;}
            .output-window {font-size: 12px;}
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
            <div class="subtitle">KEYBOARD + MOUSE CONTROLLER</div>
        </div>
        <div class="wifi-status">
            <div class="status-indicator status-connected"></div>
            <span>WiFi Connected</span>
        </div>
    </div>
    
    <div class="container">
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-title">
                    <div class="terminal-icon"></div>
                    BadUSB Enhanced - Keyboard + Mouse Control
                </div>
                <div class="terminal-controls">
                    <div class="terminal-button minimize"></div>
                    <div class="terminal-button maximize"></div>
                    <div class="terminal-button close"></div>
                </div>
            </div>
            <div class="terminal-editor">
                <textarea id="script" placeholder="Type here ..."></textarea>
            </div>
        </div>
        
        <div class="button-container">
            <button onclick="sendScript()">UPLOAD</button>
            <button onclick="executeScript()">EXECUTE</button>
            <button onclick="clearScript()">CLEAR</button>
            <button onclick="showHelp()">HELP</button>
        </div>
        
        <div class="output-window">
            <span id="status">Enhanced system ready with keyboard + mouse support!</span><span class="cursor"></span>
        </div>
        
        <div class="footer">
            <p><span class="rgb-text" style="font-size: 14px;">KEYOES</span> BadUSB Enhanced v3.0 | Keyboard + Mouse Control</p>
        </div>
    </div>

    <script>
        function sendScript() {
            const script = document.getElementById('script').value;
            document.getElementById('status').innerHTML = "Uploading enhanced script...";
            
            fetch('/upload', {
                method: 'POST',
                body: script,
                headers: {'Content-Type': 'text/plain'}
            })
            .then(response => response.text())
            .then(data => {
                document.getElementById('status').innerHTML = data;
            })
            .catch(error => {
                document.getElementById('status').innerHTML = 'Error: ' + error;
            });
        }

        function executeScript() {
            document.getElementById('status').innerHTML = "Executing enhanced attack...";
            
            fetch('/execute', {method: 'POST'})
            .then(response => response.text())
            .then(data => {
                document.getElementById('status').innerHTML = data;
            })
            .catch(error => {
                document.getElementById('status').innerHTML = 'Error: ' + error;
            });
        }
        
        function clearScript() {
            document.getElementById('script').value = '';
            document.getElementById('status').innerHTML = "Script cleared";
        }
        
        function showHelp() {
            alert(`NU ai nevoide de ajutor.Ce-i asta?`);
        }
        
        function checkWifiStatus() {
            fetch('/wifi-status?t=' + Date.now(), {signal: AbortSignal.timeout(3000)})
            .then(response => response.json())
            .then(data => {
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
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.wifi-status span');
                
                indicator.className = 'status-indicator';
                indicator.style.backgroundColor = '#ff5f56';
                statusText.textContent = 'Connection Lost';
            });
        }
        
        setInterval(checkWifiStatus, 30000);
        
        document.addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'Enter') {
                event.preventDefault();
                executeScript();
            }
            if (event.ctrlKey && event.key === 's') {
                event.preventDefault();
                sendScript();
            }
            if (event.key === 'F1') {
                event.preventDefault();
                showHelp();
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
            checkWifiStatus();
            document.getElementById('status').innerHTML = "KEYOES Enhanced ready - Keyboard + Mouse support enabled!";
        };
    </script>
</body>
</html>"""
        return httpresponse.Response(request, html, content_type="text/html")
    
    @server.route("/script", httpmethods.GET)
    def get_script(request):
        global script_in_memory
        try:
            with open(SCRIPT_PATH, "r") as f:
                content = f.read()
                return httpresponse.Response(request, content, content_type="text/plain")
        except OSError:
            if script_in_memory:
                return httpresponse.Response(request, script_in_memory, content_type="text/plain")
            else:
                return httpresponse.Response(request, "No script found", status=404)
    
    @server.route("/upload", httpmethods.POST)
    def upload_script(request):
        try:
            content = request.body.decode("utf-8")
            if save_script(content):
                return httpresponse.Response(request, "Enhanced script uploaded successfully")
            else:
                return httpresponse.Response(request, "Failed to save script", status=500)
        except Exception as e:
            return httpresponse.Response(request, f"Error: {str(e)}", status=500)
    
    @server.route("/execute", httpmethods.POST)
    def execute_badusb(request):
        try:
            if execute_script():
                return httpresponse.Response(request, "Enhanced attack executed successfully")
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
                        return httpresponse.Response(request, '{"status": "success", "message": "Enhanced script uploaded"}', 
                                                  content_type="application/json")
                    else:
                        return httpresponse.Response(request, '{"status": "error", "message": "Failed to save script"}', 
                                                  status=500, content_type="application/json")
                
                elif action == "execute":
                    if execute_script():
                        return httpresponse.Response(request, '{"status": "success", "message": "Enhanced script executed"}', 
                                                  content_type="application/json")
                    else:
                        return httpresponse.Response(request, '{"status": "error", "message": "Failed to execute script"}', 
                                                  status=500, content_type="application/json")
                
                elif action == "shortcuts":
                    return httpresponse.Response(request, json.dumps({"shortcuts": COMMAND_SHORTCUTS}),
                                               content_type="application/json")
                
                else:
                    return httpresponse.Response(request, '{"status": "error", "message": "Invalid action"}', 
                                              status=400, content_type="application/json")
                
            except ValueError:
                if save_script(content):
                    if execute_script():
                        return httpresponse.Response(request, "Enhanced script uploaded and executed successfully")
                    else:
                        return httpresponse.Response(request, "Script uploaded but execution failed", status=500)
                else:
                    return httpresponse.Response(request, "Failed to save script", status=500)
                
        except Exception as e:
            return httpresponse.Response(request, f'{{"status": "error", "message": "{str(e)}"}}', 
                                      status=500, content_type="application/json")
    
    print("Starting enhanced server on port 80...")
    try:
        server.start(port=80)
        return server
    except Exception as e:
        print(f"Server error: {e}")
        return None

def main():
    print("Starting KEYOES BadUSB Enhanced...")
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
