# Fine-key GM25 full-window quality cohorts

Three declared profiles run on all 48 frames of each retained v24 native scene:
zero prediction/lambda0, zero prediction/lambda1, and block32 prediction with
nonzero-vector penalty512/lambda1. Every frame uses ROI8/background16; keys0/24
explicitly use background16 and skip RDO. Motion stays bounded to even integer
vectors within±8. Epoch25 and frame IDs0..47 match the parent CP25 integration.

Every encoded GM25 packet is decoded, and only this reconstructed output becomes
the next acknowledged reference. Source/destination slots, reference IDs,
packet blobs, exact source IDs, tags, paid encoder/decode work, and bare/hybrid
RGB565 quality are retained. HUD source words are overlaid exactly for hybrid
quality; this folder does not serialize HU25/CP25 or make cap-admission claims.
`results.json` uses the parent native benchmark's case/row/summary layout and
packet descriptors relative to this directory's `objects` folder.

```sh
python benchmark.py > run.log
python verify.py > verify.log
python -m unittest -v test_replay.py > tests.log 2>&1
```

Verification replays all 288 retained packets, checks every decoded quantizer map
is ROI8/background16, validates key/reference/slot history and source pins, and
recomputes actual RGB565 hashes and quality. Source YUV and originals come only
from the frozen v24 fixture objects. These offline Python projections are not
native ESP32/FPGA, radio/QSPI throughput, mapped hardware or physical30fps proof.
