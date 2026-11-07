# Scope and independent review

The new scratch oracle preserves the frozen source-backed native canonical,
SHA/C2/HUD/seal, protected-bank, reference-tile, quantizer-cache, RGB565 and
publication checks. Common SDRAM pin state is learned only from actual pin
WRITE commands; scratch and video share one timing/open-row/read-capture
oracle. No golden output or logical write request populates that memory.

Scratch request and response records are correlated between native C++ and
SV handshakes, including all 128 data bits, epoch, address, operation, native
source ID and per-frame transaction index. Successful reads require prior full
physical write ACKs for the matching child epoch. Read captures and response
assembly are checked against pin memory. Source-frame aggregation uses the
native source ID: the key has child epochs 1/2/3 and the delta 4/5/6, whereas
their outer frame epochs are 1 and 2. The first audit draft incorrectly grouped
these child epochs as frame epochs; independent review identified this and the
qualified checker now preserves both groupings separately.

Independent review also strengthened exact coverage of completed native SHA
frame groups, rejection of leftover digest groups, and binding reported native
start counters to actual start receipts. All 1,025 SHA jobs for each of the
selected frames must match the original independent hashlib oracle; the mode
summary cannot omit a frame while claiming a complete result.

Same-edge ordering normalizes pre-NBA observations only. It establishes owner
changes before arbitration, offered immutable replies before warm cancellation,
native request witnesses before inner accepted requests, and physical replies
before their consumers. Different simulation times are never reordered.
Directed invalid/cancel stimuli, stable payload assertions and exact prefix
checks remain source-reviewed self-checking tests. This does not establish
exhaustive formal, electrical, placement/routing, full-profile or hardware proof.
