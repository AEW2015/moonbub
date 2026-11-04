"""Verify collected direct-LUT evidence offline; never opens hardware/Vivado."""
from pathlib import Path
import json
import re

p = Path(__file__).resolve().parent
s = (p / "overlay-enable.txt").read_text()
blocks = {}
pattern = r"^LUT (\S+) REF=LUT(\d) INIT=(\d+)'h([0-9a-fA-F]+)\n((?: INPUT=.*\n)+)"
for m in re.finditer(pattern, s, re.M):
    name, n, width, truth, inputs = m.groups()
    drivers = {
        int(im[2]): im[3]
        for im in re.finditer(r"^ INPUT=(\S+)/I(\d+) DRIVER=(\S+) NETS=.*$", inputs, re.M)
    }
    blocks[name] = (int(n), int(width), int(truth, 16), drivers)

pins = set()
for m in re.finditer(r"^ENABLE_RESET_ONLY (\S+) value=(-?\d+) DRIVER=(\S+)/O$", s, re.M):
    pin, recursive_result, driver = m.groups()
    n, width, truth, inputs = blocks[driver]
    assert n == 4 and width == 16 and set(inputs) == {0, 1, 2, 3}
    assert inputs[0] == "rstpixel_reg[3]/Q"
    assert all(((truth >> assignment) & 1) == 0 for assignment in range(16) if assignment & 1)
    assert pin not in pins
    pins.add(pin)
assert len(pins) == 44
assert "RESET=rstpixel_reg[3]/Q REF=FDPE INIT=1'b1" in s
assert "KNOWN_BAD_HIGH_ROM_RESET_EN=1" in s

reference = p / "bram-coverage-reference"
lines = (reference / "parent-all-BRAM-cells.txt").read_text().splitlines()
split = next(i for i, line in enumerate(lines) if line.startswith("RAMB18E1 count="))
cells = set(lines[1:split])
assert lines[0] == "RAMB36E1 count=106"
assert lines[split] == "RAMB18E1 count=0" and len(cells) == 106
summary = json.loads((reference / "reqp1839-summary.json").read_text())
assert len(summary["warnings"]) == 199
assert cells == {row["cell"] for row in summary["warnings"]}
print("PASS:44 direct LUT reset-low proofs;106-cell exact BRAM/warning equality; no hardware action")
