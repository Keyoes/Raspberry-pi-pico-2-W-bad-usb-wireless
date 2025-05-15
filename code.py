import os
import time
import json
import board
import digitalio
import microcontroller
import wifi
import socketpool
import ssl
import adafruit_httpserver.server as httpserver
import adafruit_httpserver.request as httprequest
import adafruit_httpserver.response as httpresponse
import adafruit_httpserver.methods as httpmethods

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
import usb_hid

# Configurare LED pentru indicarea statusului
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Flash LED de 3 ori pentru a indica pornirea sistemului
for _ in range(3):
    led.value = True
    time.sleep(0.2)
    led.value = False
    time.sleep(0.2)

# Parametri WiFi - schimbați cu datele voastre
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"

# Path pentru fișierul cu scriptul Bad USB
SCRIPT_PATH = "/badusb_script.txt"

# Dicționar pentru maparea stringurilor de taste la codurile de taste
KEY_MAPPING = {
    "CTRL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT,
    "ALT": Keycode.ALT,
    "GUI": Keycode.GUI,
    "WINDOWS": Keycode.GUI,
    "WIN": Keycode.GUI,
    "ENTER": Keycode.ENTER,
    "RETURN": Keycode.RETURN,
    "ESC": Keycode.ESCAPE,
    "ESCAPE": Keycode.ESCAPE,
    "BACKSPACE": Keycode.BACKSPACE,
    "TAB": Keycode.TAB,
    "SPACE": Keycode.SPACE,
    "CAPSLOCK": Keycode.CAPS_LOCK,
    "DELETE": Keycode.DELETE,
    "END": Keycode.END,
    "HOME": Keycode.HOME,
    "INSERT": Keycode.INSERT,
    "NUMLOCK": Keycode.KEYPAD_NUMLOCK,
    "PAGEUP": Keycode.PAGE_UP,
    "PAGEDOWN": Keycode.PAGE_DOWN,
    "PRINTSCREEN": Keycode.PRINT_SCREEN,
    "SCROLLLOCK": Keycode.SCROLL_LOCK,
    "PAUSE": Keycode.PAUSE,
    "UP": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
    "F1": Keycode.F1,
    "F2": Keycode.F2,
    "F3": Keycode.F3,
    "F4": Keycode.F4,
    "F5": Keycode.F5,
    "F6": Keycode.F6,
    "F7": Keycode.F7,
    "F8": Keycode.F8,
    "F9": Keycode.F9,
    "F10": Keycode.F10,
    "F11": Keycode.F11,
    "F12": Keycode.F12,
    "MENU": Keycode.APPLICATION,
    "APP": Keycode.APPLICATION,
    "A": Keycode.A,
    "B": Keycode.B,
    "C": Keycode.C,
    "D": Keycode.D,
    "E": Keycode.E,
    "F": Keycode.F,
    "G": Keycode.G,
    "H": Keycode.H,
    "I": Keycode.I,
    "J": Keycode.J,
    "K": Keycode.K,
    "L": Keycode.L,
    "M": Keycode.M,
    "N": Keycode.N,
    "O": Keycode.O,
    "P": Keycode.P,
    "Q": Keycode.Q,
    "R": Keycode.R,
    "S": Keycode.S,
    "T": Keycode.T,
    "U": Keycode.U,
    "V": Keycode.V,
    "W": Keycode.W,
    "X": Keycode.X,
    "Y": Keycode.Y,
    "Z": Keycode.Z
}

# Inițializare tastatură HID - folosind dispozitivul nostru custom fără nume
keyboard = Keyboard(usb_hid.devices[0])
keyboard_layout = KeyboardLayoutUS(keyboard)

def check_wifi_connection():
    """Verifică starea conexiunii WiFi și încearcă reconectarea dacă este necesară"""
    if not wifi.radio.connected:
        print("WiFi connection lost. Attempting to reconnect...")
        connect_to_wifi()  # Această funcție va încerca până reușește
        return wifi.radio.connected
    return True  # Conexiunea este activă

def connect_to_wifi():
    """Conectare la rețeaua WiFi configurată cu încercări repetate"""
    max_attempts = 10  # Numărul maxim de încercări înainte de a semnala un eșec temporar
    retry_delay = 5    # Secunde între încercări
    attempt = 0
    
    while True:  # Buclă infinită pentru a încerca mereu reconectarea
        attempt += 1
        print(f"Connecting to {WIFI_SSID}... (Attempt {attempt})")
        
        try:
            # Semnalăm încercarea de conectare cu LED-ul
            led.value = True
            time.sleep(0.2)
            led.value = False
            
            # Încercăm să ne conectăm la WiFi
            wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
            
            # Dacă ajungem aici, conexiunea a reușit
            print(f"Connected to {WIFI_SSID}")
            print(f"IP Address: {wifi.radio.ipv4_address}")
            
            # Semnalăm succesul conexiunii cu 2 blink-uri scurte
            for _ in range(2):
                led.value = True
                time.sleep(0.2)
                led.value = False
                time.sleep(0.2)
                
            return True
            
        except Exception as e:
            print(f"Failed to connect to WiFi: {e}")
            
            # Semnalăm eșecul conectării cu un blink lung
            led.value = True
            time.sleep(1)
            led.value = False
            
            # Dacă am atins numărul maxim de încercări, semnalăm acest lucru
            if attempt % max_attempts == 0:
                print(f"Reached {max_attempts} consecutive failed attempts.")
                # Semnalăm acest lucru cu 5 blink-uri rapide
                for _ in range(5):
                    led.value = True
                    time.sleep(0.1)
                    led.value = False
                    time.sleep(0.1)
                
                # Încercăm să restartăm microcontroller-ul dacă conexiunea eșuează în mod repetat
                try:
                    microcontroller.reset()
                except:
                    pass
            
            # Așteptăm înainte de a încerca din nou
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

def main():
    """Funcția principală"""
    # Încercăm să ne conectăm la WiFi până reușim
    connect_to_wifi()  # Acum această funcție va încerca până reușește
    
    # Configurăm și pornim serverul
    server = setup_server()
    
    # Timp pentru ultima verificare a conexiunii
    last_wifi_check = time.monotonic()
    wifi_check_interval = 60  # Verifică conexiunea la fiecare 60 secunde
    
    if server:
        # Indicăm că serverul rulează cu success printr-un blink lung
        led.value = True
        time.sleep(1)
        led.value = False
        
        try:
            # Menținem serverul activ
            while True:
                try:
                    server.poll()
                except Exception as e:
                    print(f"Error during server poll: {e}")
                    # Verificăm conexiunea WiFi înainte de a încerca să repornind serverul
                    if check_wifi_connection():
                        # Încercăm să restartăm serverul
                        print("Trying to restart server...")
                        server = setup_server()
                        if not server:
                            # Dacă serverul nu pornește, restartăm dispozitivul
                            microcontroller.reset()
                
                # Verificăm periodic conexiunea WiFi
                current_time = time.monotonic()
                if current_time - last_wifi_check > wifi_check_interval:
                    print("Running scheduled WiFi connection check...")
                    if not check_wifi_connection():
                        # Dacă conexiunea WiFi a eșuat, încercăm să repornind serverul după reconectare
                        print("Server may need restart after WiFi reconnection...")
                        server = setup_server()
                        if not server:
                            # Dacă serverul nu pornește, restartăm dispozitivul
                            microcontroller.reset()
                    last_wifi_check = time.monotonic()
                
                time.sleep(0.1)  # Mică pauză pentru a preveni utilizarea excesivă a CPU
                
        except Exception as e:
            print(f"Server polling error: {e}")
            # Verificăm conexiunea înainte de a încerca repornirea
            check_wifi_connection()
            # Încercăm să repornm serverul sau restartăm microcontroller-ul
            try:
                server = setup_server()
                if not server:
                    microcontroller.reset()
            except:
                microcontroller.reset()
    else:
        # Indicăm că serverul nu a putut porni cu 5 blinkuri rapide
        for _ in range(5):
            led.value = True
            time.sleep(0.1)
            led.value = False
            time.sleep(0.1)
        # Dacă serverul nu pornește după mai multe încercări, restartăm dispozitivul
        microcontroller.reset()
def save_script(script_content):
    """Salvează scriptul Bad USB într-un fișier"""
    try:
        # Verificăm dacă fișierul există deja și îl ștergem pentru a evita erori de filesystem
        try:
            os.remove(SCRIPT_PATH)
        except OSError:
            pass  # Ignorăm dacă fișierul nu există
        
        with open(SCRIPT_PATH, "w") as f:
            f.write(script_content)
        return True
    except Exception as e:
        print(f"Error saving script: {e}")
        # Încercăm să salvăm în memorie dacă filesystem-ul nu permite
        global script_in_memory
        script_in_memory = script_content
        return True

# Variabilă pentru a stoca scriptul în memorie dacă filesystem-ul dă erori
script_in_memory = None

def parse_key_combo(key_combo):
    """Parsează o combinație de taste și returnează lista de keycodes"""
    keys = []
    # Verificăm dacă avem o combinație cu +
    if "+" in key_combo:
        parts = key_combo.split("+")
        for part in parts:
            part = part.strip().upper()
            if part in KEY_MAPPING:
                keys.append(KEY_MAPPING[part])
    else:
        # Splitim după spații pentru format alternativ
        parts = key_combo.split()
        for part in parts:
            part = part.strip().upper()
            if part in KEY_MAPPING:
                keys.append(KEY_MAPPING[part])
    
    return keys

def execute_script():
    """Citește și execută scriptul Bad USB linie cu linie cu timing îmbunătățit"""
    global script_in_memory
    
    try:
        # Încercăm să citim din fișier
        try:
            with open(SCRIPT_PATH, "r") as f:
                script_lines = f.readlines()
        except OSError:
            # Dacă nu putem citi din fișier, folosim scriptul din memorie
            if script_in_memory:
                script_lines = script_in_memory.splitlines()
            else:
                print("No script found in file or memory")
                return False
        
        # Setăm un delay de bază între caractere pentru scrierea de text
        char_delay = 0.01  # 10ms între caractere
        
        for line in script_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Luminează LED-ul în timpul executării comenzii
            led.value = True
            
            parts = line.split(" ", 1)
            command = parts[0].upper()
            
            if command == "STRING":
                if len(parts) > 1:
                    # Pentru fiecare caracter, adăugăm un mic delay
                    text = parts[1]
                    for char in text:
                        keyboard_layout.write(char)
                        time.sleep(char_delay)  # Delay între caractere
                        
                    # Delay suplimentar după un șir complet
                    time.sleep(0.05)
            elif command == "DELAY":
                if len(parts) > 1:
                    try:
                        delay_ms = int(parts[1])
                        time.sleep(delay_ms / 1000.0)
                    except ValueError:
                        print(f"Invalid delay value: {parts[1]}")
            elif command == "CHAR_DELAY":
                # Comandă nouă pentru a schimba delay-ul dintre caractere
                if len(parts) > 1:
                    try:
                        char_delay = float(parts[1]) / 1000.0  # conversia din ms în secunde
                        print(f"Character delay set to {char_delay}s")
                    except ValueError:
                        print(f"Invalid CHAR_DELAY value: {parts[1]}")
            elif command == "REM" or command.startswith("//"):
                # Comentariu - nu face nimic
                pass
            elif command in KEY_MAPPING:
                keyboard.press(KEY_MAPPING[command])
                time.sleep(0.1)  # Delay mai lung pentru taste speciale
                keyboard.release(KEY_MAPPING[command])
                time.sleep(0.05)  # Delay după eliberarea tastei
            elif "+" in line:
                # Combinație de taste (ex: CTRL+ALT+T)
                execute_key_combination(line)
                time.sleep(0.1)  # Delay după combinație
            else:
                # Încercăm să procesăm ca o combinație de taste
                execute_key_combination(line)
                time.sleep(0.05)  # Delay după comandă
            
            # Stingem LED-ul după executarea comenzii
            led.value = False
            time.sleep(0.1)  # Delay între comenzi
        
        return True
    except Exception as e:
        print(f"Error executing script: {e}")
        led.value = False
        return False

def execute_key_combination(key_combo):
    """Execută o combinație de taste cu timing îmbunătățit"""
    keycodes = parse_key_combo(key_combo)
    
    if keycodes:
        try:
            # Apăsăm tastele una câte una, cu un mic delay între ele
            for key in keycodes:
                keyboard.press(key)
                time.sleep(0.05)
            
            # Ținem tastele apăsate puțin mai mult
            time.sleep(0.15)
            
            # Eliberăm tastele în ordine inversă
            for key in reversed(keycodes):
                keyboard.release(key)
                time.sleep(0.05)
            
            # Delay suplimentar după eliberarea tuturor tastelor
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"Error executing key combination: {e}")
            # Eliberăm toate tastele pentru siguranță
            keyboard.release_all()
            time.sleep(0.1)
            return False
    return False


def setup_server():
    """Configurează și pornește serverul HTTP"""
    pool = socketpool.SocketPool(wifi.radio)
    server = httpserver.Server(pool, "/static")
    
    # Variabile globale pentru a stoca istoricul payloads și statusul WiFi
    payload_history = []
    wifi_status = {"connected": True, "ip": str(wifi.radio.ipv4_address) if wifi.radio.connected else "Not connected"}
    
    @server.route("/", httpmethods.GET)
    def base(request):
        """Handler pentru pagina principală"""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Keyoes BadUSB Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --kali-bg: #121212;
            --kali-terminal-bg: #000000;
            --kali-border: #444444;
            --kali-text: #ffffff;
            --kali-accent: #0abab5;
            --kali-header: #1a1a1a;
            --kali-button: #333333;
            --kali-button-hover: #555555;
            --kali-shadow: rgba(0, 0, 0, 0.5);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body { 
            font-family: 'Ubuntu Mono', 'Courier New', monospace; 
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
            padding: 10px 0;
            margin-bottom: 20px;
            text-align: center;
            position: relative;
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
            color: #ff5f56;
            letter-spacing: 1px;
            text-transform: uppercase;
            border: 1px solid #ff5f56;
            padding: 3px 10px;
            border-radius: 3px;
            background-color: rgba(255, 95, 86, 0.1);
        }
        
        /* Enhanced RGB Effect for KEYOES */
        .rgb-text {
            background-image: linear-gradient(90deg, 
                #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #8f00ff, #ff0000);
            background-size: 200% auto;
            color: #000;
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: rgb-animation 3s linear infinite;
            text-shadow: 
                0 0 10px rgba(255, 0, 0, 0.5),
                0 0 20px rgba(255, 255, 255, 0.3),
                0 0 30px rgba(255, 0, 0, 0.2);
            font-weight: bold;
            font-size: 30px;
            letter-spacing: 2px;
            filter: brightness(1.2) contrast(1.2);
        }
        

        /* WiFi status indicator */
        .wifi-status {
            position: absolute;
            top: 10px;
            right: 15px;
            display: flex;
            align-items: center;
            font-size: 12px;
            background-color: var(--kali-terminal-bg);
            padding: 5px 10px;
            border-radius: 20px;
            border: 1px solid var(--kali-border);
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
            background-color: #27c93f;
            box-shadow: 0 0 5px #27c93f;
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
            background: linear-gradient(to right, #333333, #222222);
            padding: 8px 15px;
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
            padding: 10px;
            position: relative;
        }
        
        #script {
            width: 100%;
            min-height: 350px;
            background-color: transparent;
            color: var(--kali-text);
            border: none;
            font-family: 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
            outline: none;
            padding: 10px;
            white-space: pre-wrap;
        }
        
        .button-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }
        
        button {
            background-color: var(--kali-button);
            color: var(--kali-text);
            border: 1px solid var(--kali-border);
            border-radius: 3px;
            padding: 10px 15px;
            font-family: 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            cursor: pointer;
            transition: background-color 0.2s;
            min-width: 120px;
        }
        
        button:hover {
            background-color: var(--kali-button-hover);
        }
        
        .output-window {
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-radius: 5px;
            padding: 10px;
            margin-top: 20px;
            height: 80px;
            overflow-y: auto;
            font-family: 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            position: relative;
        }
        
        .output-window::before {
            content: "root@kali:~# ";
            color: var(--kali-accent);
        }
        
        .cursor {
            display: inline-block;
            width: 8px;
            height: 14px;
            background-color: var(--kali-text);
            animation: blink 1s step-end infinite;
            vertical-align: middle;
            margin-left: 3px;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
        
        .footer {
            text-align: center;
            margin-top: 20px;
            padding: 10px 0;
            font-size: 12px;
            color: #888888;
            border-top: 1px solid var(--kali-border);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .button-container {
                flex-direction: column;
                align-items: stretch;
            }
            
            button {
                width: 100%;
                margin-bottom: 5px;
            }
            
            #script {
                min-height: 250px;
            }
            
            .logo {
                font-size: 20px;
            }
            
            .tab-panel {
                flex-direction: column;
            }
            
            .tab {
                margin-right: 0;
                margin-bottom: 5px;
            }
        }
        
        /* Command history */
        .command-history {
            margin-top: 20px;
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-radius: 5px;
            padding: 10px;
            max-height: 150px;
            overflow-y: auto;
        }
        
        .history-title {
            color: var(--kali-accent);
            font-size: 14px;
            margin-bottom: 5px;
            border-bottom: 1px solid var(--kali-border);
            padding-bottom: 5px;
        }
        
        .history-item {
            font-size: 12px;
            padding: 3px 0;
            border-bottom: 1px dotted var(--kali-border);
        }
        
        .history-item:last-child {
            border-bottom: none;
        }
        
        .history-timestamp {
            color: #888888;
            margin-right: 10px;
        }
        
        .history-command {
            color: var(--kali-text);
        }
        
        .history-status {
            float: right;
            color: var(--kali-accent);
        }
        
        .history-status.fail {
            color: #ff5f56;
        }
        
        /* Payloads section */
        .tab-panel {
            display: flex;
            margin-top: 20px;
            border-bottom: 1px solid var(--kali-border);
        }
        
        .tab {
            padding: 8px 15px;
            background-color: var(--kali-button);
            border: 1px solid var(--kali-border);
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .tab.active {
            background-color: var(--kali-accent);
            color: #000000;
        }
        
        .tab:hover {
            background-color: var(--kali-button-hover);
        }
        
        .tab.active:hover {
            background-color: var(--kali-accent);
        }
        
        .tab-content {
            display: none;
            background-color: var(--kali-terminal-bg);
            border: 1px solid var(--kali-border);
            border-top: none;
            border-radius: 0 0 5px 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .payloads-container {
            max-height: 200px;
            overflow-y: auto;
        }
        
        .payload-item {
            background-color: rgba(10, 186, 181, 0.1);
            border-left: 3px solid var(--kali-accent);
            margin-bottom: 10px;
            padding: 8px;
            font-size: 13px;
            word-break: break-all;
        }
        
        .payload-timestamp {
            font-weight: bold;
            color: var(--kali-accent);
            margin-bottom: 3px;
        }
        
        .payload-content {
            white-space: pre-wrap;
            font-family: 'Ubuntu Mono', 'Courier New', monospace;
        }
        
        .keyboard-shortcut {
            background-color: var(--kali-button);
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 12px;
            margin-left: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-top">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 10px;">
                    <path d="M12 2L2 7V15L12 20L22 15V7L12 2Z" stroke="#0abab5" stroke-width="2" fill="none"/>
                    <path d="M12 6L7 8.5V13.5L12 16L17 13.5V8.5L12 6Z" fill="#0abab5"/>
                </svg>
                <span class="rgb-text">KEYOES</span>
            </div>
            <div class="subtitle">DO NOT USE FOR MALICIOUS PURPOSES!</div>
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
                        root@kali: ~/badusb_attack
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
            </div>
            
            <div class="output-window">
                <span id="status">System ready. Waiting for command...</span><span class="cursor"></span>
            </div>
            
            <div class="command-history">
                <div class="history-title">Command History</div>
                <div id="history-content">
                    <!-- History items will be added here via JavaScript -->
                </div>
            </div>
        </div>
        
        <div id="payloads-tab" class="tab-content">
            <div class="history-title">Executed Payloads <small>(Session only - not stored permanently)</small></div>
            <div class="payloads-container" id="payloads-content">
                <!-- Payloads will be added here via JavaScript -->
                <div class="payload-item">
                    <div class="payload-timestamp">No payloads executed yet</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><span class="rgb-text" style="font-size: 14px;">KEYOES</span> Evil Controller v2 | Raspberry Pi Pico 2 W | Kali Terminal Interface</p>
        </div>
    </div>

    <script>
        // Historial de comenzi
        let commandHistory = [];
        let payloadHistory = [];
        
        function addToHistory(command, status) {
            const now = new Date();
            const timestamp = now.toLocaleTimeString();
            
            commandHistory.unshift({
                time: timestamp,
                command: command,
                status: status
            });
            
            // Limităm istoricul la 10 comenzi
            if (commandHistory.length > 10) {
                commandHistory.pop();
            }
            
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
                    <span class="history-timestamp">[${item.time}]</span>
                    <span class="history-command">${item.command}</span>
                    <span class="history-status ${statusClass}">${item.status}</span>
                `;
                
                historyContent.appendChild(historyItem);
            });
        }
        
        function addToPayloadHistory(scriptContent) {
            const now = new Date();
            const timestamp = now.toLocaleTimeString() + ' ' + now.toLocaleDateString();
            
            payloadHistory.unshift({
                time: timestamp,
                content: scriptContent
            });
            
            // Limităm istoricul la 20 de payloads
            if (payloadHistory.length > 20) {
                payloadHistory.pop();
            }
            
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
            // Dezactivăm toate tab-urile și conținutul
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Activăm tab-ul selectat
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
                headers: {
                    'Content-Type': 'text/plain'
                }
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
            
            fetch('/execute', {
                method: 'POST'
            })
            .then(response => response.text())
            .then(data => {
                document.getElementById('status').innerHTML = data;
                addToHistory("EXECUTE", "success");
                
                // Adăugăm scriptul la istoricul de payloads
                if (script && script.trim() !== '') {
                    addToPayloadHistory(script);
                }
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
        
// Variabile pentru starea conexiunii
        let lastPingTime = Date.now();
        let connectionLost = false;
        let connectionCheckInterval;
        
        // Verifică și actualizează statusul WiFi
        function checkWifiStatus() {
            fetch('/wifi-status?t=' + Date.now(), {
                // Adăugăm un timeout pentru a detecta mai rapid deconectările
                signal: AbortSignal.timeout(3000)
            })
            .then(response => response.json())
            .then(data => {
                // Resetăm timpul ultimului ping reușit
                lastPingTime = Date.now();
                connectionLost = false;
                
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.wifi-status span');
                
                if (data.connected) {
                    indicator.className = 'status-indicator status-connected';
                    statusText.textContent = `WiFi: ${data.ip}`;
                    indicator.style.backgroundColor = '#27c93f';
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
                
                // Marcăm conexiunea ca pierdută
                connectionLost = true;
                indicator.className = 'status-indicator';
                indicator.style.backgroundColor = '#ff5f56';
                statusText.textContent = 'Connection Lost';
            });
        }
        
        // Funcție pentru a verifica dacă dispozitivul este offline
        function checkOfflineStatus() {
            const now = Date.now();
            // Dacă nu am primit răspuns în ultimele 20 secunde, considerăm dispozitivul offline
            if (now - lastPingTime > 20000 && !connectionLost) {
                connectionLost = true;
                const indicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.wifi-status span');
                
                indicator.className = 'status-indicator';
                indicator.style.backgroundColor = '#ff5f56';
                statusText.textContent = 'Device Offline';
            }
        }
        
        // Verificăm statusul WiFi la fiecare minut
        connectionCheckInterval = setInterval(checkWifiStatus, 60000); // Verifică la fiecare minut
        
        // Verificăm statusul offline la fiecare 5 secunde
        setInterval(checkOfflineStatus, 5000);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            // Ctrl+P pentru a schimba la tab-ul Payloads
            if (event.ctrlKey && event.key === 'p') {
                event.preventDefault();
                switchTab('payloads');
            }
            
            // Ctrl+T pentru a schimba la tab-ul Terminal
            if (event.ctrlKey && event.key === 't') {
                event.preventDefault();
                switchTab('terminal');
            }
        });
        
// Inițializare la încărcare
window.onload = function() {
    addToHistory("SYSTEM BOOT", "success");
    checkWifiStatus(); // Verifică statusul WiFi inițial
    
    // Verifică statusul WiFi la fiecare 10 secunde pentru primele 2 minute
    // pentru a asigura o detectare rapidă inițială
    let initialChecks = 0;
    const initialInterval = setInterval(() => {
        checkWifiStatus();
        initialChecks++;
        if (initialChecks >= 12) { // 12 verificări = 2 minute
            clearInterval(initialInterval);
        }
    }, 10000);
};
    </script>
</body>
</html>
        """
        return httpresponse.Response(request, html, content_type="text/html")
    
    @server.route("/upload", httpmethods.POST)
    def upload_script(request):
        """Handler pentru încărcarea scriptului"""
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
        """Handler pentru executarea scriptului"""
        try:
            if execute_script():
                # Adăugăm la istoricul de payloads (doar în interfață, nu stocăm)
                return httpresponse.Response(request, "Attack executed successfully")
            else:
                return httpresponse.Response(request, "Failed to execute script", status=500)
        except Exception as e:
            return httpresponse.Response(request, f"Error: {str(e)}", status=500)

    # Endpoint pentru verificarea statusului WiFi
    @server.route("/wifi-status", httpmethods.GET)
    def wifi_status_check(request):
        """Handler pentru verificarea statusului WiFi"""
        try:
            # Verificăm conexiunea WiFi în timp real
            is_connected = wifi.radio.connected

            # Adăugăm și timestamp pentru a preveni caching-ul
            status = {
                "connected": is_connected,
                "ip": str(wifi.radio.ipv4_address) if is_connected else "Not connected",
                "timestamp": time.time()
            }

            # Adăugăm un header no-cache pentru a preveni caching-ul
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
    
    # Endpoint API pentru utilizare programatică
    @server.route("/api/badusb", httpmethods.POST)
    def api_badusb(request):
        """API endpoint pentru control programatic"""
        try:
            content = request.body.decode("utf-8")
            
            # Verificăm dacă conținutul este JSON
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
                # Dacă nu este JSON, tratăm ca script text direct
                if save_script(content):
                    # Executăm imediat scriptul
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
if __name__ == "__main__":
    main()
