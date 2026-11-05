"""Read-only source evidence and exact retained CS38 byte-count provenance."""
from pathlib import Path
import hashlib,json,struct,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DATA=HERE.parent/'python-game-binary-qual-v40-study'
RUST_PROTOCOL=ROOT/'firmware/handheld/src/streaming/protocol.rs'
RUST_STREAMING=ROOT/'firmware/handheld/src/streaming/mod.rs'
RUST_FPGA=ROOT/'firmware/handheld/src/device/drivers/fpga/mod.rs'
RUST_DEVICE=ROOT/'firmware/handheld/src/device/mod.rs'
HOST_PROTOCOL=ROOT/'host/moonshine/protocol.py'
FPGA_CORE=ROOT/'fpga/rtl/moonshine_core.sv'
EVIDENCE=(RUST_PROTOCOL,RUST_STREAMING,RUST_FPGA,RUST_DEVICE,HOST_PROTOCOL,FPGA_CORE,ROOT/'host/PROTOCOL.md')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def raw(desc,folder=DATA):
    stored=(folder/desc['path']).read_bytes();assert digest(stored)==desc['stored_sha256']
    decoder=zlib.decompressobj();data=decoder.decompress(stored,desc['raw_bytes']+1)
    assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(data)==desc['raw_bytes']
    assert digest(data)==desc['raw_sha256'];return data

def packets():
    data=load(DATA/'results.json');result=[]
    for case in data['cases']:
        rows=[]
        for row in case['rows']:
            packet=raw(row['packet']);assert packet[:4]==b'CS38'and len(packet)==row['complete_bytes']
            assert struct.unpack_from('<I',packet,8)[0]==row['id']
            assert zlib.crc32(packet[:-4])==struct.unpack('<I',packet[-4:])[0]
            rows.append(dict(id=row['id'],payload_bytes=len(packet),source_packet=row['packet'],source_packet_sha256=digest(packet)))
        assert [r['id']for r in rows]==list(range(len(rows)));result.append(dict(scene=case['scene'],rows=rows))
    assert sum(len(c['rows'])for c in result)==457;return result

def pins():
    paths=set(EVIDENCE)|{DATA/'results.json'}|{HERE/name for name in('helpers.py','model.py','benchmark.py','test_model.py')}
    return {p.relative_to(ROOT).as_posix():sha(p)for p in sorted(paths)}
