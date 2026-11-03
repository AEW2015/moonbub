# Timing and clock-domain review

The final reports under `fpga/build-final/` determine the implementation gate.
The failed/stopped attempts are preserved under `fpga/attempts/`. This review
describes the custom CDC protocols; it is not a waiver of a report violation or
qualification of external pin margins.

| Crossing | Stability/ownership rule | Physical constraint |
|---|---|---|
| QSPI write queue | Source writes RAM before advancing Gray pointer; consumer sees the pointer through two stages, and advances only after accepting a word. | Read-pointer first stage bounded to 10 ns, write-pointer first stage to 5 ns; bus skew also bounded. Following stages remain timed. |
| QSPI read address | Address remains held through request/response acknowledgment. Core drains preceding writes before snapshot. | 10 ns bundled-data maximum into the address capture; first token stage only is excepted. |
| QSPI read response | Response is registered before acknowledgment; it remains stable until a later read. | 10 ns bundled-data maximum into the SPI snapshot. |
| LCD line request | Pixel-domain line number stays held from request until 480 returned words and completion acknowledgment. Core captures the raw line number before address arithmetic. | 10 ns into explicit `captured_line` registers. Source and destination raw payload registers remain explicit. |
| LCD line completion | A bank is readable only after the completion token crosses two stages and its line/epoch matches. A good line cannot switch source midway. A late line stays black. | Only the first token stage is excepted. Dual-clock BRAM has an unconditional synchronous pixel read port. |
| LCD underrun count | Registered Gray count crosses two stages; decoded telemetry is separate from frame data ownership. | Source-period 34 ns maximum/skew into first-stage Gray registers. |
| Transport dropped words | Registered Gray loss count crosses two stages and is decoded into a registered core-domain snapshot. A change invalidates unpublished frame state, including a coincident presentation boundary. | 5 ns maximum/skew into the 32 first-stage telemetry registers. |

Gray source bounds use the actual source-clock register collection when needed
because synthesis can merge a Gray MSB with its binary counter/pointer register.
The destination collection is restricted to the relevant first-stage bus. Serial
synchronizers except bit zero only; bit one/two are ordinary timed recovery stages.
There are no global asynchronous clock-group exceptions hiding unrelated paths.

The first LCD implementation exposed two real problems: address arithmetic
absorbed the payload register into a pixel-clock DSP, and conditional RAM reads
inferred LUTRAM. The repair captures the raw payload in the memory domain before
arithmetic and uses reset-free, unconditional synchronous RAM read processes.
The revised synthesis reports identify both banks as true dual-clock block RAM.
Full scanout simulation retained its pixel, timing and underrun assertions.

The QSPI queue was also changed from an asynchronous LUTRAM data read to an
unconditional synchronous core-clock block-RAM read. A valid stage retires the
word only after the registered data is available, and mailbox reads wait for
both RAM and the staged word to drain. The bridge accepts up to one word per
two 100 MHz cycles; this remains above the 20 MB/s calculated quad-SPI ceiling.
Pin-level digital tests and deliberate-overload conservation tests pass after
the change.

The SDRAM receive architecture uses a 100 MHz clock at 279 degrees, an input
capture register, a command-clock falling-edge retiming register and a later
response cycle. It deliberately captures the previous returned data beat.
The 16 DQ-pad-to-capture paths therefore use a setup multiplier of two, guarded
by the exact 10 ns/7.75 ns receive waveform. No hold multiplier is applied:
the associated strong hold check must protect the capture against the next
returned beat. Routed I/O reports must show the intended setup/hold edges,
rather than merely a positive aggregate WNS. This follows the edge-selection
semantics in [AMD UG903](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/set_multicycle_path-Syntax).
Frequencies and the 7 ns/2 ns external data-delay budgets are unchanged.

Each SDRAM output data/T ODDR is SAME_EDGE with identical D1 and D2 nets, so its
falling output transition repeats its already-launched value. The exception
excludes only that non-transition through those 32 ODDR Q pins to DQ pads.
Runtime Tcl checks the cell count, SAME_EDGE property and identical pin nets
before applying it; rising-edge output checks and internal D1/D2 checks remain.

The JPEG output arithmetic is pipelined without changing coefficients or integer
rounding. A separate software model using that arithmetic matches every pixel
of the full-resolution fixture; an independent Pillow decode comparison remains
recorded separately. That comparison does not certify external memory pins.

External SDRAM tAC/board flight-time budgets and the MCU SPI output budget remain
explicit prototype assumptions. Input synchronizers make SPI sampling a digital
oversampling protocol, not proof of pin-level margin at 40 MHz. Routed setup,
hold, route, pulse-width, DRC, exception coverage and bus-skew reports must be
read together; a successful bitstream command alone cannot satisfy those gates.

The retained command-level SDRAM models check a bounded functional subset with
4 ns forwarded-clock flight and both 2 ns and 7 ns data-delay corners, using
distinct words across each burst to expose capture of the wrong beat. They are
not vendor timing models, PVT qualification, or observations of this board.
Hardware bring-up remains a separate gate.

Final offline implementation evidence: setup +0.031 ns, hold +0.014 ns, pulse
width +2.000 ns; zero failing setup/hold/pulse endpoints, 13,535/13,535 routed
nets and zero DRC errors. The final DQ input setup/hold minima are +0.395/+0.219 ns;
output setup/hold minima are +0.056/+2.588 ns. These retain the assumed budgets.

The final report has no unclocked or unconstrained internal endpoints and no
critical CDC findings. Four Gray-bus and 54 held-payload CDC warnings correspond
to the protocols above. Seventeen raw button/SPI inputs have no synchronous input
delay, CS has a partial-input-delay diagnostic, and two forwarded-clock ports
have no data-output delay. Those external interface assumptions remain explicit;
the reports do not constitute MCU pin-margin or physical board qualification.
