import time
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

class DuckyInterpreter:
    """Interpret și execută scripturi de tip Rubber Ducky"""
    
    def __init__(self, keyboard, keyboard_layout):
        self.keyboard = keyboard
        self.keyboard_layout = keyboard_layout
        
        # Mapare taste speciale
        self.key_mapping = {
            "CTRL": Keycode.CONTROL,
            "SHIFT": Keycode.SHIFT,
            "ALT": Keycode.ALT,
            "GUI": Keycode.GUI,
            "WINDOWS": Keycode.GUI,
            "COMMAND": Keycode.GUI,
            "ENTER": Keycode.ENTER,
            "RETURN": Keycode.RETURN,
            "ESCAPE": Keycode.ESCAPE,
            "ESC": Keycode.ESCAPE,
            "BACKSPACE": Keycode.BACKSPACE,
            "DELETE": Keycode.DELETE,
            "TAB": Keycode.TAB,
            "CAPSLOCK": Keycode.CAPS_LOCK,
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
            "HOME": Keycode.HOME,
            "END": Keycode.END,
            "INSERT": Keycode.INSERT,
            "PAGEUP": Keycode.PAGE_UP,
            "PAGEDOWN": Keycode.PAGE_DOWN,
            "UP": Keycode.UP_ARROW,
            "DOWN": Keycode.DOWN_ARROW,
            "LEFT": Keycode.LEFT_ARROW,
            "RIGHT": Keycode.RIGHT_ARROW,
            "SPACE": Keycode.SPACE,
            "APP": Keycode.APPLICATION,
            "MENU": Keycode.APPLICATION,
            "PRINTSCREEN": Keycode.PRINT_SCREEN
        }
    
    def execute_line(self, line):
        """Execută o singură linie din scriptul Ducky"""
        line = line.strip()
        if not line or line.startswith("#") or line.upper().startswith("REM "):
            return  # Ignoră comentariile și liniile goale
        
        parts = line.split(" ", 1)
        command = parts[0].upper()
        
        # Avem un parametru?
        param = parts[1] if len(parts) > 1 else ""
        
        # Procesăm comenzile
        if command == "DELAY":
            try:
                delay_time = float(param) / 1000  # Convertim din ms în secunde
                time.sleep(delay_time)
            except ValueError:
                print(f"Eroare la comanda DELAY: {param}")
        
        elif command == "STRING":
            self.keyboard_layout.write(param)
        
        elif command == "REPEAT":
            # Această funcție nu este implementată în acest exemplu
            # Ar necesita un istoric al comenzilor
            print("Comanda REPEAT nu este implementată")
        
        elif "+" in command:
            # Combinație de taste (ex: CTRL+ALT+DELETE)
            keys = command.split("+")
            key_codes = []
            
            for key in keys:
                if key in self.key_mapping:
                    key_codes.append(self.key_mapping[key])
                else:
                    print(f"Tastă necunoscută: {key}")
            
            if key_codes:
                self.keyboard.press(*key_codes)
                time.sleep(0.1)
                self.keyboard.release(*key_codes)
        
        elif command in self.key_mapping:
            # Tastă singulară
            self.keyboard.press(self.key_mapping[command])
            time.sleep(0.1)
            self.keyboard.release(self.key_mapping[command])
        
        else:
            print(f"Comandă necunoscută: {command}")
    
    def execute_script(self, script_content):
        """Execută un script Ducky complet"""
        lines = script_content.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if line:  # Ignoră liniile goale
                self.execute_line(line)
                time.sleep(0.01)  # O mică pauză între comenzi
        
        return True