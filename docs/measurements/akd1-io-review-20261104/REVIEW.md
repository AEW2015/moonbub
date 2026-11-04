# Independent AKD1 routed I/O and CDC review

Read-only review of the failed routed `akd1-compute-lcd-prune-20261104` parent,
manifest `a36bcaa4d7e3cd1d7722b9ef7cf49bdc8b3d735c6cc467ce910a2cb81a0d84d1`.
`review.json` binds 21 inspected source/report files. No build, candidate edit,
device/COM/USB/JTAG/SD operation or hardware observation was performed.

## CDC categories and coverage

`cdc.rpt` has exactly eight Gray-bus warnings: bridge FIFO write/read pointers,
transport overflow count, audio slot write/read pointers and audio consumed,
played and underrun counters. Source increments are one event at a time; resets
are a separate protocol case. Their first stages have explicit max-delay and
bus-skew constraints; all eight reported skew constraints pass (smallest margin
3.459 ns). This is not a waiver of reset/rekey behavior.

The 113 CE-controlled payload warnings are exactly margin 7 + timing 62 + bridge
read address 12 + bridge response 32. RTL holds each payload through synchronized
request/acknowledgment and has exact endpoint datapath bounds. There is no new
unknown CDC category in this parent. First-stage false paths cut D only, leaving
following metastability recovery stages timed. `ASYNC_REG` alone does not prove
multibit coherency; the Gray and held-data protocols supply the rationale.

`check-timing.rpt` finds zero no-clock or unconstrained internal endpoints.
Its 17 missing input delays are 12 asynchronous buttons plus external SCK and
four DQ inputs, which enter the intended two-stage oversampling synchronizers.
CS is partially constrained by its separate CS-to-DQ max-delay path. These
warnings must not be hidden with invented synchronous input delays.
The two no-output-delay clock ports are forwarded LCD and DAC clocks.

## Finite output budgets versus physical qualification

LCD falling-edge output setup/hold reports are finite and positive: worst
+10.85/+15.885 ns under the existing +2/-1 ns budgets. The generated clock
matches the noninverting ODDR and named falling sampling convention. Panel/PCB
skew is outside this report review.

QSPI has a 10 ns datapath-only pad budget, with +0.581 ns worst slack on raw
CS-to-DQ ownership release. **External QSPI hold is NOT_PROVEN:** the min report
contains `Slack: inf` and `Timing Exception: False Path`, not a finite ESP32
sampling requirement. The passing 10 ns max constraint must not be described as
full QSPI setup/hold signoff or as proof of maximum bandwidth.

The endpoint source explicitly limits its digital validation to reads <=16 MHz
and writes <=40 MHz. At 200 MHz, external SCK traverses two sampling registers;
its detected falling edge drives `shift_out` on a subsequent core edge. With no
metastability extension, nominal falling-edge-to-output-register update is
roughly 10-15 ns. A <=10 ns pad-path envelope fits within the 31.25 ns half-cycle
of 16 MHz, leaving at most a nominal 6.25 ns residual budget in the pessimistic
phase combination. This is an explanatory nominal window, **not guaranteed
margin**: synchronizer metastability latency, ESP32 input setup, output-clock
skew, PCB delay and duty-cycle distortion are not established here. The digital
test/source cap supports a conservative lab experiment; prior build50 playback
does not physically qualify a newly placed bitstream. Retain its measured-rate
and min-dummy validation, then measure the new physical result before rate lift.

Audio's finite [0, one-MCLK] output envelope reports +23.956 ns setup and
+3.245 ns hold. The constraint comments explicitly call the DAC 8 ns/PCB budget
provisional. Audio is off in the AKD1 compute lab; these reports do not qualify AV
or acoustics.

## DRC warning review remains open

Zero DRC errors does not close DRC review. `CHECK-3` says `REQP-1839` details were
capped at 20. Visible warnings include audio sample BRAM write enables driven
through async-set `crst`, bridge queue write enables through async-set `rst200`,
and fixture ROM enable/reset controls through async-set `rst100`. The tool
explicitly warns about RAM corruption/read behavior during asynchronous reset
assertion that default STA does not analyze. An uncapped inventory plus a
per-memory reset/discard/fresh-write or ROM-output-valid justification is needed;
RTL reset tests cannot model the analog BRAM hazard. Do not waive these merely
because the modules match build50. DSP pipeline warnings are performance
suggestions; `RTSTAT-10` names only unused timing payload bits 60 and 61.

Unused SDRAM pins are explicit inactive constants/tristates. Their absence from
active timing is intentional and establishes no SDRAM memory qualification.

Overall remains INCOMPLETE independently of the known -2.184 ns setup failure.
Rebind the review to final successor reports; unchanged constraints do not imply
unchanged routed margins or warning inventory.
