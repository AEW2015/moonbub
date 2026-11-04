# AKD1 first complete board route: failed setup

Candidate: `fpga/candidates/akd1-compute-lcd-prune-20261104`,
Vivado 2025.2, `xc7a100tcsg324-1`, top `moonshine_top_akd1`.
Manifest SHA-256:
`a36bcaa4d7e3cd1d7722b9ef7cf49bdc8b3d735c6cc467ce910a2cb81a0d84d1`.

These are exact copies of selected local records. The manifest inventories 101
artifacts; the complete candidate, checkpoints and all inventoried files are
not distributed here. Raw report whitespace is preserved to retain hashes.

| Routed check | Result |
| --- | --- |
| Setup | -2.184 ns; 13,629 failing endpoints |
| Hold | +0.007 ns; zero failing endpoints |
| Pulse width | +2.000 ns; zero failing endpoints |
| Route / DRC | Fully routed; zero DRC errors |
| CDC / active I/O review | Incomplete |
| Bitstream / hardware | Not generated / not tested |

The worst path launches from the QSPI command queue BRAM and reaches inverse
coefficient clock enables through abort/admission control: 11 LUT levels,
11.960 ns data delay (8.142 ns routing). This evidence does not support adding
latency to the operand-read mux. The follow-up isolates raw command decoding
from the compute-facing cancellation path while retaining controller STOP
priority and ordered CSR behavior. It must pass new cancellation-collision
tests and a complete route before it is a hardware candidate.

Unused SDRAM is explicitly inactive and unqualified. Internal compute OOC
closure, this failed board route and physical playback are separate results.
