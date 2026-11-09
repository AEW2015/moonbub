#!/usr/bin/env python3
"""Prepare only: pin real QSPI-to-JPEG boundary and its immutable fixture."""
import hashlib,json,pathlib,sys,zlib
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3]
A=R/'experiments/python-gamebub-v115/jpeg-wire';S=R/'fpga/experiments/cu66-v115-jpeg-wire'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 sys.path.insert(0,str(R/'host'))
 from moonshine.protocol import parse_packet,Reassembler
 fixture=R/'host/fixtures/pattern-msv1-packets.bin';wire=fixture.read_bytes();jpeg=(R/'host/fixtures/pattern-720x480-420-q65.jpg').read_bytes();pos=0;parts=[];chunks=[];receiver=Reassembler();completed=None
 while pos<len(wire):
  n=int.from_bytes(wire[pos:pos+2],'big');pos+=2;packet=wire[pos:pos+n];pos+=n;h=parse_packet(packet);parts.append(h.payload);chunks.append(dict(id=h.frame_id,offset=h.offset,bytes=len(h.payload)));value=receiver.accept(packet)
  if value is not None:completed=value
 assert pos==len(wire) and b''.join(parts)==jpeg and len(chunks)==26 and len(jpeg)==26159
 assert completed is not None
 reference=R/'host/evidence/pattern-c-model-fixed-color.ppm';header=b'P6\n720 480\n255\n';rgb=reference.read_bytes();assert rgb.startswith(header);rgb=rgb[len(header):];assert len(rgb)==720*480*3
 golden=bytearray()
 for at in range(0,len(rgb),3):
  red,green,blue=rgb[at:at+3];v=((red>>3)<<11)|((green>>2)<<5)|(blue>>3);golden+=v.to_bytes(2,'little')
 A.mkdir(parents=True,exist_ok=True);(A/'golden-rgb565.bin').write_bytes(golden)
 sources=[S/'jpeg_wire.sv',R/'fpga/rtl/moonshine_qspi_endpoint.sv',R/'fpga/rtl/moonshine_bus_cdc.sv',R/'fpga/rtl/moonshine_core.sv',R/'fpga/experiments/throughput30/burst/jpeg_input_guarded.v']
 sources+=sorted(p for p in (R/'fpga/vendor/core_jpeg/src_v').glob('*.v')if p.name!='jpeg_input.v')
 other=[S/'tb_jpeg_wire.cpp',fixture,R/'host/fixtures/pattern-720x480-420-q65.jpg',reference,A/'golden-rgb565.bin',R/'host/moonshine/protocol.py',R/'firmware/handheld/src/streaming/protocol.rs',R/'firmware/handheld/src/streaming/mod.rs',pathlib.Path(__file__),pathlib.Path(__file__).parent/'qualify.py',R/'scripts/cu66-v114/optimized_spatial.py']
 sources_map={str(p.relative_to(R)):sha(p)for p in sources+other}
 c=dict(schema='v115-real-qspi-jpeg-preparation-v1',status='PREPARED_NOT_RUN',rtl_source_order=[str(p.relative_to(R))for p in sources],source_sha256=sources_map,fixture=dict(packets=26,jpeg_bytes=len(jpeg),crc32=zlib.crc32(jpeg),packet_trace=chunks),oracle='Existing fixed-color related upstream C-model PPM, converted without Pillow to little-endian RGB565; shares upstream JPEG mathematics and is not independent decoder validation.',firmware_scope='C++ pin-driver adapter mirrors begin/forward/commit MMIO from actual streaming/mod.rs. Production Python parser/reassembler checks fixture. No Rust/ESP32 CPU execution or timing claim.',guarded_JPEG_scope='Actual vendor JPEG modules except existing isolated SOF research jpeg_input_guarded.v substitution. Not unmodified production input, CS88 decoder, or V115 spatial codec timing composition.',sink_scope='Finite one-frame address/seen model and immutable golden; accepted pixel value/owner/held tuple checks; explicit modeled drain and frame-boundary publication fence. No SDRAM/LCD physical model in this wrapper.')
 (A/'preparation.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n');return c,sources
if __name__=='__main__':
 c,_=prepare();print(c['status'],len(c['rtl_source_order']),'actual RTL modules; no simulation launched')
