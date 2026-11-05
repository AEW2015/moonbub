"""Check register traffic and overlap policy against the frozen baseline.

This verifies source compatibility, not FPGA timing or hardware behavior.
"""
from pathlib import Path
import re

workspace=Path(__file__).resolve().parents[4]
old=workspace/'firmware/evidence/build-overlap-v5-frozen/source/handheld/src'
new=workspace/'firmware/experiments/overlap/handheld/src'
for rel in ('streaming/mod.rs','streaming/protocol.rs','streaming/rx_queue.rs'):
    assert (old/rel).read_bytes()==(new/rel).read_bytes(), rel

original=(old/'streaming/overlap.rs').read_text()
updated=(new/'streaming/overlap.rs').read_text()
start='#[derive(Clone, Copy, Debug, PartialEq, Eq)]\npub enum Mode'
end='#[cfg(test)]'
assert original[original.index(start):original.index(end)]==updated[updated.index(start):updated.index(end)], 'overlap policy changed'

a=(old/'usb_test.rs').read_text();b=(new/'usb_test.rs').read_text()
for op in ('read_u32','write_u32'):
    pattern=rf'd\.fpga\.{op}\(base \+ (0x[0-9a-f]+|\d+)'
    assert re.findall(pattern,a)==re.findall(pattern,b), op
print('PASS: streaming engine/protocol/queue and overlap policy identical; USB FPGA register read/write sequences identical')
