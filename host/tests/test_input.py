import argparse
from contextlib import redirect_stdout
from io import StringIO
import queue
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moonshine.input import InputSession, KeyboardInjector, KEY_MAP
from moonshine.protocol import FEEDBACK
from moonshine.sender import run


class KeyboardTests(unittest.TestCase):
    def test_button_mapping_combined_and_duplicate_masks(self):
        calls = []
        keyboard = KeyboardInjector(lambda key, down: calls.append((key, down)))
        keyboard.update((1 << 11) | (1 << 7) | (1 << 4))
        self.assertEqual(set(calls), {(0x5a, True), (0x26, True), (0x27, True)})
        before = list(calls)
        keyboard.update((1 << 11) | (1 << 7) | (1 << 4))
        self.assertEqual(calls, before)
        keyboard.release_all()
        self.assertEqual(set(calls[3:]), {(0x5a, False), (0x26, False), (0x27, False)})
        self.assertFalse(keyboard.pressed)

    def test_direction_switch_releases_before_pressing(self):
        calls = []
        keyboard = KeyboardInjector(lambda key, down: calls.append((key, down)))
        keyboard.update(1 << 5)
        keyboard.update(1 << 4)
        self.assertEqual(calls, [(0x25, True), (0x25, False), (0x27, True)])
        keyboard.release_all()

    def test_timeout_disconnect_and_shutdown_release(self):
        for reason in ("disconnect", "socket error", "sender shutdown"):
            calls, logs = [], []
            keyboard = KeyboardInjector(lambda key, down: calls.append((key, down)))
            session = InputSession(keyboard, lambda mask, why: logs.append((mask, why)))
            session.feedback((1 << 11) | (1 << 1), now=1)
            session.disconnect(reason)
            self.assertEqual(logs[-1], (0, reason))
            self.assertFalse(keyboard.pressed)
            self.assertEqual(set(calls[-2:]), {(0x5a, False), (0x0d, False)})
        calls = []
        keyboard = KeyboardInjector(lambda key, down: calls.append((key, down)))
        session = InputSession(keyboard)
        session.feedback(1 << 11, now=2)
        session.tick(2.5)
        self.assertTrue(keyboard.pressed)
        session.tick(2.501)
        self.assertFalse(keyboard.pressed)
        self.assertEqual(calls, [(0x5a, True), (0x5a, False)])

    def test_failed_key_down_still_attempts_release(self):
        calls = []
        def backend(key, down):
            calls.append((key, down))
            if down:
                raise OSError("mock platform accepted down then reported error")
        keyboard = KeyboardInjector(backend)
        session = InputSession(keyboard)
        with self.assertRaises(OSError):
            session.feedback(1 << 11, now=0)
        self.assertEqual(calls, [(0x5a, True), (0x5a, False)])
        self.assertFalse(keyboard.pressed)

    def test_failed_release_does_not_skip_other_held_keys(self):
        calls = []
        def backend(key, down):
            calls.append((key, down))
            if key == 0x0d and not down:
                raise OSError("mock key up failure")
        keyboard = KeyboardInjector(backend)
        keyboard.update((1 << 1) | (1 << 11))
        with self.assertRaises(OSError):
            keyboard.release_all()
        self.assertIn((0x5a, False), calls)
        self.assertEqual(keyboard.pressed, {0x0d})

    def test_default_session_logs_without_constructing_windows_backend(self):
        logs = []
        session = InputSession(logger=lambda mask, reason: logs.append((mask, reason)))
        session.feedback(1 << 11, now=0)
        session.disconnect()
        self.assertEqual(logs, [(1 << 11, "feedback"), (0, "disconnect")])


class SenderCleanupTests(unittest.TestCase):
    def fake_capture(self):
        class FakeCapture:
            def __init__(self):
                self.queue = queue.Queue()
                self.ended = True
                self.error = None
                self.replaced = 0
            def start(self, args):
                pass
            def close(self):
                pass
        return FakeCapture

    def args(self, inject_keys):
        return argparse.Namespace(host="127.0.0.1", port=5533, fps=30, quality=65, mbps=12,
                                  duration=0.1, input_jsonl=None, metrics=None, inject_keys=inject_keys)

    def test_opt_in_sender_socket_error_releases_without_real_injection(self):
        calls = []
        events = [FEEDBACK.pack(b"MSF1", 1, 0, 1 << 11, 1, 1024, 1, 0, 0),
                  ConnectionResetError("mock socket closed")]
        class FakeSocket:
            def connect(self, address): pass
            def setblocking(self, enabled): pass
            def recv(self, count):
                value = events.pop(0)
                if isinstance(value, Exception): raise value
                return value
            def close(self): pass
        with patch("moonshine.sender.WindowsKeyboard", return_value=lambda key, down: calls.append((key, down))) as backend, \
             patch("moonshine.sender.socket.socket", return_value=FakeSocket()), \
             patch("moonshine.sender.LatestFrames", self.fake_capture()), redirect_stdout(StringIO()):
            with self.assertRaises(ConnectionResetError):
                run(self.args(True))
        backend.assert_called_once()
        self.assertEqual(calls, [(0x5a, True), (0x5a, False)])

    def test_default_sender_never_constructs_windows_backend(self):
        class FakeSocket:
            def connect(self, address): pass
            def setblocking(self, enabled): pass
            def recv(self, count): raise BlockingIOError()
            def close(self): pass
        with patch("moonshine.sender.WindowsKeyboard") as backend, \
             patch("moonshine.sender.socket.socket", return_value=FakeSocket()), \
             patch("moonshine.sender.LatestFrames", self.fake_capture()), redirect_stdout(StringIO()):
            result = run(self.args(False))
        backend.assert_not_called()
        self.assertFalse(result["keyboard_injection"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
