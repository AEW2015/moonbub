# UI rendering and action regression

Run on Windows with:

```powershell
cargo +stable run --locked --manifest-path firmware/handheld/tests/ui-preview/Cargo.toml --target x86_64-pc-windows-msvc
```

This compiles the production Slint UI and drives it through the software
renderer at both menu resolutions. The test selects Reset color trims
and LCD RGB Lab repeatedly using actual key events, then edits a trim.
During those render passes it holds a mock device mutex, as the firmware
does. The settings callback uses try_lock so a lock inversion fails the
test instead of hanging it. Each press must invoke the action exactly once.

The old conditional FocusScope init activation failed this test with
`settings action ran while rendering held the device lock: WouldBlock`.
Action activation now occurs in the list's input callback. The test does
not replace hardware checks of the SPI transport or LCD appearance.

The value-refresh regression edits both trim lists, resets their model
values, and compares the rendered pixels with the neutral baseline. It
also rejects an edit to confirm the displayed value and next request use
the backend's confirmed selection. Before the binding fix, reset changed
the model but failed the pixel comparison. Gamma remains unchanged by the
color-trim reset.
