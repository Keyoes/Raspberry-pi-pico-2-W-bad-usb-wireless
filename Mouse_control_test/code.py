import time, json, wifi, socketpool, microcontroller
import adafruit_httpserver.server as httpserver
import adafruit_httpserver.response as httpresponse
import adafruit_httpserver.methods as httpmethods
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
import usb_hid

# Status LED, WiFi, script storage, key parsing and the serving loop live in
# lib/badusb_core.py, shared with the keyboard-only build so a fix lands once.
import badusb_core

led = badusb_core.led
badusb_core.blink(3)

WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SCRIPT_PATH = "/badusb_script.txt"
SCRIPT_DIR = "/scripts"
WWW_ROOT = "/www"

# Commands this build understands on top of the shared set, so the
# validator and the dry run do not report them as unknown.
MOUSE_COMMANDS = (
    "MOUSE_CLICK", "MOUSE_MOVE", "MOUSE_PRESS", "MOUSE_RELEASE",
    "MOUSE_DRAG", "MOUSE_SPEED", "SCROLL_UP", "SCROLL_DOWN",
)


def _json(request, payload, status=200, headers=None):
    """JSON response built with json.dumps, never string formatting."""
    return httpresponse.Response(
        request,
        json.dumps(payload),
        status=status,
        content_type="application/json",
        headers=headers,
    )

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

badusb_core.configure(
    ssid=WIFI_SSID,
    password=WIFI_PASSWORD,
    keyboard=keyboard,
    keyboard_layout=keyboard_layout,
    key_mapping=KEY_MAPPING,
    script_path=SCRIPT_PATH,
    script_dir=SCRIPT_DIR,
)

check_wifi_connection = badusb_core.check_wifi_connection
connect_to_wifi = badusb_core.connect_to_wifi
save_script = badusb_core.save_script
parse_key_combo = badusb_core.parse_key_combo
execute_key_combination = badusb_core.execute_key_combination

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
    try:
        script_lines = badusb_core.load_script_lines()
        if script_lines is None:
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
    # No root_path: every response is produced by a route below, and pointing
    # it at a directory would expose the device's files (settings.toml, the
    # stored script) over HTTP. "/static" did not exist in the first place.
    server = httpserver.Server(pool)


    @server.route("/", httpmethods.GET)
    def base(request):
        # The page lives in /www on the device, not as a string literal in
        # here, so it no longer has to sit in RAM per request.
        return badusb_core.page_response(request, root=WWW_ROOT)
    
    @server.route("/script", httpmethods.GET)
    def get_script(request):
        content = badusb_core.read_script()
        if content is None:
            return httpresponse.Response(request, "No script found", status=404)

        return httpresponse.Response(request, content, content_type="text/plain")
    
    @server.route("/upload", httpmethods.POST)
    def upload_script(request):
        try:
            content = request.body.decode("utf-8")
            detail = save_script(content)
            return httpresponse.Response(request, f"Enhanced script uploaded: {detail}")
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
        headers = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
        try:
            return _json(request, badusb_core.status_snapshot(), headers=headers)
        except Exception as e:
            return _json(request, {"connected": False, "error": str(e)}, headers=headers)

    @server.route("/validate", httpmethods.POST)
    def validate(request):
        """Report what is wrong with a script. Sends no keystrokes."""
        try:
            problems = badusb_core.validate_script(
                request.body.decode("utf-8"), extra_commands=MOUSE_COMMANDS
            )
            return _json(request, {
                "ok": not problems,
                "problems": [
                    {"line": number, "text": text, "message": message}
                    for number, text, message in problems
                ],
            })
        except Exception as e:
            return _json(request, {"error": str(e)}, status=500)

    @server.route("/dry-run", httpmethods.POST)
    def dry_run(request):
        """Describe what a script would do. Sends no keystrokes."""
        try:
            text = request.body.decode("utf-8") or badusb_core.read_script()
            if not text:
                return _json(request, {"error": "no script given or stored"}, status=404)

            return _json(request, {
                "steps": badusb_core.explain_script(text, extra_commands=MOUSE_COMMANDS)
            })
        except Exception as e:
            return _json(request, {"error": str(e)}, status=500)

    @server.route("/scripts", httpmethods.GET)
    def scripts_list(request):
        return _json(request, {"scripts": badusb_core.list_scripts()})

    @server.route("/scripts", httpmethods.POST)
    def scripts_write(request):
        """Save, load or delete a named script in the library.

        Body: {"action": "save"|"load"|"delete", "name": ..., "script": ...}
        """
        try:
            data = json.loads(request.body.decode("utf-8"))
            action = data.get("action", "")
            name = data.get("name", "")

            if action == "save":
                badusb_core.save_named_script(name, data.get("script", ""))
                return _json(request, {"status": "success", "name": name})

            if action == "load":
                content = badusb_core.load_named_script(name)
                if content is None:
                    return _json(request, {"error": f"no script named {name!r}"}, status=404)
                detail = badusb_core.save_script(content)
                return _json(request, {"status": "success", "name": name, "detail": detail})

            if action == "delete":
                if not badusb_core.delete_named_script(name):
                    return _json(request, {"error": f"no script named {name!r}"}, status=404)
                return _json(request, {"status": "success", "name": name})

            return _json(request, {"error": f"unknown action {action!r}"}, status=400)
        except ValueError as e:
            return _json(request, {"error": str(e)}, status=400)
        except Exception as e:
            return _json(request, {"error": str(e)}, status=500)

    @server.route("/api/badusb", httpmethods.POST)
    def api_badusb(request):
        try:
            content = request.body.decode("utf-8")
            
            try:
                data = json.loads(content)
                action = data.get("action", "")
                
                if action == "upload" and "script" in data:
                    detail = save_script(data["script"])
                    return httpresponse.Response(
                        request,
                        json.dumps({"status": "success",
                                    "message": f"Enhanced script uploaded: {detail}"}),
                        content_type="application/json",
                    )

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
                detail = save_script(content)
                if execute_script():
                    return httpresponse.Response(
                        request, f"Enhanced script uploaded ({detail}) and executed successfully"
                    )
                return httpresponse.Response(
                    request, f"Script uploaded ({detail}) but execution failed", status=500
                )

        except Exception as e:
            # json.dumps, not an f-string: an exception message containing a
            # quote or backslash used to produce invalid JSON here.
            return httpresponse.Response(request, json.dumps({"status": "error", "message": str(e)}),
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
    badusb_core.connect_to_wifi()
    server = setup_server()

    if server:
        led.value = True
        time.sleep(1)
        led.value = False

        badusb_core.serve_forever(server, setup_server)
    else:
        badusb_core.blink(5, on=0.1, off=0.1)
        microcontroller.reset()

if __name__ == "__main__":
    main()
