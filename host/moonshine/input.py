"""Opt-in Windows keyboard mapping for MSF1 buttons. No import-time injection."""
import ctypes
import os


# GameBub physical buttons, not the unrelated Godot runtime API button masks.
# A=Z, B=X, X=A, Y=S, L=Q, R=E, Start=Enter, Select=Space.
KEY_MAP = {
    11: 0x5A, 10: 0x58, 9: 0x41, 8: 0x53,
    7: 0x26, 6: 0x28, 5: 0x25, 4: 0x27,
    3: 0x51, 2: 0x45, 1: 0x0D, 0: 0x20,
}
EXTENDED_KEYS = {0x25, 0x26, 0x27, 0x28}


class WindowsKeyboard:
    """Send one explicit key transition using Win32 SendInput.

    Constructed only when the user supplies --inject-keys. Tests substitute a
    mock callable and never instantiate or invoke this real desktop backend.
    """
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("--inject-keys requires Windows")
        from ctypes import wintypes

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.c_size_t)]

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

        class PAYLOAD(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("payload", PAYLOAD)]

        self.INPUT = INPUT
        self.KEYBDINPUT = KEYBDINPUT
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.user32.SendInput.restype = wintypes.UINT

    def __call__(self, virtual_key, pressed):
        flags = (0 if pressed else 0x0002) | (0x0001 if virtual_key in EXTENDED_KEYS else 0)
        value = self.INPUT()
        value.type = 1  # INPUT_KEYBOARD
        value.payload.ki = self.KEYBDINPUT(virtual_key, 0, flags, 0, 0)
        if self.user32.SendInput(1, ctypes.byref(value), ctypes.sizeof(value)) != 1:
            error = ctypes.get_last_error()
            raise OSError(error, "Windows SendInput did not accept the key event (desktop/integrity restrictions may apply)")


class KeyboardInjector:
    """Stateful key transitions with explicit cleanup, using an injectable backend."""
    def __init__(self, backend, mapping=None):
        self.backend = backend
        self.mapping = dict(KEY_MAP if mapping is None else mapping)
        self.pressed = set()

    def update(self, buttons):
        wanted = {key for bit, key in self.mapping.items() if buttons & (1 << bit)}
        # Release before pressing: switching directions never holds both merely
        # because of iteration order. Duplicate masks cause no repeated presses.
        for key in sorted(self.pressed - wanted):
            self.backend(key, False)
            self.pressed.remove(key)
        for key in sorted(wanted - self.pressed):
            # Track attempted downs before the call, allowing a finally cleanup
            # even if the platform accepted an event before reporting an error.
            self.pressed.add(key)
            self.backend(key, True)

    def release_all(self):
        """Attempt every held release even if one platform event fails."""
        errors = []
        for key in sorted(self.pressed):
            try:
                self.backend(key, False)
            except OSError as exc:
                errors.append(exc)
            else:
                self.pressed.remove(key)
        if errors:
            raise OSError(f"could not release {len(errors)} injected key(s): {errors[0]}")


class InputSession:
    """Feedback/timeout/disconnect policy shared by logging and opt-in injection."""
    def __init__(self, injector=None, logger=None, timeout_seconds=0.5):
        self.injector = injector
        self.logger = logger
        self.timeout_seconds = timeout_seconds
        self.buttons = 0
        self.last_feedback = None

    def _apply(self, mask, reason):
        mask &= 0x0fff
        if mask == self.buttons:
            return
        try:
            if self.injector:
                self.injector.update(mask)
            if self.logger:
                self.logger(mask, reason)
            self.buttons = mask
        except BaseException:
            # A down can have reached the platform before the backend reports
            # failure. Always clean attempted downs before propagating failure.
            if self.injector:
                self.injector.release_all()
            raise

    def feedback(self, mask, now):
        self.last_feedback = now
        self._apply(mask, "feedback")

    def tick(self, now):
        if self.buttons and self.last_feedback is not None and now - self.last_feedback > self.timeout_seconds:
            self.disconnect("feedback timeout")

    def disconnect(self, reason="disconnect"):
        try:
            self._apply(0, reason)
        finally:
            if self.injector:
                self.injector.release_all()
            self.buttons = 0
            self.last_feedback = None
