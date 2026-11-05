# LCD gamma host tests

**32 distinct tests: the original 7 plus 25 additions.** Each revision runs 30:
29 common tests and one board-specific settings-visibility test. Run all three
revision configurations to exercise the complete set (90 passing executions).

On this Windows workspace, run the complete matrix from any working directory:

```powershell
.\firmware\handheld\tests\lcd-gamma\run-tests.ps1
```

The path above is relative to the repository root; an absolute script path also
works. Use `-Board rev4` for a single configuration.

Run from the repository root (outside `firmware/handheld`, to avoid the embedded
Cargo configuration):

```powershell
cargo +stable test --locked --manifest-path firmware/handheld/tests/lcd-gamma/Cargo.toml --target x86_64-pc-windows-msvc
```

The tests import the real LCD drivers and the production KVS implementation.
Only the SPI transport, output pins, and NVS backend are mocked. They check
original gamma bytes, register addresses and field widths, preset restoration,
page cleanup after every possible ILI9806E write failure, rejected ILI9488
changes, wake behavior, and persistence after discarding the KVS cache.

These tests do not measure panel luminance, emulate flash wear or NVS power-loss
recovery, or replace on-device reboot and visual tests.

## Additional coverage

`tests/additional.rs` implements the 25 requested cases:

1. Settings callback sends the selected preset to the driver.
2. Successful changes display the applied selection.
3. Failed changes display the previous selection.
4. Failed changes notify exactly once, including rollback failure.
5. Invalid UI indices have no hardware/storage side effects.
6. Selecting the saved preset avoids redundant NVS writes.
7. Rapid Default/Low/High changes finish with High applied and saved.
8. Rev4's real settings schema exposes all three presets.
9. Rev2's real settings schema exposes all three presets.
10. Rev3's real settings schema contains no gamma entry.
11. The unsupported-panel API leaves storage untouched.
12. Startup without a saved setting applies Default after initialization.
13. Startup applies saved Low after initialization.
14. Startup applies saved High after initialization.
15. Unknown stored IDs select Default in hardware and the UI mapping.
16. A failed startup application attempts Default restoration.
17. Successful fallback saves and displays Default.
18. Failed fallback returns an initialization error without saving.
19. Partial runtime failures rewrite both previous curves on both controllers.
20. Failed runtime changes neither update nor flush storage.
21. Failed rollback reports failure and preserves the saved value.
22. Saving follows all LCD writes, including ILI9806E page restoration.
23. Reinitialization restores original curves and remembered Default on both controllers.
24. Gamma failures during wake prevent Display On on both controllers.
25. Runtime gamma changes never toggle reset or issue unrelated display commands.

## Production code exercised

The device now delegates initialization and changes to `src/device/gamma.rs`.
The settings callback and selected-row value delegate to
`src/ui/state/settings/gamma.rs`; the actual page definitions are in
`src/ui/state/settings/pages.rs`. The tests import these exact modules, rather
than implementing copies of their behavior. The extraction retains the existing
runtime policy and uses static dispatch.

Lifecycle tests use local mock panel/storage objects to inject errors and record
ordering. Transport tests additionally use the real ILI9488/ILI9806E drivers.
The original persistence test exercises the production KVS adapter, cache and
serialization with mock NVS. The real board-gated settings definitions are
compiled for each revision; only the unrelated `About` screen ID is stubbed.

The suite exercises the production gamma callback adapter and selected-value
mapping, not a running Slint event loop, widget rendering, or physical key input.
