# v20 kit formats and interfaces

`golden-index.json` uses `gamebub-v20-inverse-golden-v1`. Every array descriptor
has a safe relative path, zlib storage, raw/stored SHA-256, shape and `<i4` dtype.
Decode the raw bytes as signed little-endian int32. Dataset order is block,
row, column. A real-source dataset also records the contiguous cohort/frame/
plane groups. Expected residuals retain full int32 values, including legal
extremes above int16 range. Work counts distinguish sparse GENERAL products,
constant DC products, nonzero coefficients/intermediates and classifications.
The input is already dequantized; no entropy or predictor state is implicit.

`results.json` uses `gamebub-v20-c11-acceptance-v1`. It records compiler/flags,
source pins, golden-index hash, exact output hashes/work totals and sanitizer
status. Replaying on another supported host can use another compiler; the
retained arithmetic outputs must match. Toolchain metadata is not target-cycle
or hardware-resource evidence. Generated libraries live only in temporary paths.

`wire-contract.json` uses `gamebub-v20-lab-wire-contract-v1`. The `layouts`
entries define byte order, field sizes and offsets against frozen Python struct
formats. AR03 has a variable body and final CRC; fixed envelope size is distinct
from contiguous header size. The complete epoch-1 example is encoded/decoded
through the real Python AR03 lifecycle. Control sequences reconstruct serialized
FG19 bytes from actual v19 controller histories, with their model times and
intentional delivery-loss flags. Their timing is a reference-model record, not a
radio capture. CRC/token identity and reference publication are separate checks.

`vectors/rtl-smoke/*.mem` contains six signed-edge blocks. `slice.json` gives the
source index hash, dataset, range, word width and order. Use `export_mem.py` for
more slices. This smoke set supplements the complete binary arrays; it is not
full RTL coverage. Advance only on valid AND ready, hold payload and metadata
while stalled, and retain exact block identity through both inverse passes.

IT20 is an **offline generated-tile fixture** defined by the inline study, not a
runtime codec or negotiated transport. Its tile records drive the tagger test
interface: plane, top-left x/y, cropped width/height and newly clipped uint8
samples. The actual runtime packet contract remains AR03/GF03 plus negotiated
control behavior. Each isolated AR03 fixture must use its declared pre-banks;
its P payload is not independently decodable from an arbitrary predictor.

No register address map, pin constraint, mapped RAM allocation, SHA/entropy RTL,
FPGA utilization or native endpoint implementation is implied by these formats.
Those are named implementation gates in ACCEPTANCE.md and TASKS.md.
