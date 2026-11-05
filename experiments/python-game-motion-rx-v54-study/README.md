# V54 actual motion through the tiled CS38 receiver

This extends V48's mostly zero-motion retained campaign with198 actual receives:
96 fixed-grid V47 frames,96 selected mixed-motion V53 frames, and six directed
fractional-motion fixtures. The nine histories retain their actual reference
trajectories. All198 tiled V48 outputs match direct V43 in coefficients, vectors,
canonical references, HUD and displayed pixels. Independent replay passes.

There are148 frames with nonzero vectors,10,650 nonzero vector instances and
1,725 fractional luma/chroma vector instances each. The directed fixture uses
negative/positive fractional motion and edge clamping. It recodes the six frozen
CS37 motion-probe packets into forced full/compact AB38 representations because
V48 explicitly supports arithmetic dispatch5/6 only. All36 actual alternatives
are retained and independently decoded; coefficients, maps, HUD and output tags
match old CS37. The largest directed complete packet is18,261 bytes.

The qualification inherits the eight V48 implementation tests; dataset extension
is not counted as new unit tests. Each actual motion packet receives three
alternating whole-call timing pairs. The mean of per-frame paired medians is
72.776ms for direct arrays and227.405ms for tiled receive on this host. This is
another correctness/architecture campaign, not a Python speedup or FPGA timing
measurement. Constructors/forks, comparisons and I/O are outside both clocks.

Frozen V48 code remains unchanged. Per-tile source addressing, real sparse
mixed maps, partial right-edge32 macroblocks and directed fractional coordinates
are now exercised at complete frame/reference level. Full reference/output planes
remain external-memory models. No target memory controller, address-port timing,
RTL, ESP32, physical display or30fps proof is provided.

```sh
python fractional.py    # regenerate directed coefficient-exact fixtures
python benchmark.py
python verify.py
```
