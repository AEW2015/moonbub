"""@brief Optional Xbox 360 virtual gamepad output for Game Bub button masks.

Importing this module does not load a virtual-gamepad package or touch a device.
The caller owns protocol authentication, session binding, ordering, and timeouts;
only a current normalized 12-bit Game Bub mask should be passed to the dispatcher.
"""

from importlib import import_module
from typing import ClassVar

GAMEBUB_XBOX_BUTTONS = {
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
GAMEBUB_MASK = (1 << 12) - 1


def gamebub_mask_to_xbox_buttons(mask):
    """@brief Map a complete 12-bit Game Bub snapshot to Xbox 360 button names.

    @param mask Unsigned normalized Game Bub button bitmask.
    @return Frozen set of pressed Xbox 360 control names.
    @throws ValueError If the mask is not an integer containing only 12 bits.
    """
    if type(mask) is not int or mask < 0 or mask & ~GAMEBUB_MASK:
        raise ValueError("Gamepad mask must contain only the twelve Game Bub buttons")
    return frozenset(name for bit, name in GAMEBUB_XBOX_BUTTONS.items() if mask & (1 << bit))


class GamepadDispatcher:
    """@brief Apply complete Game Bub snapshots to a small gamepad backend.

    The backend must expose ``set_buttons(frozenset[str])`` and ``close()``.
    Protocol identity and per-session stale-packet rejection belong to the
    transport adapter that calls this class.
    """

    def __init__(self, backend):
        """@brief Bind one backend to this dispatcher instance."""
        if not callable(getattr(backend, "set_buttons", None)) or not callable(
            getattr(backend, "close", None)
        ):
            raise TypeError("Gamepad backend must provide set_buttons() and close()")
        self._backend = backend
        self._buttons = frozenset()
        self._closed = False
        self._failed = False

    @property
    def buttons(self):
        """@brief Return the last successfully submitted complete button state."""
        return self._buttons

    def apply(self, mask):
        """@brief Apply a complete normalized Game Bub button snapshot.

        @param mask Unsigned 12-bit Game Bub button mask.
        @return True if the backend state changed; False if it was unchanged.
        @throws ValueError If the mask contains invalid bits.
        @throws RuntimeError If the dispatcher is closed or the backend failed.
        """
        self._ensure_active()
        buttons = gamebub_mask_to_xbox_buttons(mask)
        if buttons == self._buttons:
            return False
        self._submit(buttons)
        return True

    def neutral(self):
        """@brief Release every button while keeping the backend available.

        @return True if a held state was released; False if already neutral.
        @throws RuntimeError If the dispatcher is closed or the backend failed.
        """
        self._ensure_active()
        if not self._buttons:
            return False
        self._submit(frozenset())
        return True

    def close(self):
        """@brief Best-effort neutralization followed by backend cleanup.

        Repeated calls are safe. If neutralization fails, backend cleanup is
        still attempted and the failure is reported to the caller.
        """
        if self._closed:
            return
        failure = None
        if not self._failed and self._buttons:
            try:
                self._submit(frozenset())
            except RuntimeError as error:
                failure = error
        try:
            self._backend.close()
        except Exception as error:  # noqa: BLE001 - cleanup must mark this dispatcher closed
            failure = failure or RuntimeError(f"Gamepad backend cleanup failed: {error}")
        finally:
            self._buttons = frozenset()
            self._closed = True
        if failure:
            raise failure

    def _ensure_active(self):
        if self._closed:
            raise RuntimeError("Gamepad dispatcher is closed")
        if self._failed:
            raise RuntimeError("Gamepad backend has failed")

    def _submit(self, buttons):
        try:
            self._backend.set_buttons(buttons)
        except Exception as error:
            self._failed = True
            # A failed state update may have partially reached the driver. Try
            # an explicit neutral report before detaching the virtual device.
            cleanup_errors = []
            try:
                self._backend.set_buttons(frozenset())
            except Exception as cleanup_error:  # noqa: BLE001 - preserve original failure
                cleanup_errors.append(f"neutralization failed: {cleanup_error}")
            try:
                self._backend.close()
            except Exception as cleanup_error:  # noqa: BLE001 - preserve original failure
                cleanup_errors.append(f"cleanup failed: {cleanup_error}")
            self._buttons = frozenset()
            self._closed = True
            detail = "; " + "; ".join(cleanup_errors) if cleanup_errors else ""
            raise RuntimeError(
                f"Gamepad backend failed; neutralization was attempted: {error}{detail}"
            ) from error
        self._buttons = buttons


class VigemXbox360Backend:
    """@brief Lazy vgamepad adapter backed by a ViGEm Xbox 360 virtual pad."""

    _CONSTANTS: ClassVar[dict[str, str]] = {
        "a": "XUSB_GAMEPAD_A",
        "b": "XUSB_GAMEPAD_B",
        "x": "XUSB_GAMEPAD_X",
        "y": "XUSB_GAMEPAD_Y",
        "up": "XUSB_GAMEPAD_DPAD_UP",
        "down": "XUSB_GAMEPAD_DPAD_DOWN",
        "left": "XUSB_GAMEPAD_DPAD_LEFT",
        "right": "XUSB_GAMEPAD_DPAD_RIGHT",
        "left_shoulder": "XUSB_GAMEPAD_LEFT_SHOULDER",
        "right_shoulder": "XUSB_GAMEPAD_RIGHT_SHOULDER",
        "start": "XUSB_GAMEPAD_START",
        "back": "XUSB_GAMEPAD_BACK",
    }

    def __init__(self, gamepad):
        """@brief Wrap an already-created vgamepad-compatible Xbox device."""
        self._gamepad = gamepad
        self._buttons = frozenset()
        self._enum = None

    @classmethod
    def create(cls):
        """@brief Create a ViGEm Xbox 360 pad only when explicitly requested.

        @return A backend connected to the local ViGEmBus runtime.
        @throws RuntimeError If vgamepad or its ViGEm runtime is unavailable.
        """
        try:
            module = import_module("vgamepad")
        except ImportError as error:
            raise RuntimeError(
                "Xbox input requires the optional vgamepad package and ViGEmBus; "
                "no driver was installed"
            ) from error
        try:
            gamepad = module.VX360Gamepad()
        except Exception as error:
            raise RuntimeError(
                f"Could not create the ViGEm Xbox 360 pad: {error}; no driver was installed"
            ) from error
        backend = cls(gamepad)
        backend._enum = module.XUSB_BUTTON
        return backend

    def set_buttons(self, buttons):
        """@brief Submit a full button state using only changed button edges."""
        if self._gamepad is None:
            raise RuntimeError("ViGEm gamepad is closed")
        buttons = frozenset(buttons)
        unknown = buttons - self._CONSTANTS.keys()
        if unknown:
            raise ValueError(f"Unknown Xbox buttons: {sorted(unknown)}")
        try:
            for name in self._buttons - buttons:
                self._gamepad.release_button(button=self._constant(name))
            for name in buttons - self._buttons:
                self._gamepad.press_button(button=self._constant(name))
            self._gamepad.update()
        except Exception as error:
            try:
                self._best_effort_neutral()
            except Exception as neutral_error:  # noqa: BLE001 - retain both driver failures
                raise RuntimeError(
                    f"ViGEm update failed: {error}; neutral report failed: {neutral_error}"
                ) from error
            raise
        self._buttons = buttons

    def close(self):
        """@brief Release all controls and detach the virtual controller."""
        if self._gamepad is None:
            return
        gamepad = self._gamepad
        errors = []
        try:
            try:
                self._best_effort_neutral()
            except Exception as error:  # noqa: BLE001 - still attempt device detach
                errors.append(f"neutral report failed: {error}")
            unplug = getattr(gamepad, "unplug", None)
            if callable(unplug):
                try:
                    unplug()
                except Exception as error:  # noqa: BLE001 - retain cleanup failure
                    errors.append(f"device detach failed: {error}")
        finally:
            self._buttons = frozenset()
            self._gamepad = None
        if errors:
            raise RuntimeError("ViGEm cleanup failed: " + "; ".join(errors))

    def _constant(self, name):
        if self._enum is None:
            raise RuntimeError("ViGEm enum is unavailable")
        return getattr(self._enum, self._CONSTANTS[name])

    def _best_effort_neutral(self):
        gamepad = self._gamepad
        if gamepad is None:
            return
        try:
            gamepad.reset()
            gamepad.update()
        finally:
            self._buttons = frozenset()
