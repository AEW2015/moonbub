"""@brief Tests for pure Game Bub to Xbox state dispatch and fake ViGEm calls."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gamepad_backend import (
    GAMEBUB_MASK,
    GamepadDispatcher,
    VigemXbox360Backend,
    gamebub_mask_to_xbox_buttons,
)


class FakeBackend:
    """@brief Record complete fake gamepad states without injecting input."""

    def __init__(self, fail_on=None):
        self.states = []
        self.closed = False
        self.fail_on = fail_on

    def set_buttons(self, buttons):
        buttons = frozenset(buttons)
        if buttons == self.fail_on:
            raise OSError("injected fake backend error")
        self.states.append(buttons)

    def close(self):
        self.closed = True


class GamepadMappingTests(unittest.TestCase):
    """@brief Verify every Game Bub control maps to its expected Xbox control."""

    def test_each_gamebub_bit_maps_to_expected_xbox_control(self):
        expected = {
            11: "a",
            10: "b",
            9: "x",
            8: "y",
            7: "up",
            6: "down",
            5: "left",
            4: "right",
            3: "left_shoulder",
            2: "right_shoulder",
            1: "start",
            0: "back",
        }
        for bit, button in expected.items():
            with self.subTest(bit=bit):
                self.assertEqual(gamebub_mask_to_xbox_buttons(1 << bit), {button})
        self.assertEqual(gamebub_mask_to_xbox_buttons(GAMEBUB_MASK), set(expected.values()))
        self.assertEqual(gamebub_mask_to_xbox_buttons(0), frozenset())

    def test_invalid_masks_are_rejected_before_backend_mutation(self):
        backend = FakeBackend()
        dispatcher = GamepadDispatcher(backend)
        for mask in (-1, GAMEBUB_MASK + 1, True, 1.0):
            with self.subTest(mask=mask), self.assertRaises(ValueError):
                dispatcher.apply(mask)
        self.assertEqual(backend.states, [])


class GamepadDispatcherTests(unittest.TestCase):
    """@brief Verify complete snapshots, neutralization, and lifecycle failures."""

    def test_chords_changes_neutral_and_close_are_complete_states(self):
        backend = FakeBackend()
        dispatcher = GamepadDispatcher(backend)
        self.assertTrue(dispatcher.apply((1 << 11) | (1 << 7)))
        self.assertFalse(dispatcher.apply((1 << 11) | (1 << 7)))
        self.assertTrue(dispatcher.apply(1 << 7))
        self.assertTrue(dispatcher.neutral())
        self.assertFalse(dispatcher.neutral())
        dispatcher.apply((1 << 10) | (1 << 1))
        dispatcher.close()
        dispatcher.close()
        self.assertEqual(
            backend.states,
            [frozenset({"a", "up"}), frozenset({"up"}), frozenset(), frozenset({"b", "start"}), frozenset()],
        )
        self.assertTrue(backend.closed)
        with self.assertRaises(RuntimeError):
            dispatcher.apply(0)
        with self.assertRaises(RuntimeError):
            dispatcher.neutral()

    def test_close_neutralizes_a_held_state(self):
        backend = FakeBackend()
        dispatcher = GamepadDispatcher(backend)
        dispatcher.apply(1 << 11)
        dispatcher.close()
        self.assertEqual(backend.states[-1], frozenset())
        self.assertTrue(backend.closed)

    def test_backend_failure_attempts_release_and_closes(self):
        backend = FakeBackend(fail_on=frozenset({"a"}))
        dispatcher = GamepadDispatcher(backend)
        with self.assertRaisesRegex(RuntimeError, "neutralization was attempted"):
            dispatcher.apply(1 << 11)
        self.assertEqual(backend.states, [frozenset()])
        self.assertTrue(backend.closed)
        with self.assertRaises(RuntimeError):
            dispatcher.apply(0)

    def test_bad_backend_is_rejected(self):
        with self.assertRaises(TypeError):
            GamepadDispatcher(object())


class FakeVigemTests(unittest.TestCase):
    """@brief Verify calls to the ViGEm adapter without a physical device."""

    def test_lazy_factory_reports_missing_optional_package(self):
        with patch("gamepad_backend.import_module", side_effect=ImportError("missing")), self.assertRaisesRegex(
            RuntimeError, "no driver was installed"
        ):
            VigemXbox360Backend.create()

    def test_vigem_adapter_sends_deltas_then_neutralizes_and_unplugs(self):
        class Pad:
            def __init__(self):
                self.calls = []

            def press_button(self, *, button):
                self.calls.append(("press", button))

            def release_button(self, *, button):
                self.calls.append(("release", button))

            def update(self):
                self.calls.append(("update",))

            def reset(self):
                self.calls.append(("reset",))

            def unplug(self):
                self.calls.append(("unplug",))

        enum = SimpleNamespace(XUSB_GAMEPAD_A=1, XUSB_GAMEPAD_B=2)
        pad = Pad()
        backend = VigemXbox360Backend(pad)
        backend._enum = enum
        backend._CONSTANTS = {"a": "XUSB_GAMEPAD_A", "b": "XUSB_GAMEPAD_B"}
        backend.set_buttons(frozenset({"a"}))
        backend.set_buttons(frozenset({"a", "b"}))
        backend.set_buttons(frozenset({"b"}))
        backend.close()
        self.assertEqual(
            pad.calls,
            [
                ("press", 1),
                ("update",),
                ("press", 2),
                ("update",),
                ("release", 1),
                ("update",),
                ("reset",),
                ("update",),
                ("unplug",),
            ],
        )
        with self.assertRaises(RuntimeError):
            backend.set_buttons(frozenset())

    def test_cleanup_attempts_unplug_even_when_neutral_report_fails(self):
        class BrokenPad:
            def __init__(self):
                self.unplugged = False

            def reset(self):
                raise OSError("reset failed")

            def update(self):
                raise AssertionError("update must not follow failed reset")

            def unplug(self):
                self.unplugged = True

        pad = BrokenPad()
        backend = VigemXbox360Backend(pad)
        with self.assertRaisesRegex(RuntimeError, "neutral report failed"):
            backend.close()
        self.assertTrue(pad.unplugged)
        self.assertIsNone(backend._gamepad)


if __name__ == "__main__":
    unittest.main()
