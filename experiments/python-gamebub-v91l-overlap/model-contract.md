# V91l native decode/display overlap model

This independent Python model records the bank ownership contract needed for
the next native overlap experiment. It is an abstract state model. It does not
verify new RTL, model the SDRAM arbiter, or claim complete-system timing.

## Source sequence and leases

The intended schedule is:

1. Decode, validate, and publish the key into video bank 0.
2. Present key bank 0, clearing its pending-publication slot, before starting
   the key RGB read lease.
3. Keep bank 0 leased as the key RGB source while delta decode reads accepted
   reference bank 0 and writes its candidate into bank 1.
4. After delta validation and physical candidate-write drain, advance the
   accepted-reference identity to delta bank 1. This does not end key RGB's
   physical read lease or move the current front.
5. Publish and present delta only when vblank and scanout drain allow the front
   swap. Release key bank 0 for candidate reuse only after its consumer lease,
   outstanding RGB reads, and front ownership have all ended.

The source allocator in `cu66_frame_bank_control.sv` protects accepted
reference, front, pending, and active-writer banks. Its `safe_swap` requires
both vblank and scanout drain. The native overlap contract adds a distinct
source-provenance lease for a physical RGB reader: changing `ref_bank` to 1
cannot itself prove that an RGB reader has stopped accessing key bank 0. The
model checks this additional lease explicitly and enforces that a new key
starts RGB only after key publication/presentation has completed.

Publication also waits for the actual writer drain. A response lease captures
epoch, generation, bank, and address. The abstract cancel cases cover a cancel
before any physical acceptance and a pending cancel after two accepted
operations. Accepted work drains before an error response; unaccepted work is
suppressed. A held response stays immutable under backpressure and descriptor
change, and only acknowledgement of that response releases its lease. These
are behavioral contract checks, not evidence that the current hardware has
implemented or passed the new overlap path.

## Traffic and timing arithmetic

Traffic counts are copied from the retained two-source physical scratch
campaign's measured result table and machine-readable summary: key has 3,938
scratch writes plus 3,938 scratch reads (35,442 controller commands); delta
has 3,091 writes plus 3,091 reads (27,819 commands). Each RGB output is 345,600
pixels / 691,200 bytes and 32,400 logical and physical reads. Input file and
source SHA-256 values are captured in `model-results.json` to make the check
independent of prior result status claims.

The isolated stage intervals are the source result's cycle intervals converted
at its assumed 100 MHz: key decode 29.00464 ms, key RGB 29.68636–29.69672 ms,
delta decode 33.46038–33.46534 ms, delta RGB 29.68215–29.69177 ms. The nominal
serial component sum is 121.83353–121.85847 ms. Ideal component arithmetic for
key decode, then `key RGB || delta decode`, then delta RGB is
92.14717–92.16175 ms. This is only a zero-contention optimistic lower bound;
these arithmetic intervals use only the named component stage intervals. They
omit interstage and qcache/preload gaps and therefore are not an actual complete
two-frame pair measurement. The native campaign's pair metric is measured from
key native start through final delta RGB closure, including those gaps, and is
compared with the same-seed/tAC serial control using its raw start/close fences.
No shared-controller contention or native overlap timing is estimated here;
consult the campaign's measured results for those values. Delta decode alone
exceeds the 33.333 ms 30-Hz frame slot, so overlap by itself cannot establish
30 fps.

## Reproduction

Run `python3 experiments/python-gamebub-v91l-overlap/overlap_model.py` to
generate `model-results.json`, and `python3
experiments/python-gamebub-v91l-overlap/overlap_model.py --check` to verify the
deterministic result. The model reads but never rewrites prior experiment
evidence. The current baseline identifier is recorded in the JSON.
