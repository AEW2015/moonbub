# V128: parallel validation and incremental header padding

V128 passes its bounded functional regressions but **does not meet 125 MHz**.
The fresh 8 ns component route measured **−1.320 ns WNS**, −3,146.811 ns TNS
and 10,006 failing setup endpoints. V127 measured −1.193 ns and 6,980 failing
endpoints. This source is not promoted as a 125 MHz timing-closed design.

The selected RTL compares complete RAW and context coefficient tuples in
parallel before selecting the validation result. It also accumulates the header
padding check as bytes 116–127 arrive, using one unreset owned payload bit. Five
of 18 component source origins changed; the public cycle count and encoded data
format are unchanged. These are logical source structures; physical mapping and
routing are measured separately.

| Evidence | Result |
| --- | --- |
| Python raw-tuple algebra | 71,066 cases and 568,528 phase comparisons; no mismatches. This is a finite model, not sequential or physical proof. |
| Focused actual RTL | Six seeds passed, including two paired-scratch clocked seeds and two source-extracted padding-kernel seeds. |
| Full decoder/transport, peer and byte/row parent | Four, two and four exact stream comparisons passed against V127, with zero public-cycle delta. |
| Targeted RAW-mode to scratch state | −1.193 ns → +1.118 ns; the targeted path improved while global timing regressed. |
| 125 MHz route | WNS −1.320 ns; TNS −3,146.811 ns; 10,006 setup failures. Hold and pulse checks passed. |
| Routing and internal clock coverage | All 74,852 routable nets routed, zero routing errors and zero unconstrained internal endpoints. |
| Routed resources versus V127 | 34,504 LUTs (+928), 43,432 FFs (−162), 42 DSPs and 32 RAMB36 + 12 RAMB18 (unchanged); 1,233 control sets (−20). |

The independently audited worst path is in the Rice parser, from its
`cached_remaining` register to `out_consumed`. A separate dense-owner path and
scratch write-control paths also fail. The [next timing proposal](next-timing.md)
uses the measured paths and describes how to verify a latency-changing register
boundary without weakening ownership, cancellation or memory-acknowledgment
checks.

The retained row profiles take **1,145,104 / 1,553,197 cycles** from the final
accepted outer input to validated commit. At an *assumed* complete-parent
125 MHz, those are **9.160832 / 12.425576 ms**; the stalled profile needs at
least 303,198 fewer cycles for strictly under 10 ms. V128 preserves those cycle
counts, and the complete parent has not been routed at 125 MHz.

The independent terminal audit passed 1,654 evidence checks while explicitly
reporting `design_timing_pass=false`. This is an out-of-context component build:
1,101 inputs and 12,887 outputs lack external delay constraints. Actual ESP32
Wi-Fi/QSPI service, the complete parent and board timing, sustained hardware
30 fps, and hardware-validated sub-10-ms decoding remain open. No board
bitstream was generated or hardware programmed. The existing
[B100 control](../cu66-v120/handoff.md) remains the separate qualified component
baseline.

The checked-in study runners use Docker, Vivado 2026.1 and a compatible local
license. Their existing tool and build-directory paths are specific to this
Linux host; another system must adapt those paths and rerun qualification. The
routed checkpoint is recorded as an external artifact, not included in this
source package.

See the [functional results](functional-results.md), [routed timing results](timing-results.md),
[padding observations](padding-inspection-results.md),
[source selection](../../fpga/experiments/cu66-v128-raw/selected-composition.json)
and [machine-readable result](../../experiments/python-gamebub-v128/results.json).
