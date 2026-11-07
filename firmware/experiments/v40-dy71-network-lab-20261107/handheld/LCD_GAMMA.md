# LCD gamma presets

On supported revisions, open **Settings → Display → Gamma** and use Left/Right
to select **Default**, **Low Gamma**, or **High Gamma**. The driver applies the
selection immediately, and the `lcd-gamma` NVS key is flushed after a successful
change. Default uses the original firmware's vendor gamma bytes exactly.

## Controllers

| Firmware feature | Panel | Control |
| --- | --- | --- |
| `rev1`, `rev2` | ILI9488 | `0xE0` positive / `0xE1` negative, 15 bytes each |
| `rev4` (including Rev4.1) | ILI9806E | Page 1 `0xA0–0xAF` positive / `0xC0–0xCF` negative |
| `rev3` | ST7262 | No connected command interface; Display/Gamma entry absent |

Runtime gamma writes are supported in normal operation and sleep according to
the [ILI9488 datasheet, sections 5.3.33–34](https://files.waveshare.com/upload/2/2d/ILI9488_Data_Sheet.pdf)
and [ILI9806E datasheet, sections 4.4.38–39](https://www.displayfuture.com/Display/datasheet/controller/ILI9806E.pdf).
ILI9806E selects page 1 only for the gamma writes and attempts to restore page 0
even if a transaction fails. It does not write the page-1 `0xE0/0xE1` OTP commands.

Low and High are conservative, **uncalibrated** analog-register tuning presets,
not specified gamma exponents such as 1.8 or 2.4. ILI9488 adjusts the unpacked
gray-20/43 controls by ±4; ILI9806E adjusts gray-52 through gray-203 controls by
±1. Each polarity retains its own vendor baseline, and the endpoints, packed
fields, voltage rails, VCOM and display timing are unchanged. Physical panel
measurements are required to confirm the intended Low/High direction and tune
the strength of the visual effect. No FPGA pixel correction is involved.

## Lifecycle and failures

- Missing or unknown stored IDs select Default (IDs 0/1/2 are stable).
- The saved preset is applied just after LCD initialization, before display use.
- Both drivers retain the last fully written preset and reapply it before
  display-on when waking (including undocking).
- Runtime write failures attempt to restore the last successful curve, leave
  the saved choice unchanged, log the error, and show a notification.
- If a saved preset fails at startup, Default is restored and saved. Failure
  to restore Default is reported as an initialization error.
- NVS writes use the existing KVS framework. As with other settings, storage
  transport failures follow its existing panic behavior.

SPI writes are not synchronized to a panel frame boundary, so a brief transition
artifact is possible. Neither driver has register readback in this implementation;
successful SPI transfer is not physical readback verification. A persistent SPI
fault can also prevent rollback/page restoration; errors are logged rather than
claiming success. Panel calibration, actual reboot persistence, sleep/dock
behavior and visual Default restoration still require on-device verification.

## Code map

- `src/device/drivers/lcd_gamma.rs`: stable preset IDs, labels, curve pair type.
- `src/device/drivers/{ili9488,ili9806e}.rs`: panel tables and command sequences.
- `src/device/drivers/mod.rs`: shared module registration.
- `src/device/mod.rs`: device integration with the gamma lifecycle policy.
- `src/device/gamma.rs`: startup restore, runtime application, rollback and persistence
  through statically dispatched panel/storage adapters shared with the tests.
- `src/kvs/keys.rs`: key and shutdown flush registration.
- `src/ui/state/settings.rs`: existing list widget integration.
- `src/ui/state/settings/gamma.rs`: gamma callback and selected-value mapping.
- `src/ui/state/settings/pages.rs`: board-gated settings definitions.
- `tests/lcd-gamma`: 32 distinct host regression tests with mock transport/storage;
  30 run for each of Rev2/Rev3/Rev4 (the visibility test varies by board).

To add another preset, assign a new stable enum ID, extend the labels and each
driver's match/table, and add test coverage. A future custom-curve API should
validate each controller's field widths before writing; UI code should continue
to operate on preset/settings values rather than raw registers.
