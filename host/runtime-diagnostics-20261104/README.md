# Firmware v24 diagnostic source and host checks

This export contains seven byte-identical source files from sealed
`v24-runtime-diagnostics-20261104`: the changed/new integration modules, existing
telemetry dependency and pure test harness. `source-snapshot.json` binds them to
their original paths, the 553-input inventory and sealed build manifest.

Run with Python and the rustup Rust stable proxy:

```text
python run_tests.py --rustc C:/Users/lavat/.cargo/bin/rustc.exe
```

The SDK-free runner verifies all seven bindings and executes 14 tests: four new
formatting checks and ten inherited telemetry checks. Compilation happens in a
temporary directory. It does not need ESP-IDF, the complete application, a serial
port or the device. It does not build or install firmware.

The new `?` command queries reset reason, uptime, variant, SDK app descriptor,
embedded ELF identity and memory/USB stack values. It preserves `r` as the CRC
benchmark. The large legacy `t` frame/queue Debug records are replaced by bounded
`USB_D24 v=1` pages. Existing brief `s` and AV pages remain. Consumers must retain
the new prefix; the old trace parser is not a parser for these pages.

Pages carry capture `c`, sampled software source generation `g`, presentation
epoch `e`, frame `f` and page name `p`. Begin/end pages describe sampling and
after-generation/epoch observations. Matching markers do not establish an atomic
snapshot or bind the separately sampled frame to an epoch. Runtime SDK ELF SHA
is distinct from the source inventory and complete installed BIN identity.

Worst-width tests cover 28 page shapes, with a maximum 161-byte payload and no
formatter heap allocation. The 64-byte logger reserve is modeled: actual ESP
framing, logger/worker overhead, nested stack use and reboot behavior require
physical verification. This code does not claim to fix the unexplained v22 reset.

The complete local v24 application separately passed 371 host-test executions,
target build and verification of 12,301 application-only UF2 blocks. Its SDK
configuration matches v22. Those broader checks are not executed by this runner.
The export omits the rest of the application, SDK and binary artifacts; restoring
the seven files alone does not constitute a complete firmware checkout.
No streaming wire format, port, profile or FPGA capability is introduced.
