import time, json, wifi, socketpool, microcontroller
import adafruit_httpserver.server as httpserver
import adafruit_httpserver.response as httpresponse
import adafruit_httpserver.methods as httpmethods
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
import usb_hid

# Status LED, WiFi, script storage, key parsing and the serving loop live in
# lib/badusb_core.py, shared with the mouse build so a fix lands once.
import badusb_core

led = badusb_core.led
# Short blinks: still plainly three of them, but 0.48 s rather than the
# 1.2 s the old 0.2/0.2 timing cost before anything else could start.
badusb_core.blink(3, on=0.08, off=0.08)
badusb_core.report_board()   # one line on serial; useful on a new board

WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
SCRIPT_PATH = "/badusb_script.txt"
SCRIPT_DIR = "/scripts"
WWW_ROOT = "/www"

# Must stay above badusb_core.MAX_BODY_BYTES, since headers share this buffer.
REQUEST_BUFFER_SIZE = 4096


def _json(request, payload, status=200, headers=None):
    """JSON response built with json.dumps, never string formatting.

    Hand-built JSON used to break here as soon as a value contained a
    quote or a backslash.
    """
    return httpresponse.Response(
        request,
        json.dumps(payload),
        status=status,
        content_type="application/json",
        headers=headers,
    )


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

# Holds each key for a few USB frames so the host actually sees it;
# see badusb_core.KEY_HOLD_SECONDS for why characters were dropped.
keyboard = badusb_core.paced_keyboard(Keyboard, usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)

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

def execute_script():
    try:
        script_lines = badusb_core.load_script_lines()
        if script_lines is None:
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
                    # The key hold comes out of char_delay rather than on
                    # top of it, so the character rate the target sees is
                    # unchanged. See badusb_core.type_text.
                    badusb_core.type_text(parts[1], char_delay)
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
    # No root_path: every response is produced by a route below, and pointing
    # it at a directory would expose the device's files (settings.toml, the
    # stored script) over HTTP. "/static" did not exist in the first place.
    server = httpserver.Server(pool)

    # The library defaults this to 1024 bytes, headers included, so a script
    # much over a kilobyte never made it to the handler. Raising it costs
    # that many bytes of RAM permanently, which is why it is a named
    # constant rather than something large and hopeful.
    server.request_buffer_size = REQUEST_BUFFER_SIZE


    @server.route("/", httpmethods.GET)
    def base(request):
        # The page lives in /www on the device, not as a 27 KB string
        # literal in here, so it no longer has to sit in RAM per request.
        # root_path is a dedicated directory holding only web assets.
        return badusb_core.page_response(request, root=WWW_ROOT)

    @server.route("/validate", httpmethods.POST)
    def validate(request):
        """Report what is wrong with a script. Sends no keystrokes."""
        try:
            problems = badusb_core.validate_script(badusb_core.read_body(request))
            return _json(request, {
                "ok": not problems,
                "problems": [
                    {"line": number, "text": text, "message": message}
                    for number, text, message in problems
                ],
            })
        except badusb_core.BodyTooLarge as e:
            return _json(request, {"error": str(e)}, status=413)
        except Exception as e:
            return _json(request, {"error": str(e)}, status=500)

    @server.route("/dry-run", httpmethods.POST)
    def dry_run(request):
        """Describe what a script would do. Sends no keystrokes.

        The body is used if there is one, otherwise the stored script is
        described, so you can check what is loaded before firing it.
        """
        try:
            text = badusb_core.read_body(request) or badusb_core.read_script()
            if not text:
                return _json(request, {"error": "no script given or stored"}, status=404)

            return _json(request, {"steps": badusb_core.explain_script(text)})
        except badusb_core.BodyTooLarge as e:
            return _json(request, {"error": str(e)}, status=413)
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
            data = json.loads(badusb_core.read_body(request))
            action = data.get("action", "")
            name = data.get("name", "")

            if action == "save":
                badusb_core.save_named_script(name, data.get("script", ""))
                return _json(request, {"status": "success", "name": name})

            if action == "load":
                content = badusb_core.load_named_script(name)
                if content is None:
                    return _json(request, {"error": f"no script named {name!r}"}, status=404)
                # Loading makes it the active script, which is what /execute runs.
                detail = badusb_core.save_script(content)
                return _json(request, {"status": "success", "name": name, "detail": detail})

            if action == "delete":
                if not badusb_core.delete_named_script(name):
                    return _json(request, {"error": f"no script named {name!r}"}, status=404)
                return _json(request, {"status": "success", "name": name})

            return _json(request, {"error": f"unknown action {action!r}"}, status=400)
        except ValueError as e:
            # Covers both bad JSON and a rejected script name.
            return _json(request, {"error": str(e)}, status=400)
        except badusb_core.BodyTooLarge as e:
            return _json(request, {"error": str(e)}, status=413)
        except Exception as e:
            return _json(request, {"error": str(e)}, status=500)


    @server.route("/upload", httpmethods.POST)
    def upload_script(request):
        try:
            content = badusb_core.read_body(request)
            detail = save_script(content)
            return httpresponse.Response(request, f"Script uploaded: {detail}")
        except badusb_core.BodyTooLarge as e:
            return httpresponse.Response(request, f"Refused: {e}", status=413)
        except Exception as e:
            return httpresponse.Response(request, f"Error: {str(e)}", status=500)
    
    @server.route("/verify", httpmethods.POST)
    def verify_link(request):
        """Check the host is actually receiving keystrokes.

        Presses Num Lock and waits for the host to report the LED state
        back, then presses it again to leave the target as it was. This is
        the only acknowledgement USB HID offers, so it is the only way to
        tell a working cable from a payload typing into nothing.
        """
        ok, detail = badusb_core.verify_host_link()
        payload = {"ok": ok, "usb_connected": badusb_core.usb_host_connected()}
        payload.update(detail)
        return _json(request, payload, status=200 if ok else 503)

    @server.route("/execute", httpmethods.POST)
    def execute_badusb(request):
        try:
            if badusb_core.usb_host_connected() is False:
                # Running a payload with nothing plugged in used to report
                # success. It types into nothing.
                return httpresponse.Response(
                    request,
                    "No USB host attached; nothing would be typed",
                    status=503,
                )

            if execute_script():
                return httpresponse.Response(request, "Attack executed successfully")
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
    
    @server.route("/api/badusb", httpmethods.POST)
    def api_badusb(request):
        try:
            content = badusb_core.read_body(request)
            
            try:
                data = json.loads(content)
                action = data.get("action", "")
                
                if action == "upload" and "script" in data:
                    detail = save_script(data["script"])
                    return httpresponse.Response(
                        request,
                        json.dumps({"status": "success", "message": f"Script uploaded: {detail}"}),
                        content_type="application/json",
                    )

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
                detail = save_script(content)
                if execute_script():
                    return httpresponse.Response(
                        request, f"Script uploaded ({detail}) and executed successfully"
                    )
                return httpresponse.Response(
                    request, f"Script uploaded ({detail}) but execution failed", status=500
                )
                
        except badusb_core.BodyTooLarge as e:
            return httpresponse.Response(request, json.dumps({"status": "error", "message": str(e)}),
                                      status=413, content_type="application/json")
        except Exception as e:
            # json.dumps, not an f-string: an exception message containing a
            # quote or backslash used to produce invalid JSON here.
            return httpresponse.Response(request, json.dumps({"status": "error", "message": str(e)}),
                                      status=500, content_type="application/json")
    
    print("Starting server on port 80...")
    try:
        server.start(port=80)
        return server
    except Exception as e:
        print(f"Server error: {e}")
        return None


def main():
    badusb_core.connect_to_wifi()
    server = setup_server()

    if server:
        # One long blink to say the server is up. This runs before
        # serve_forever, so every millisecond here is a millisecond the
        # server is bound but not yet answering; 0.3 s reads the same and
        # gets us listening sooner.
        led.value = True
        time.sleep(0.3)
        led.value = False

        badusb_core.serve_forever(server, setup_server)
    else:
        badusb_core.blink(5, on=0.1, off=0.1)
        microcontroller.reset()

if __name__ == "__main__":
    main()
