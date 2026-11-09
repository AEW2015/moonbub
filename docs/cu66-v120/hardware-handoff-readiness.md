# V120 hardware handoff readiness review

## Local device check

Read-only USB enumeration found one Digilent FT2232C/D/H bridge (`0403:6010`, serial `210292747873`) with `/dev/serial/by-id/usb-Digilent_Digilent_USB_Device_210292747873-if01-port0` pointing to `/dev/ttyUSB1`. No `/dev/ttyACM*` device was present. This identifies a Digilent USB bridge, not the attached FPGA board model; it cannot distinguish Game Bub Rev4 from VCS3. No programming or service changes were made. See [hardware-discovery.json](../../experiments/python-gamebub-v120/audit/hardware-discovery.json).

## Existing board integration

The repository has a full older `moonshine_top` in [moonshine_top.sv](../../fpga/rtl/moonshine_top.sv), with an MCU 4-bit SPI/QSPI endpoint, a 100 MHz core/SDRAM domain, a 16-bit SDRAM interface, LCD scanout, and an ESP32 overlay path. Its core is `moonshine_core`; the experimental `cs88_pipeline_v91k` is not instantiated in this hierarchy. Existing platform/button pin constraints and Rev4 LCD/SDRAM/button pin files plus SDRAM and final build scripts are available. They do not compose or constrain the V120 decode pipeline as a complete board design.

The board-level work still needs an exact selected V120 source composition connected to ingress, refill, decoder, memory ownership, and presentation; complete clock/reset/CDC and board constraints; a full-design timing route; and a board test recipe tied to the exact source manifest. The target board and wiring must also be identified on the other test system.

## Keep the clock lanes separate

V118 is the stable repeat-qualified 100 MHz out-of-context reference. V119 also has repeat-qualified 100 MHz component results, but its own manifest says it is not recommended as a stable baseline replacement; its 125 MHz attempt is unqualified. V120’s context-terminal unit pass is unselected and adds no clock qualification.

Source B now has a [qualified 100 MHz component handoff](handoff.md) and [source-bound manifest](../../experiments/python-gamebub-v120/handoff.json). Both fresh implementations passed at +0.174 ns setup and +0.028 ns hold. All 18 selected source/include files match the hardware team's `69c0f145` pin. The 125 MHz result remains a separate failed timing target at −1.517 ns. A component-only result retains its OOC scope; keep V118 available as the stable control.

The top level and board constraints required to exercise the selected V120 pipeline together remain outside the selected component composition, and the historical local USB observation does not establish which board is connected. Both 100 MHz receipts and the independent repeat audit are finalized. No complete board bitstream or hardware frame-rate/latency result is claimed; follow the [remote bring-up instructions](remote-hardware-test.md) for the other test system.
