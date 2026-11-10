#!/usr/bin/env python3
"""Prepare only: pin real QSPI-to-JPEG boundary and its immutable fixture."""
import hashlib,json,pathlib,sys,zlib
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3]
A=R/'experiments/python-gamebub-v124/jpeg-wire';OLD_A=R/'experiments/python-gamebub-v115/jpeg-wire';S=R/'fpga/experiments/cu66-v115-jpeg-wire'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 sys.path.insert(0,str(R/'host'))
 from moonshine.protocol import parse_packet,Reassembler
 endpoint_index=R/'experiments/python-gamebub-v124/endpoint/results.json';selected=json.loads(endpoint_index.read_text());assert selected['status']=='PASS_NATIVE_PACKETIZER_TO_RUST_RECEIVER'
 selected_receipt=R/selected['selected_receipt']['path'];endpoint_result=R/selected['result']['path'];assert sha(selected_receipt)==selected['selected_receipt']['sha256'] and sha(endpoint_result)==selected['result']['sha256']
 er=json.loads(selected_receipt.read_text());endpoint_attempt=R/selected['selected_attempt'];assert all(sha(endpoint_attempt/rel)==meta['sha256'] for rel,meta in er['source_snapshots'].items());native_packet=R/selected['selected_attempt']/'out/native-1024.bin';rust_recovered=R/selected['selected_attempt']/'out/case-native_golden_1024.jpg';jpeg=R/'host/fixtures/pattern-720x480-420-q65.jpg';fixture=native_packet;wire=fixture.read_bytes();jpeg_bytes=jpeg.read_bytes();native_sha=sha(fixture);result_data=json.loads(endpoint_result.read_text())
 assert er['status']=='PASS' and native_sha==result_data['native_packet_outputs']['1024']['sha256']==selected['packetization_sizes']['1024']['sha256']
 assert sha(rust_recovered)==result_data['cases'][0]['recovered_sha256'] and rust_recovered.read_bytes()==jpeg_bytes
 assert result_data['golden_1024']['byte_exact'] and native_sha==result_data['golden_1024']['sha256']
 pos=0;parts=[];chunks=[];receiver=Reassembler();completed=None
 while pos<len(wire):
  n=int.from_bytes(wire[pos:pos+2],'big');pos+=2;packet=wire[pos:pos+n];pos+=n;h=parse_packet(packet);parts.append(h.payload);chunks.append(dict(id=h.frame_id,offset=h.offset,bytes=len(h.payload)));value=receiver.accept(packet)
  if value is not None:completed=value
 assert pos==len(wire) and b''.join(parts)==jpeg_bytes and completed is not None and completed[1]==jpeg_bytes==rust_recovered.read_bytes() and len(chunks)==26 and len(jpeg_bytes)==26159
 assert completed is not None
 reference=R/'host/evidence/pattern-c-model-fixed-color.ppm';header=b'P6\n720 480\n255\n';rgb=reference.read_bytes();assert rgb.startswith(header);rgb=rgb[len(header):];assert len(rgb)==720*480*3
 golden=bytearray()
 for at in range(0,len(rgb),3):
  red,green,blue=rgb[at:at+3];v=((red>>3)<<11)|((green>>2)<<5)|(blue>>3);golden+=v.to_bytes(2,'little')
 assert (OLD_A/'golden-rgb565.bin').read_bytes()==bytes(golden),'frozen V115 RGB565 golden changed'
 A.mkdir(parents=True,exist_ok=True)
 sources=[S/'jpeg_wire.sv',R/'fpga/rtl/moonshine_qspi_endpoint.sv',R/'fpga/rtl/moonshine_bus_cdc.sv',R/'fpga/rtl/moonshine_core.sv',R/'fpga/experiments/throughput30/burst/jpeg_input_guarded.v']
 sources+=sorted(p for p in (R/'fpga/vendor/core_jpeg/src_v').glob('*.v')if p.name!='jpeg_input.v')
 other=[S/'tb_jpeg_wire.cpp',fixture,jpeg,reference,OLD_A/'golden-rgb565.bin',R/'host/moonshine/protocol.py',R/'firmware/handheld/src/streaming/protocol.rs',R/'firmware/handheld/src/streaming/mod.rs',pathlib.Path(__file__),pathlib.Path(__file__).parent/'qualify.py',R/'scripts/cu66-v114/optimized_spatial.py',endpoint_index,selected_receipt,endpoint_result,rust_recovered,endpoint_attempt/'src/packetizer_probe.cpp',endpoint_attempt/'src/receiver_probe.rs',endpoint_attempt/'src/run.py',endpoint_attempt/'source/sunshine/msv1.cpp',endpoint_attempt/'source/sunshine/msv1.h',endpoint_attempt/'source/moonbub/protocol.rs']
 waiver=json.loads((S/'baseline-lint-review.json').read_text())
 assert sha(S/'baseline-lint.vlt')==waiver['vlt_sha256'] and waiver['assertion_waivers']==waiver['blanket_warning_waivers']==0
 for item in waiver['entries']:
  original=R/item['path'];assert sha(original)==item['source_sha256'];assert original.read_text().splitlines()[item['line']-1]==item['line_text']
 root_review=OLD_A/'root-lint-review-message.json'
 review=json.loads(root_review.read_text());assert review['status']=='REVIEWED_SCOPED_DIGITAL_BASELINE_LINT' and review['proposal']['sha256']==sha(S/'baseline-lint-review.json') and review['vlt_sha256']==waiver['vlt_sha256']
 other += [OLD_A/'root-lint-review.json',root_review,S/'baseline-lint.vlt',S/'baseline-lint-review.json',OLD_A/'compile-diagnostics.json',R/waiver['failed_raw_report']]
 sources_map={str(p.relative_to(R)):sha(p)for p in sources+other}
 c=dict(schema='v124-native-msv1-to-real-qspi-jpeg-preparation-v1',status='PREPARED_NOT_RUN',baseline_lint=dict(path='fpga/experiments/cu66-v115-jpeg-wire/baseline-lint.vlt',sha256=waiver['vlt_sha256'],rules=waiver['exact_rules'],diagnostics=waiver['inherited_diagnostics'],root_review_path=str(root_review.relative_to(R)),root_review_sha256=sha(root_review),scope='Exact frozen source+line only; Root-reviewed digital baseline lint, not assertion or physical CDC waiver'),rtl_source_order=[str(p.relative_to(R))for p in sources],source_sha256=sources_map,fixture=dict(packets=26,jpeg_bytes=len(jpeg_bytes),crc32=zlib.crc32(jpeg_bytes),packet_sha256=native_sha,packet_trace=chunks),native_endpoint=dict(selected_pointer=str(endpoint_index.relative_to(R)),selected_pointer_sha256=sha(endpoint_index),receipt=str(selected_receipt.relative_to(R)),receipt_sha256=sha(selected_receipt),result=str(endpoint_result.relative_to(R)),result_sha256=sha(endpoint_result),native_packet_file=str(fixture.relative_to(R)),native_packet_sha256=native_sha,rust_recovered_jpeg=str(rust_recovered.relative_to(R)),rust_recovered_sha256=sha(rust_recovered),native_golden_byte_exact=True,rust_and_python_recovered_jpeg_byte_exact=True),oracle='Frozen upstream C-model PPM converted without Pillow to little-endian RGB565 and original V115 golden; related upstream JPEG mathematics, not an independent decoder oracle. Production Python MSV1 parser/reassembler consumes the actual native C++ packet file as an additional parser oracle, never as producer.',firmware_scope='Input packets are output bytes from Sunshine native packetizer archived in the selected host endpoint attempt. Existing C++ pin-driver adapter mirrors begin/forward/commit MMIO into actual streaming/mod.rs. No Rust firmware session, ESP32 CPU, capture, encode, send, Wi-Fi, or timing claim.',guarded_JPEG_scope='Actual vendor JPEG modules except existing isolated SOF research jpeg_input_guarded.v substitution. Not unmodified production input, CS88 decoder, or V124 spatial codec timing composition.',sink_scope='Finite one-frame address/seen model and immutable V115 RGB565 golden; accepted pixel value/owner/held tuple checks; explicit modeled drain and frame-boundary publication fence. No SDRAM/LCD physical model in this wrapper.')
 (A/'preparation.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n');return c,sources
if __name__=='__main__':
 c,_=prepare();print(c['status'],len(c['rtl_source_order']),'actual RTL modules; no simulation launched')
