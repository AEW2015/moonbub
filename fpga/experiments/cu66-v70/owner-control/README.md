# V70 receiver owner and diagnostics control test

This bounded C++ self-checker instantiates the actual frozen `cu70_receiver`
RTL with `WATCHDOG_CYCLES=512`. It does not modify the DUT or provide a golden
reference path. It uses the same receiver source list as the full receiver
qualification, in a separate `/build/v70-owner-control` build directory.

```sh
python3 fpga/experiments/cu66-v70/owner-control/run.py
```

The retained Verilator result is `OWNER_CONTROL_PASS`: **618 assertions in561
modeled clocks**, with source hashes unchanged before/after. Coverage includes:

- Zero generation and 32-bit packet lengths0/65,536 reject immediately before
  narrowing or issuing a packet request. A reused generation rejects after a
  prior admitted transaction. Thirteen invalid starts are rejected across the
  complete test, including deliberate repeated probes to wrap the event ring.
- A fresh generation with admitted length24,758 accepts its first packet-read
  request. Its matching response is withheld until the configured watchdog
  raises error0x7f. This tests an admitted request lease, not a decoded packet.
- Same-generation wrong-sequence and wrong-address responses, plus a wrong-
  generation response, are consumed as stale without satisfying the live read.
  Packet/HUD-result/HUD-drain/software-ACK stale completions arrive together;
  all four count, rather than losing increments. The final stale count is10.
- Watchdog DRAIN remains busy and blocks new starts while the accepted read
  is outstanding. Stale completions during DRAIN do not free it. Only the
  original matching generation/sequence/address response permits drain to IDLE.
- No canonical/reference/front frame is published; accepted and presented
  counts remain zero.
- Public diagnostics retain the first fault across later failures, clear and
  re-arm it explicitly, report the proper generation/stage/address, preserve
  stage timestamps, and expose a checked bounded event ring. Sixteen events
  produce eight overwrites; retained sequence/time/payload words are checked.

`results.json` records commands, actual log hashes, all RTL/include/test sources,
the imported source-list runner and counts. `--Wall` diagnostics remain fatal
except the established explicit-empty diagnostic output selection. The test
has a2,000-cycle guard and requires both normal exit and the explicit PASS.

This is negative/control/diagnostic qualification only. It does not decode a
complete frame, execute the processor HUD service, measure software latency,
exercise physical memory/panel behavior or establish30fps, target fit or timing.
