# Registered upload credit: isolated timing candidate

`qualification-v001.json` seals the timing-equivalent implementation. The selected
stager and controls, active board builds, PHY, map and timing constraints were not
modified. No Vivado run or hardware test was performed for this candidate.

The CSR's combinational 32-bit remaining subtraction followed by a count mux and
the stager's 33-bit sum/comparison are replaced by redundant registered modular
remaining bytes, saturated count and an explicit `written_bytes<=packet_bytes`
flag. All full-width begin validation is retained. `source-proof-v002.json` is the
current source binding; the initial `derivation.json` and failed evidence retain
the earlier syntax and overshoot-assumption failures for audit, not selection.

Finite proof covers 900,000 randomized simultaneous-input cycles across five
MAX_BYTES values, every count0..7, full49152-byte CRC/readback and the actual typed
CU71/DY71 async bridge suite. Arithmetic checks include reduced-width exhaustive
domains and full32-bit wrap boundaries. This is not unbounded formal equivalence.

The original interface permits upload and discard together in LOADING with no
held bytes: both accept, discard enters EMPTY while retaining the new held count.
A later smaller BEGIN drains stale bytes beyond its packet. The actual split CSR
reproducer accepts a3-byte upload concurrently with DISCARD, ACKs success and later
writes3 bytes for a1-byte BEGIN, without a staging fault. See
`evidence/control-edge01`. Physical bridge delivery of this adversarial schedule
was not tested. The reviewed v36 driver waits for command ACK/status and waits for
each exact written-byte count, so it does not issue this overlap; that does not
make arbitrary bus traffic safe.

The explicit successor `safety-v002` rejects simultaneous discard/upload in both
the stager and CSR, and gates begin_ready on empty held bytes. It deliberately
changes malformed-input behavior. Its separate qualification records ordinary
cycle equivalence,900,000 fresh-history invariant checks, actual CSR rejection,
and18 unchanged v36 SDK/native endpoint tests. The SDK tests use a software CSR
model; they are separate from the actual RTL tests.

Before selection: independent review, measured unchanged-constraint OOC, actual
SDK/RTL co-simulation, then full-board timing/fit/CDC. No timing improvement is
claimed from source structure alone. The redundant counter adds expected36
register bits and its own update path must be measured.
