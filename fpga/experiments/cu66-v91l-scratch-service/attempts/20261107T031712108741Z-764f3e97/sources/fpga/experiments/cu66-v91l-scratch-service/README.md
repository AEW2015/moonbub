# V91l packed scratch SDRAM service

Simulation-only physical scratch endpoint and transaction arbiter. The frozen
video service retains banks 0–2 and its existing bounds. Scratch owns the first
262144 bytes of SDRAM bank 3 (word aperture 0xc00000–0xc1ffff). Every logical
request is a full, aligned 16-byte line with a nonzero epoch. Writes issue eight
single x16 commands, and reads issue one BL8 command and capture all eight beats.
No masks, RMW, hidden memory preload, or extra controller instance are used.

Ownership covers accepted physical commands, controller drain, and the held
logical response. Reset/cancel stops unissued commands, drains accepted work,
and returns an error. An offered response remains immutable under a late kill.
Partial canceled writes remain in the private scratch aperture; this is not an
atomic rollback promise. Video ownership and protected frame contents remain
isolated. Two consecutive idle observations fence physical scratch retirement.

Run `python3 scripts/cu66-v91l-scratch-service/run.py`. Directed simulations use
Verilator 5.020, finite watchdogs, strict warnings/assertions, and the unchanged
functional timed SDRAM model at tAC 2 ns and 7 ns. They do not establish routed
frequency, board electrical margin, native end-to-end throughput or hardware fit.
