from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;root=Path('C:/mb70');d=root/'fpga/experiments/cu66-v71/rows-idle-capture-v026';d.mkdir()
old=root/'dy71-v025-20261107-v003/inputs/fpga/experiments/cu66-v71/rows/cu71_tile_rows.sv'
s=old.read_text();assert s.count('captured_tile<=0;')==1 and s.count('captured_tile<=tile_pixels;')==1
s=s.replace('captured_tile<=0;','').replace('captured_tile<=tile_pixels;','')
needle='    always_ff @(posedge clk)begin\n        if(rst)begin'
assert s.count(needle)==1
s=s.replace(needle,'''    // Speculatively capture while idle; payload is authoritative only while
    // write_busy is asserted. A true tile handshake sets write_busy on the same
    // edge that captures the accepted pixels. Abort/reset invalidate tokens,
    // never require resetting the 512-bit payload. No added handshake latency.
    always_ff @(posedge clk) if(!write_busy) captured_tile<=tile_pixels;
'''+needle)
(d/'cu71_tile_rows.sv').write_text(s)
(d/'cu71_tile_rows_reference.sv').write_text(old.read_text().replace('module cu71_tile_rows #(','module cu71_tile_rows_reference #('))
(d/'derivation.json').write_text(json.dumps(dict(parent=str(old),parent_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256((d/'cu71_tile_rows.sv').read_bytes()).hexdigest(),changes=['Remove payload reset only','Capture payload while !write_busy instead of full external ready/kill chain','No token/control/handshake/state/RAM changes'],hardware=False),indent=2)+'\n')
print(str(d))
