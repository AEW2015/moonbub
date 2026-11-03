# Python Game Bub v8 evidence audit

`audit.py` independently recomputes the stored v8 codec/rate rows and checks all
declared source pins before and after the audit. It verifies fixture file hashes,
GF01 packet/datagram/wire accounting, candidate attempts and timing component
sums, complete GM01 packet caps separately from wire bytes, and exact common-ID
MSE comparisons. It distinguishes each DCT analysis from the three Y/U/V plane
transforms and checks decoded ROI scale-8 evidence for admitted priority rows.

Source ID, native PTS, frame hashes, and quality comparisons are kept tied to
exact shared IDs. Missing fields are reported as missing evidence. A mean timing
or immediate protocol ACK is not treated as proof of 30 distinct presented
frames/s or physical memory read-drain.

The stored evidence contains 72 codec packets, 120 rate-controller decisions
(96 real-video policy decisions and 24 synthetic stress decisions), and 8
golden frame fixtures. The audit reports 108 admitted and 12 rejected rate
decisions, with at most two materialized candidate packets per decision. These
offline host results do not establish real-time 30 distinct displayed frames/s
or physical memory read-drain.

The size study adds 32 paired calls. Exact preflight packet sizes match all
materialized candidate sizes and preserve selection and packet hashes. The
cheap gate lower bounds stay at or below the actual packet sizes; emitted sizes,
selection and packet hashes match the full encoder. Per-row RGB hashes are not
stored, though both benchmark paths assert decoded RGB hash equality during
their runs. The frozen-prior check matches all 72 prior packet hashes and checks
216 plane lengths.

Timing remains separated by input class: exact preflight reduces the seeded
noise reject mean from 113.48 ms to 43.24 ms, while its real normal and pressure
means rise from 32.66 to 34.62 ms and 35.96 to 37.37 ms. The cheap gate reduces
the noise reject mean to 25.04 ms with zero serialized candidates (28.68 ms
maximum); normal input changes from 33.52 to 32.93 ms, while pressure changes
from 37.07 to 37.75 ms. These are paired offline host samples under uncontrolled
load, not a default normal-path speedup or a 30 fps result.

Run with `python3 audit.py` and `python3 -m unittest -v test_audit.py`.
