# V91l reference tile grant contract model

This experiment models a bounded arbitration policy for the existing 64-byte
reference tile reader. The legacy mux rotates on each accepted 16-byte
physical command. The candidate policy gives the reference reader one grant
for up to four contiguous 16-byte commands, then makes display eligible. A
parameter value of one is defined to retain the legacy per-command rotation.

The model checks:

- Every luma/chroma tile begins on a 64-byte boundary, all four chunks remain
  within one physical 1024-byte row, and every chunk is aligned and inside its
  plane and 19-bit physical address range. Plane bases are 0, 345600, and
  432000 bytes.
- A grant covers no more than one 64-byte tile. The proposed maximum gap is
  eight abstract cycles while a grant is reserved and the reference offers no
  continuation. The RTL does not count time spent waiting for bridge request
  readiness or response acknowledgement/drain. The model checks release
  conditions for a full tile, malformed next descriptor, cancellation,
  physical error, and timeout; it does not simulate cycle timing.
- A ticket is a separate nonzero 32-bit physical identifier. Increment wraps
  from `0xffffffff` to 1. Epoch and bank remain part of the transaction
  identity, and the captured descriptor identity remains stable while a reply
  is held.
- An accepted physical operation drains before an error reply is offered. A
  held response remains owned through wrong response tags and caller metadata
  changes, and is released only after explicit acknowledgement.
- The reference path supplies a nonzero 32-bit physical epoch/ticket and
  source bank 0–2; the mux captures and matches those tag fields. The tile
  reader's 32-bit ticket wraps from `0xffffffff` to 1. The first
  legal 64-byte tile base is 0 and the last is 518336, ending at byte 518399
  (exclusive end 518400).
- Under contention, the schedule grants one display 16-byte command after
  each reference grant. The candidate's reference grant contains four
  contiguous commands; the legacy grant contains one. Schedule counts do not
  represent elapsed time or controller throughput. The checked schedule keeps
  display continuously pending and asserts the maximum uninterrupted
  reference service is bounded by one grant.

The existing directed overlap case observed 7,806 reference tile requests,
equivalent to 31,224 physical 16-byte/BL8 reads. Those traffic counts are
retained unchanged by this policy model. Existing pin analysis reports 18,000
additional bank-0 ACTIVATE commands with the overlap workload while the same
548 unique bank-0 rows were activated. This is a row-locality hypothesis for
the next experiment; it does not establish that row changes caused elapsed
time or that tile grants improve performance.

## Run and reproducibility

From the repository root:

```sh
python3 experiments/python-gamebub-v91l-tile-grant/grant_model.py
python3 experiments/python-gamebub-v91l-tile-grant/grant_model.py --check
```

The generated [model-results.json](model-results.json) records SHA-256 hashes
for the legacy reader sources, candidate mux RTL, prior overlap docs, and its
summary and pin traffic inputs. `--check` recomputes the model and refuses
stale results.

This is an independent Python contract model, not a full functional FPGA
simulation, RTL verification, SDRAM timing model, or hardware result. It makes
no timing or speedup claim and does not qualify sustained 30 fps.
