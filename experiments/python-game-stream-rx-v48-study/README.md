# V48 integrated tile receive: exact references, lower staging, slower Python

This experimental receiver combines the V44 block iterator, V45 mirrored Q14
inverse and direct per-tile motion prediction. It accepts the arithmetic-only
CS38 capability (dispatch5/6); legal legacy dispatch0–4 is explicitly rejected.
The complete V43 receiver remains the compatibility control. This is not a
transparent replacement for every valid CS38 packet.

The campaign replays577 causal receives across eight retained histories, with
three alternating whole-call pairs per packet. It reconstructs4,673,700 full-grid
tiles while consuming4,530,538 actual AB38 tiles; compact payloads supply implicit
hidden zeros. Every coefficient hash, normalized reference, HUD word, displayed
RGB565 hash and final receiver state matches direct V43. Independent replay passes.
Five producer and three independent tests cover exact key/P handling, half-pel
border clamp, quantizer tables, immutable ownership, late-failure atomicity and
explicit legacy rejection. Guards prove the path does not call whole-plane
coefficient decode, whole-plane prediction or whole-plane inverse reconstruction.

## What is staged

The component delivers one128-byte coefficient tile, dequantizes and inverses it,
predicts the corresponding8×8 region and writes reconstructed samples. Q tables
come from the declared macroblock scale, rather than a full per-block table array.
Both original rounding boundaries, zero/DC cases and fractional motion phases
are exact. Negative-coordinate +1 taps clamp the original coordinate correctly.

It does not stage whole coefficient or prediction planes. Full current reference,
reconstruction and normalized YUV planes remain Python models of external-memory
banks; each full set is1,036,800 bytes in this int16 host representation. The
compressed frame and sliced components, HUD, tags/maps, Python temporaries and
inverse/prediction tile scratch also remain. Thus128 bytes does not describe the
whole receiver or prove a BRAM/ESP32 allocation fit.

No state is published until all entropy streams finish, hidden coefficients are
checked, pre-normalization and canonical tags match, and HUD validation succeeds.
Normalized planes and privately owned HUD words publish read-only. Later failure
leaves the old state unchanged. This is a software publication invariant, not a
proved FPGA fence, DMA lifetime or physical display recovery implementation.

## Whole-call timing and tracked allocation

The mean of per-frame paired medians is77.713822 ms for direct full-array V43 and
225.768906 ms for the integrated tile path on this host. The tile implementation
is slower in Python; it favors an explicit bounded data path over NumPy batching.
This is a distinct campaign from V43's proof-adapter comparison; its timing must
not be added to or substituted into that earlier result. It proves no physical
frame rate or faster native implementation.

`memory_probe.py` runs16 fresh-process points: key0/P1 in four clips ×two receive
implementations. Tracemalloc starts after imports, packet I/O and any prior
reference bootstrap. Direct traced peak call increments span10,408,319–30,120,239
bytes; tile peaks span2,799,321–2,852,932 bytes. These are instrumented Python
allocation increments, not whole-process RSS, every native allocation, total
retained memory or target hardware allocation. Both retain external-model output
and HUD; existing P-frame reference allocation is outside tracing. No speed claim
uses this instrumented probe. Raw records and source pins remain available.

The architecture result is removal of full coefficient/prediction staging with
exact software atomic publication. Next hardware work needs packet/reservoir
banking, transform scheduling, external-memory arbitration, tags/HUD/color, clock
crossings and physical scanout measurements. No RTL or firmware is changed.

```sh
python -m unittest -v test_receiver
python -m unittest -v test_verify
python benchmark.py
python verify.py
python memory_probe.py
```
