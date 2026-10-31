"""Tests for lib/badusb_core.py, runnable without a board.

    python3 -m unittest discover -s tests

These cover the logic that is easy to get wrong and impossible to see from
the outside: where a script actually got stored, what the validator makes of
a line, whether the dry run agrees with the executor's dispatch order, and
whether the serving loop rebuilds its socket at the right moment.

Hardware behaviour is out of scope. USB HID, the radio and the HTTP server
are stubbed, so a green run here means the logic holds -- not that the
firmware works on a Pico.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.dirname(__file__))

import circuitpython_stubs as stubs  # noqa: E402


class CoreTestCase(unittest.TestCase):
    """Fresh stubs, a fresh module and a temporary filesystem per test."""

    def setUp(self):
        self.env = stubs.install()
        import badusb_core

        self.core = badusb_core
        self.keyboard = stubs.FakeKeyboard()
        self.tmp = tempfile.mkdtemp()
        stubs.instant_clock(self.core)

        self.core.configure(
            ssid="TestNet",
            password="secret",
            keyboard=self.keyboard,
            keyboard_layout=None,
            key_mapping=stubs.KEY_MAPPING,
            script_path=os.path.join(self.tmp, "active.txt"),
            script_dir=os.path.join(self.tmp, "scripts"),
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestStatusLed(CoreTestCase):
    def test_uses_board_led_when_present(self):
        self.assertEqual(self.core.init_status_led().pin, "GP25")

    def test_falls_back_to_a_stub_when_absent(self):
        stubs.install(with_led=False)
        import badusb_core

        led = badusb_core.init_status_led()
        self.assertEqual(type(led).__name__, "_NoStatusLed")
        led.value = True  # must not raise
        badusb_core.blink(2, on=0, off=0)


class TestScriptStorage(CoreTestCase):
    def test_reports_flash_when_the_write_lands(self):
        self.assertEqual(self.core.save_script("STRING hi\n"), "saved to flash")
        self.assertEqual(self.core.load_script_lines(), ["STRING hi\n"])

    def test_reports_ram_when_the_write_fails(self):
        self.core.configure(
            ssid="TestNet", password="secret", keyboard=self.keyboard,
            keyboard_layout=None, key_mapping=stubs.KEY_MAPPING,
            script_path="/does/not/exist/active.txt",
            script_dir=os.path.join(self.tmp, "scripts"),
        )
        detail = self.core.save_script("STRING fallback")
        self.assertIn("RAM only", detail)
        # Still runnable, just not durable -- which is why the wording differs.
        self.assertEqual(self.core.load_script_lines(), ["STRING fallback"])

    def test_no_script_reads_as_none(self):
        self.assertIsNone(self.core.load_script_lines())
        self.assertIsNone(self.core.read_script())

    def test_successful_write_clears_the_stale_ram_copy(self):
        self.core.configure(
            ssid="n", password="p", keyboard=self.keyboard, keyboard_layout=None,
            key_mapping=stubs.KEY_MAPPING, script_path="/does/not/exist/x.txt",
            script_dir=os.path.join(self.tmp, "scripts"),
        )
        self.core.save_script("OLD")
        good = os.path.join(self.tmp, "active.txt")
        self.core.configure(
            ssid="n", password="p", keyboard=self.keyboard, keyboard_layout=None,
            key_mapping=stubs.KEY_MAPPING, script_path=good,
            script_dir=os.path.join(self.tmp, "scripts"),
        )
        self.core.save_script("NEW")
        os.remove(good)
        self.assertIsNone(self.core.load_script_lines())


class TestScriptLibrary(CoreTestCase):
    def test_save_list_load_delete(self):
        self.core.save_named_script("payload-1", "STRING one\n")
        self.core.save_named_script("payload-2", "STRING two\n")
        self.assertEqual(self.core.list_scripts(), ["payload-1", "payload-2"])
        self.assertEqual(self.core.load_named_script("payload-1"), "STRING one\n")
        self.assertTrue(self.core.delete_named_script("payload-1"))
        self.assertEqual(self.core.list_scripts(), ["payload-2"])

    def test_missing_script_reads_as_none_and_deletes_as_false(self):
        self.assertIsNone(self.core.load_named_script("nope"))
        self.assertFalse(self.core.delete_named_script("nope"))

    def test_empty_library_lists_nothing(self):
        self.assertEqual(self.core.list_scripts(), [])

    def test_rejects_names_that_could_escape_the_directory(self):
        for bad in ["../boot.py", "..", ".hidden", "a/b", "a\\b", "", "x" * 49,
                    "with space", "semi;colon"]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.core.save_named_script(bad, "STRING x")

    def test_traversal_attempt_does_not_touch_the_target(self):
        victim = os.path.join(self.tmp, "boot.py")
        with open(victim, "w") as f:
            f.write("original")

        with self.assertRaises(ValueError):
            self.core.save_named_script("../boot.py", "overwritten")

        with open(victim) as f:
            self.assertEqual(f.read(), "original")

    def test_accepts_ordinary_names(self):
        for good in ["payload", "payload-1", "payload_1", "p.txt", "A1"]:
            with self.subTest(name=good):
                self.core.save_named_script(good, "STRING x")


class TestClassifyLine(CoreTestCase):
    def kind(self, line):
        return self.core.classify_line(line)[0]

    def warning(self, line):
        return self.core.classify_line(line)[2]

    def test_blank_and_comments(self):
        self.assertEqual(self.kind(""), "blank")
        self.assertEqual(self.kind("   "), "blank")
        self.assertEqual(self.kind("# note"), "comment")
        self.assertEqual(self.kind("REM note"), "comment")

    def test_string_and_delay(self):
        self.assertEqual(self.kind("STRING hello"), "string")
        self.assertEqual(self.kind("DELAY 500"), "delay")
        self.assertEqual(self.kind("CHAR_DELAY 20"), "char_delay")
        self.assertIsNone(self.warning("DELAY 500"))

    def test_flags_delay_without_a_number(self):
        self.assertIsNotNone(self.warning("DELAY soon"))
        self.assertIsNotNone(self.warning("DELAY"))
        self.assertIsNotNone(self.warning("STRING"))

    def test_plus_combination_is_understood(self):
        kind, detail, warning = self.core.classify_line("CTRL+ALT+DELETE")
        self.assertEqual(kind, "combo")
        self.assertIsNone(warning)
        self.assertIn("CTRL", detail)

    def test_flags_unknown_key_inside_a_combination(self):
        self.assertIn("NOPE", self.warning("CTRL+NOPE"))

    def test_flags_the_space_separated_trap(self):
        """The executor matches a bare key name before it checks for '+',
        so only the first key of a space-separated line is ever sent. The
        validator has to say so, and suggest the form that works."""
        warning = self.warning("CTRL ALT DELETE")
        self.assertIsNotNone(warning)
        self.assertIn("only CTRL is sent", warning)
        self.assertIn("CTRL+ALT+DELETE", warning)

    def test_flags_a_modifier_with_a_trailing_argument(self):
        self.assertIn("GUI+R", self.warning("GUI R"))

    def test_flags_an_unrecognised_command(self):
        kind, _detail, warning = self.core.classify_line("MOSUE_MOVE 10 10")
        self.assertEqual(kind, "unknown")
        self.assertIn("MOSUE_MOVE", warning)

    def test_extra_commands_are_accepted_when_declared(self):
        kind, _detail, warning = self.core.classify_line(
            "MOUSE_MOVE 10 10", extra_commands=("MOUSE_MOVE",)
        )
        self.assertEqual(kind, "extra")
        self.assertIsNone(warning)


class TestValidateAndExplain(CoreTestCase):
    SCRIPT = (
        "# open a terminal\n"
        "GUI R\n"
        "DELAY 500\n"
        "STRING hello\n"
        "CTRL+ALT+DELETE\n"
        "BOGUS_THING\n"
    )

    def test_validate_finds_only_the_real_problems(self):
        problems = self.core.validate_script(self.SCRIPT)
        self.assertEqual([number for number, _text, _message in problems], [2, 6])

    def test_validate_passes_a_clean_script(self):
        self.assertEqual(self.core.validate_script("STRING hi\nDELAY 10\nENTER\n"), [])

    def test_dry_run_skips_blanks_and_keeps_line_numbers(self):
        steps = self.core.explain_script(self.SCRIPT)
        self.assertEqual([step["line"] for step in steps], [1, 2, 3, 4, 5, 6])
        self.assertEqual(steps[3]["kind"], "string")
        self.assertIn("hello", steps[3]["detail"])

    def test_dry_run_sends_nothing(self):
        self.core.explain_script(self.SCRIPT)
        self.core.validate_script(self.SCRIPT)
        self.assertEqual(
            self.keyboard.events, [],
            "a dry run must not touch the keyboard",
        )


class TestKeyCombinations(CoreTestCase):
    def test_plus_separated_presses_and_releases_in_reverse(self):
        self.assertTrue(self.core.execute_key_combination("CTRL+ALT+DELETE"))
        self.assertEqual(
            self.keyboard.events,
            [("press", 1), ("press", 3), ("press", 6),
             ("release", 6), ("release", 3), ("release", 1)],
        )

    def test_unknown_keys_send_nothing(self):
        self.assertFalse(self.core.execute_key_combination("NOPE+ZZZ"))
        self.assertEqual(self.keyboard.events, [])

    def test_empty_input_sends_nothing(self):
        self.assertFalse(self.core.execute_key_combination(""))
        self.assertEqual(self.keyboard.events, [])


class TestStatusSnapshot(CoreTestCase):
    def test_reports_the_link_and_free_memory(self):
        snapshot = self.core.status_snapshot()
        self.assertTrue(snapshot["connected"])
        self.assertEqual(snapshot["ip"], "192.168.1.50")
        self.assertEqual(snapshot["free_memory"], 180000)
        self.assertIn("uptime_s", snapshot)

    def test_hides_the_address_when_offline(self):
        self.env.radio.connected = False
        self.assertEqual(self.core.status_snapshot()["ip"], "Not connected")


class TestBodyLimit(CoreTestCase):
    def test_decodes_a_body_within_the_limit(self):
        request = stubs.FakeRequest(b"STRING hello")
        self.assertEqual(self.core.read_body(request), "STRING hello")

    def test_an_empty_body_reads_as_empty(self):
        self.assertEqual(self.core.read_body(stubs.FakeRequest(b"")), "")
        self.assertEqual(self.core.read_body(stubs.FakeRequest(None)), "")

    def test_refuses_an_oversized_body(self):
        request = stubs.FakeRequest(b"x" * 100)
        with self.assertRaises(self.core.BodyTooLarge):
            self.core.read_body(request, limit=99)

    def test_the_refusal_names_both_sizes(self):
        request = stubs.FakeRequest(b"x" * 100)
        try:
            self.core.read_body(request, limit=10)
        except self.core.BodyTooLarge as e:
            self.assertIn("100", str(e))
            self.assertIn("10", str(e))

    def test_a_body_exactly_at_the_limit_is_accepted(self):
        request = stubs.FakeRequest(b"x" * 50)
        self.assertEqual(len(self.core.read_body(request, limit=50)), 50)


class TestPageResponse(CoreTestCase):
    def setUp(self):
        super().setUp()
        self.www = os.path.join(self.tmp, "www")
        os.mkdir(self.www)

    def write_plain(self, body="<html></html>"):
        with open(os.path.join(self.www, "index.html"), "w") as f:
            f.write(body)

    def write_gzip(self, body=b"\x1f\x8bcompressed"):
        with open(os.path.join(self.www, "index.html.gz"), "wb") as f:
            f.write(body)

    def test_streams_the_plain_file_when_there_is_no_gzip(self):
        self.write_plain()

        response = self.core.page_response(stubs.FakeRequest(), root=self.www)
        self.assertIsInstance(response, stubs.FakeFileResponse)
        self.assertEqual(response.filename, "index.html")

    def test_prefers_the_gzip_and_marks_the_encoding(self):
        self.write_gzip()

        response = self.core.page_response(stubs.FakeRequest(), root=self.www)
        # Streamed, like the plain file: neither path holds the whole page.
        self.assertIsInstance(response, stubs.FakeFileResponse)
        self.assertEqual(response.filename, "index.html.gz")
        self.assertEqual(response.headers["Content-Encoding"], "gzip")
        # Without this the library would map .gz to application/gzip and the
        # browser would download the page instead of rendering it.
        self.assertEqual(response.content_type, "text/html")

    def test_offers_an_etag_and_always_revalidates(self):
        self.write_gzip()

        response = self.core.page_response(stubs.FakeRequest(), root=self.www)
        self.assertIn("ETag", response.headers)
        self.assertEqual(response.headers["Cache-Control"], "no-cache")

    def test_an_unchanged_page_costs_a_304_not_the_document(self):
        self.write_gzip()
        first = self.core.page_response(stubs.FakeRequest(), root=self.www)
        etag = first.headers["ETag"]

        again = self.core.page_response(
            stubs.FakeRequest(headers={"if-none-match": etag}), root=self.www
        )
        self.assertEqual(again.status, 304)
        self.assertEqual(again.body, "")

    def test_an_edited_page_is_sent_again(self):
        self.write_gzip(b"\x1f\x8bshort")
        etag = self.core.page_response(stubs.FakeRequest(), root=self.www).headers["ETag"]

        self.write_gzip(b"\x1f\x8bconsiderably longer than before")
        response = self.core.page_response(
            stubs.FakeRequest(headers={"if-none-match": etag}), root=self.www
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["Content-Encoding"], "gzip")

    def test_a_missing_page_does_not_raise(self):
        # Nothing in /www at all: must still hand back a response object
        # rather than blowing up inside the route.
        response = self.core.page_response(stubs.FakeRequest(), root=self.www)
        self.assertIsInstance(response, stubs.FakeFileResponse)


class TestReconnectPolicy(CoreTestCase):
    def test_connected_link_needs_no_work(self):
        self.env.radio.connected = True
        self.assertTrue(self.core.check_wifi_connection())
        self.assertEqual(self.env.radio.attempts, 0)

    def test_reconnect_is_bounded_so_serving_is_not_blocked(self):
        self.env.radio.connected = False
        self.env.radio.connect_succeeds = False

        self.assertFalse(self.core.check_wifi_connection(max_attempts=3))
        self.assertEqual(self.env.radio.attempts, 3)

    def test_successful_reconnect_reports_online(self):
        self.env.radio.connected = False
        self.assertTrue(self.core.check_wifi_connection())


class FakeServer:
    """A server that holds a port, so a leaked socket is visible."""

    port_holder = None

    def __init__(self, name):
        self.name = name

    def start(self, port=80):
        if FakeServer.port_holder is not None:
            raise OSError(112, f"address in use, held by {FakeServer.port_holder}")
        FakeServer.port_holder = self.name

    def stop(self):
        if FakeServer.port_holder == self.name:
            FakeServer.port_holder = None

    def poll(self):
        pass


class TestRestartServer(CoreTestCase):
    def setUp(self):
        super().setUp()
        FakeServer.port_holder = None
        self.created = []

    def setup_server(self):
        server = FakeServer(f"srv{len(self.created) + 1}")
        self.created.append(server)
        try:
            server.start(port=80)
            return server
        except OSError:
            return None

    def test_rebinding_without_stopping_first_fails(self):
        """The behaviour being fixed: the old code called setup_server()
        again while the previous socket still held port 80, so the restart
        returned None and the caller rebooted the board."""
        self.setup_server()
        self.assertIsNone(self.setup_server())

    def test_restart_frees_the_port_and_succeeds(self):
        old = self.setup_server()
        new = self.core.restart_server(old, self.setup_server)
        self.assertIsNotNone(new)
        self.assertEqual(FakeServer.port_holder, new.name)

    def test_restart_survives_a_stop_that_raises(self):
        class LegacyServer(FakeServer):
            def stop(self):
                raise RuntimeError("stop() not available in this version")

        FakeServer.port_holder = None
        self.assertIsNotNone(self.core.restart_server(LegacyServer("old"), self.setup_server))


class TestServeForever(CoreTestCase):
    """The scheduled check must rebuild the socket after a reconnect, and
    only then. The original condition was inverted."""

    def run_loop(self, offline_at_check, reconnect_succeeds):
        clock = stubs.instant_clock(self.core)
        restarts = []

        class Server:
            def __init__(self, polls_before_exit=3):
                self.polls = 0
                self.limit = polls_before_exit

            def poll(self):
                self.polls += 1
                clock["t"] += 40  # two polls clear the 60 s check interval
                if self.polls > self.limit:
                    raise SystemExit

            def stop(self):
                pass

        def setup_server():
            restarts.append(True)
            return Server()

        self.env.radio.connected = not offline_at_check
        self.env.radio.connect_succeeds = reconnect_succeeds

        try:
            self.core.serve_forever(Server(), setup_server)
        except SystemExit:
            pass

        return len(restarts)

    def test_no_restart_while_the_link_is_up(self):
        self.assertEqual(self.run_loop(offline_at_check=False, reconnect_succeeds=True), 0)

    def test_restarts_after_a_successful_reconnect(self):
        self.assertGreaterEqual(
            self.run_loop(offline_at_check=True, reconnect_succeeds=True), 1
        )

    def test_no_restart_when_the_reconnect_failed(self):
        self.assertEqual(
            self.run_loop(offline_at_check=True, reconnect_succeeds=False), 0,
            "restarting the server with no network was the inverted condition",
        )


class TestAdaptivePolling(CoreTestCase):
    """The loop should back off when nothing is happening and tighten up
    the moment it is, instead of waking hundreds of times a second to be
    told there was no request."""

    def run_loop(self, poll_result, iterations=12):
        pauses = []

        class Clock:
            t = 0.0

            @classmethod
            def sleep(cls, seconds):
                pauses.append(seconds)
                cls.t += seconds

            @classmethod
            def monotonic(cls):
                return cls.t

        self.core.time = Clock

        class Server:
            def __init__(self):
                self.polls = 0

            def poll(self):
                self.polls += 1
                if self.polls > iterations:
                    raise SystemExit
                return poll_result

            def stop(self):
                pass

        try:
            self.core.serve_forever(Server(), lambda: Server())
        except SystemExit:
            pass

        return pauses

    def test_backs_off_while_idle(self):
        pauses = self.run_loop("no_request")
        self.assertLess(pauses[0], pauses[-1], "an idle loop should slow down")
        self.assertEqual(pauses[-1], 0.1, "and settle at the idle ceiling")

    def test_never_exceeds_the_idle_ceiling(self):
        self.assertTrue(all(p <= 0.1 for p in self.run_loop("no_request", 40)))

    def test_stays_tight_while_requests_arrive(self):
        pauses = self.run_loop("request_handled_response_sent")
        self.assertTrue(all(p == 0.002 for p in pauses),
                        "a busy loop must not back off")

    def test_a_request_resets_the_backoff(self):
        """Idle for a while, then a request: the next pause is tight again."""
        results = ["no_request"] * 8 + ["request_handled_response_sent"] * 3
        step = iter(results)
        pauses = []

        class Clock:
            t = 0.0

            @classmethod
            def sleep(cls, seconds):
                pauses.append(seconds)
                cls.t += seconds

            @classmethod
            def monotonic(cls):
                return cls.t

        self.core.time = Clock

        class Server:
            def poll(self):
                try:
                    return next(step)
                except StopIteration:
                    raise SystemExit

            def stop(self):
                pass

        try:
            self.core.serve_forever(Server(), lambda: Server())
        except SystemExit:
            pass

        self.assertGreater(pauses[7], 0.002, "should have backed off while idle")
        self.assertEqual(pauses[8], 0.002, "and snapped back on the first request")

    def test_an_uninformative_poll_keeps_the_fixed_pause(self):
        """Older libraries whose poll() returns nothing must not be guessed
        at; the loop keeps a steady pause instead."""
        pauses = self.run_loop(None)
        self.assertTrue(all(p == 0.002 for p in pauses))


class TestKeyHold(CoreTestCase):
    """A keypress the host never polls is a keypress that did not happen.

    USB HID is polled once per 1 ms frame and the device gets no
    acknowledgement, so a press followed immediately by a release can land
    entirely between two polls: the host reads the endpoint once, sees
    nothing held, and the character is lost. This is the "characters skip
    at low delays" behaviour, and it is why a faster implementation loses
    more of them rather than fewer.
    """

    POLL_INTERVAL = 0.001

    def build(self, hold):
        """A fake keyboard on a fake clock, with a host polling at 1 ms."""
        clock = {"t": 0.0}
        reports = []          # (time, keys held) each time the report changes
        polls = []            # what a host polling every 1 ms would observe

        class Clock:
            @staticmethod
            def sleep(seconds):
                clock["t"] += seconds

            @staticmethod
            def monotonic():
                return clock["t"]

        self.core.time = Clock

        class BaseKeyboard:
            def __init__(self, devices):
                self.held = set()

            def press(self, key):
                self.held.add(key)
                reports.append((clock["t"], frozenset(self.held)))

            def release_all(self):
                self.held.clear()
                reports.append((clock["t"], frozenset()))

        keyboard = self.core.paced_keyboard(BaseKeyboard, ("dev",), hold=hold)

        def host_polls():
            """What the host reads: the last report before each 1 ms tick."""
            polls.clear()
            end = reports[-1][0] if reports else 0.0
            tick = 0.0
            while tick <= end + self.POLL_INTERVAL:
                visible = frozenset()
                for at, keys in reports:
                    if at <= tick:
                        visible = keys
                polls.append(visible)
                tick += self.POLL_INTERVAL
            return polls

        return keyboard, host_polls

    def type_one_key(self, keyboard):
        """What adafruit_hid's _write does: press, then release at once."""
        keyboard.press("A")
        keyboard.release_all()

    def test_without_a_hold_the_host_can_miss_the_key(self):
        keyboard, host_polls = self.build(hold=0)
        self.type_one_key(keyboard)

        self.assertTrue(
            all("A" not in seen for seen in host_polls()),
            "press and release in the same frame should be invisible; "
            "if this starts passing the simulation is wrong, not the fix",
        )

    def test_holding_the_key_makes_it_visible(self):
        keyboard, host_polls = self.build(hold=self.core.KEY_HOLD_SECONDS)
        self.type_one_key(keyboard)

        self.assertTrue(any("A" in seen for seen in host_polls()),
                        "the host should poll at least once while held")

    def test_the_hold_spans_several_poll_frames(self):
        keyboard, host_polls = self.build(hold=self.core.KEY_HOLD_SECONDS)
        self.type_one_key(keyboard)

        frames = sum(1 for seen in host_polls() if "A" in seen)
        self.assertGreaterEqual(
            frames, 2,
            "one frame of margin is not enough when the host polls late",
        )

    def test_the_key_is_still_released_afterwards(self):
        keyboard, host_polls = self.build(hold=self.core.KEY_HOLD_SECONDS)
        self.type_one_key(keyboard)

        self.assertEqual(host_polls()[-1], frozenset(),
                         "a key left held would repeat on the target")

    def test_hold_zero_restores_the_original_behaviour(self):
        keyboard, _polls = self.build(hold=0)
        before = self.core.time.monotonic()
        self.type_one_key(keyboard)
        self.assertEqual(self.core.time.monotonic(), before)


class TestTypeText(CoreTestCase):
    """The hold has to come out of the character delay, not on top of it,
    or making typing reliable would also make it slower."""

    def build(self, char_delay, hold=None):
        if hold is None:
            hold = self.core.KEY_HOLD_SECONDS

        clock = {"t": 0.0}
        events = []

        class Clock:
            @staticmethod
            def sleep(seconds):
                clock["t"] += seconds

            @staticmethod
            def monotonic():
                return clock["t"]

        self.core.time = Clock

        class Layout:
            def write(self, char):
                events.append(("press", char, clock["t"]))
                clock["t"] += hold          # what release_all now waits
                events.append(("release", char, clock["t"]))

        self.core.configure(
            ssid="n", password="p", keyboard=self.keyboard,
            keyboard_layout=Layout(), key_mapping=stubs.KEY_MAPPING,
            script_path=os.path.join(self.tmp, "active.txt"),
            script_dir=os.path.join(self.tmp, "scripts"),
        )
        return clock, events, hold

    def test_character_rate_is_unchanged_by_the_hold(self):
        char_delay = 0.010
        clock, _events, _hold = self.build(char_delay)

        self.core.type_text("hello", char_delay)

        self.assertAlmostEqual(clock["t"], 5 * char_delay, places=6,
                               msg="five characters should still take five "
                                   "character delays, not five plus five holds")

    def test_each_key_is_actually_held(self):
        char_delay = 0.010
        _clock, events, hold = self.build(char_delay)

        self.core.type_text("ab", char_delay)

        for i in range(0, len(events), 2):
            press, release = events[i], events[i + 1]
            self.assertAlmostEqual(release[2] - press[2], hold, places=6)

    def test_the_hold_becomes_the_floor_for_very_short_delays(self):
        """Asking for 1 ms characters gets 4 ms rather than nothing typed."""
        _clock2, _e, hold = self.build(0.001)
        clock, _events, _h = self.build(0.001)

        self.core.type_text("abc", 0.001)

        self.assertAlmostEqual(clock["t"], 3 * hold, places=6)

    def test_a_generous_delay_is_respected(self):
        clock, _events, _hold = self.build(0.050)
        self.core.type_text("abcd", 0.050)
        self.assertAlmostEqual(clock["t"], 4 * 0.050, places=6)

    def test_empty_text_does_nothing(self):
        clock, events, _hold = self.build(0.010)
        self.core.type_text("", 0.010)
        self.assertEqual(events, [])
        self.assertEqual(clock["t"], 0.0)


class TestHostVerification(CoreTestCase):
    """USB HID acknowledges nothing, with one exception: the host sends the
    device its keyboard LED state. Pressing a lock key and watching that
    come back changed is the only end-to-end proof available that
    keystrokes are arriving."""

    def configure_with(self, keyboard):
        stubs.instant_clock(self.core)
        self.core.configure(
            ssid="n", password="p", keyboard=keyboard, keyboard_layout=None,
            key_mapping=stubs.KEY_MAPPING,
            script_path=os.path.join(self.tmp, "active.txt"),
            script_dir=os.path.join(self.tmp, "scripts"),
        )
        return keyboard

    def test_a_listening_host_is_confirmed(self):
        self.configure_with(stubs.FakeHostKeyboard(answers=True))
        ok, detail = self.core.verify_host_link()
        self.assertTrue(ok, detail)

    def test_it_reports_how_long_the_host_took(self):
        self.configure_with(stubs.FakeHostKeyboard(answers=True))
        _ok, detail = self.core.verify_host_link()
        self.assertIn("round_trip_s", detail)
        self.assertGreaterEqual(detail["round_trip_s"], 0)

    def test_the_suggested_delay_never_drops_below_the_key_hold(self):
        """Nothing under the hold is achievable, so suggesting it would be
        advice that cannot be followed."""
        self.configure_with(stubs.FakeHostKeyboard(answers=True))
        _ok, detail = self.core.verify_host_link()
        floor_ms = int(round(self.core.KEY_HOLD_SECONDS * 1000))
        self.assertGreaterEqual(detail["suggested_char_delay_ms"], floor_ms)

    def test_a_slow_host_is_told_to_type_slower(self):
        self.assertGreater(
            self.core._suggested_char_delay(0.040),
            self.core._suggested_char_delay(0.002),
        )

    def test_the_target_is_left_as_it_was_found(self):
        keyboard = self.configure_with(stubs.FakeHostKeyboard(answers=True))
        before = keyboard.led_status
        self.core.verify_host_link()
        self.assertEqual(keyboard.led_status, before,
                         "Num Lock must be pressed back, not left toggled")

    def test_a_silent_host_is_reported_as_a_failure(self):
        self.configure_with(stubs.FakeHostKeyboard(answers=False))
        ok, detail = self.core.verify_host_link(timeout=0.05)
        self.assertFalse(ok)
        self.assertIn("no response", detail["message"])

    def test_a_keyboard_without_led_state_is_unknown_not_broken(self):
        """A build that cannot report LED state must not be called a
        failure; not knowing and knowing it failed are different."""
        self.configure_with(stubs.FakeKeyboard())
        ok, detail = self.core.verify_host_link()
        self.assertIsNone(ok)
        self.assertIn("LED state", detail["message"])

    def test_the_check_uses_the_ordinary_key_path(self):
        keyboard = self.configure_with(stubs.FakeHostKeyboard(answers=True))
        self.core.verify_host_link()
        self.assertIn(("press", 0x53), [(a, k) for a, k in keyboard.events
                                        if a == "press"])


if __name__ == "__main__":
    unittest.main()
