# V130 prequalification: admission and header timing experiments

V130 is the plan's hardware-qualification milestone, which remains open. This
work is a prequalification experiment on the V129 125 MHz timing problem; it
is not a deployable board image or evidence of hardware 30 fps.

* [Routed-path priorities](route-priorities.md) summarize the retained V128
  and V129 top-50 setup paths. V129 fails at −1.257 ns WNS.
* The [V130 route analysis](route-analysis.md) records −1.974 ns WNS and
  13,378 failing setup endpoints. This speculative-read candidate is not a
  timing improvement over V129 and is not selected for release.
* [Speculative admission read](spec-read.md) records the isolated actual-RTL
  candidate, valid-qualified pair checks, same-epoch retry, and fault controls.
  The physical read enable is changed; invalid response-data values may differ.
* [Consumer contract review](spec-read-consumer-contract.md) traces internal
  response-valid gating. The external `frame_read_data` invalid-cycle contract
  is not yet verified.
* [Header-fetch verification](../../fpga/experiments/cu66-v130-header-verify/README.md)
  records a separate, unselected candidate and directed paired-RTL tests.
* [Active-cell scan lookahead](active-scan-prefetch.md) records a separate
  paired-RTL and synthesis experiment for the new worst path. Its bitmap
  mapped to 1,350 flip-flops rather than BRAM; synthesis WNS was −1.760 ns
  versus −1.764 ns for its baseline. It is not selected or routed.
* [Full-parent exploratory receipt](../../experiments/python-gamebub-v130/full-parent/results.json)
  records byte and row cases against V129; the [independent review](../../experiments/python-gamebub-v130/audit/full-parent-second-review.md)
  explains the unchanged golden, ownership and physical-debt checks and the
  difference between exact recorded streams and all-port-cycle equivalence.

The candidate's additional [spatial and peer recorded-stream comparisons](../../experiments/python-gamebub-v130/audit/spatial-peer-independent.json)
also passed against V129. They do not establish invalid-cycle external-port
equivalence. A passing component route would not
qualify the complete board, actual I/O constraints, ESP32/Wi-Fi transport, or
hardware timing. Sustained 30 fps and under-10-ms validated FPGA decode remain
open; V129's stalled parent case needs at least 303,198 fewer cycles at an
actually achieved 125 MHz to meet the latter threshold on the measured boundary.
