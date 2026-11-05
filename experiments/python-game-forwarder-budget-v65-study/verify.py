#!/usr/bin/env python3
"""Independent exact-rational forwarding envelope and read-only source audit.

Not ESP32 instruction/RF execution, measured overhead, backend compatibility,
or proof of physical30fps. Current firmware and FPGA remain JPEG-only.
"""
from pathlib import Path
from fractions import Fraction
import hashlib,importlib.util,json,math,re,struct,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DATA=HERE.parent/'python-game-binary-qual-v40-study'
CLOCKS=(40_000_000,20_000_000,16_000_000,10_000_000);RESERVES=(0,5000,10000);UNKNOWNS=(25,100,500,1000);PERIOD=Fraction(1_000_000,30)
EVIDENCE=('firmware/handheld/src/streaming/protocol.rs','firmware/handheld/src/streaming/mod.rs','firmware/handheld/src/device/drivers/fpga/mod.rs','firmware/handheld/src/device/mod.rs','host/moonshine/protocol.py','fpga/rtl/moonshine_core.sv','host/PROTOCOL.md')
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
host=module('forward65_existing_host_protocol',ROOT/'host/moonshine/protocol.py')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def raw(desc,folder=DATA):
    data=(folder/desc['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==desc['stored_sha256']
    z=zlib.decompressobj();out=z.decompress(data,desc['raw_bytes']+1)
    assert z.eof and not z.unused_data and not z.unconsumed_tail and len(out)==desc['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==desc['raw_sha256'];return out

def parts(length,chunk=1024):
    if type(length)is not int or not 1<=length<=262144 or type(chunk)is not int or not 1<=chunk<=1024:raise ValueError('bounded payload/fragment sizes')
    return tuple(min(chunk,length-offset)for offset in range(0,length,chunk))
def frame(length,header=40,chunk=1024):
    if type(header)is not int or header<0:raise ValueError('illustrative nonnegative header size')
    p=parts(length,chunk);count=len(p);clocks=sum(8+8+2*n for n in p);l3=sum(n+header+20+8 for n in p)
    return dict(payload_bytes=length,fragment_payload_limit=chunk,fragments=count,tail_payload_bytes=p[-1],header_bytes=header,
        udp_payload_bytes=sum(n+header for n in p),ipv4_udp_header_bytes=28*count,L3_IPv4_UDP_bytes=l3,
        nominal_payload_bits_per_second_at30=length*240,nominal_L3_bits_per_second_at30=l3*240,
        source_level_crc_bit_rounds=length*8,payload_QSPI_clocks=2*length,command_address_QSPI_clocks=16*count,total_QSPI_clocks=clocks)
def qspi(length,clock):
    if type(clock)is not int or clock<1:raise ValueError('positive assumed pin clock')
    return Fraction(sum(8+8+2*p for p in parts(length))*1_000_000,clock)
def budget(length,clock,reserve,unknown=0):
    if any(type(v)is not int or v<0 for v in(reserve,unknown)):raise ValueError('nonnegative assumed work')
    elapsed=qspi(length,clock)+reserve+len(parts(length))*unknown;return elapsed,PERIOD-elapsed

def fraction(record,expected):
    assert type(record['numerator'])is type(record['denominator'])is int
    assert(record['numerator'],record['denominator'])==(expected.numerator,expected.denominator)
    assert type(record['value'])in(int,float)and math.isfinite(record['value'])and math.isclose(record['value'],float(expected),rel_tol=1e-14,abs_tol=1e-12)

def source_audit(audit):
    protocol=(ROOT/EVIDENCE[0]).read_text();stream=(ROOT/EVIDENCE[1]).read_text();driver=(ROOT/EVIDENCE[2]).read_text();device=(ROOT/EVIDENCE[3]).read_text();rtl=(ROOT/EVIDENCE[5]).read_text();spec=(ROOT/EVIDENCE[6]).read_text()
    def constant(name):return int(re.search(r'pub const '+name+r': usize = (\d+);',protocol).group(1))
    assert constant('HEADER')==host.VIDEO.size==40 and constant('CHUNK')==host.MAX_PAYLOAD==1024
    assert 'pub const MAX_FRAME: u32 = 256 * 1024;'in protocol and host.MAX_FRAME==262144
    assert 'packet[5] != 1'in protocol and 'h.flags & !3 != 0'in protocol # codec field gate, not payload magic validation
    assert 'for _ in 0..8'in protocol and '0xEDB88320u32'in protocol
    assert '"FPGA JPEG unsupported"'in stream and 'jpeg_core #(.SUPPORT_WRITABLE_DHT(0))'in rtl and '1 = restricted baseline JPEG'in spec
    assert 'DmaBuffer::new(protocol::HEADER + protocol::CHUNK + 1)?'in stream
    assert 'MALLOC_CAP_DMA | esp_idf_svc::sys::MALLOC_CAP_INTERNAL'in stream
    start=stream.index('fn ensure_core()');stop=stream.index('\nfn abort()',start);boot=stream[start:stop]
    assert 'DmaBuffer::new(16 * 1024)?'in boot and 'program(&mut file, scratch.bytes())'in boot
    assert stream.index('ensure_core()?;')<stream.index('session(host, generation)')
    assert '.name("Streaming".into())'in stream and '.stack_size(16 * 1024)'in stream
    assert 'forward(&bytes[protocol::HEADER..])?'in stream and 'Some(Hertz(40_000_000))'in stream
    assert 'let width = LineWidth::Quad;'in driver
    assert 'Operation::Write(&[command])'in driver and 'Operation::WriteWithWidth(&address, width)'in driver and 'Operation::WriteWithWidth(&data, width)'in driver
    assert 'let address = address.to_be_bytes();'in driver and '*clock <= max_clock'in driver
    assert 'MAX_SPI_READ_CLOCK: Hertz = Hertz(16_000_000)'in driver
    assert 'let spi_rates = [40.MHz(), 20.MHz(), 16.MHz(), 10.MHz()]'in device
    # Count the clean-success MMIO path; recovery reads are extra unmodeled work.
    ident=stream[stream.index('fn identity('):stream.index('fn ensure_core()')]
    begin=stream[stream.index('fn begin('):stream.index('fn forward(')]
    forward=stream[stream.index('fn forward('):stream.index('struct DmaBuffer')]
    assert ident.count('read_u32(')==2 and forward.count('read_u32(')==1 and 'identity(d)?;'in forward
    assert begin[:begin.index('if core_status')].count('read_u32(')==4 and begin.count('write_u32(')==6 # one extra abort write in failure branch
    assert 'd.fpga.write_u32(BASE + 0x24, 4)?;'in stream and 'std::thread::yield_now();'in stream
    expected=dict(current_CS38_deployable=False,header_bytes=40,fragment_payload_limit=1024,protocol_MAX_FRAME_bytes=262144,
        runtime_internal_DMA_buffer_bytes=1065,boot_programming_DMA_scratch_bytes=16384,streaming_thread_stack_declared_bytes=16384,
        QSPI_payload_command_single_bits=8,QSPI_address_quad_bits=32,QSPI_data_lanes=4,forward_requested_max_clock_hz=40000000,
        declared_driver_rates_hz=list(CLOCKS),read_requested_max_clock_hz=16000000)
    for key,value in expected.items():assert audit[key]==value,key
    mmio=audit['nominal_clean_success_MMIO'];assert(mmio['reads_per_fragment'],mmio['begin_reads_per_frame'],mmio['begin_writes_per_frame'],mmio['commit_reads_per_frame'],mmio['commit_writes_per_frame'])==(3,4,5,2,1)
    assert 'not added as simultaneous runtime DMA'in audit['boot_scratch_scope']and 'not measured maximum stack use'in audit['stack_scope']and 'Not total ESP32 SRAM'in audit['memory_scope']
    assert '8 source-level bit rounds'in audit['source_crc_scope']and 'not compiled instructions/cycles'in audit['source_crc_scope']

def aggregate(rows):
    result=dict(frames=len(rows))
    for name in('payload_bytes','fragments','L3_IPv4_UDP_bytes','nominal_L3_bits_per_second_at30','total_QSPI_clocks'):
        values=[r[name]for r in rows];result[name]=dict(total=sum(values),mean=sum(values)/len(values),maximum=max(values),minimum=min(values))
    result['minimum_optimistic_combined_us_per_fragment_at40MHz']=min(float((PERIOD-qspi(r['payload_bytes'],40_000_000))/r['fragments'])for r in rows)
    result['maximum_QSPI_phase_lower_bound_us_at40MHz']=max(float(qspi(r['payload_bytes'],40_000_000))for r in rows)
    return result

def main():
    data=json.loads((HERE/'results.json').read_text());source=json.loads((DATA/'results.json').read_text());assert data['schema']=='gamebub-forwarder-budget-v65'
    for path,want in data['source_sha256'].items():assert sha(ROOT/path)==want,path
    assert all(p in data['source_sha256']for p in EVIDENCE)
    source_audit(data['audit']);assert data['current_firmware_accepts_CS38']is data['firmware_modified']is data['ESP32_ISA_or_RF_execution_simulated']is data['physical_30fps_proven']is False
    assumptions=data['assumptions'];assert assumptions['fps']==30 and assumptions['IPv4_UDP_minimum_header_bytes']==28
    fraction(assumptions['frame_period_us'],PERIOD);assert assumptions['QSPI_clocks_hz']==list(CLOCKS)and assumptions['combined_unknown_us_per_fragment']==list(UNKNOWNS)and assumptions['other_stage_reserve_us']==list(RESERVES)
    assert len(data['cases'])==len(source['cases'])==4;flat=[];wire_fragments=0
    for case,old in zip(data['cases'],source['cases'],strict=True):
        assert case['scene']==old['scene']and len(case['rows'])==len(old['rows'])
        for row,prior in zip(case['rows'],old['rows'],strict=True):
            packet=raw(prior['packet']);length=len(packet);fid=prior['id']
            assert packet[:4]==b'CS38'and struct.unpack_from('<I',packet,8)[0]==fid and zlib.crc32(packet[:-4])==struct.unpack('<I',packet[-4:])[0]
            assert row['id']==fid and row['source_packet']==prior['packet']and row['payload_bytes']==length==prior['complete_bytes']
            assert row['source_packet_sha256']==hashlib.sha256(packet).hexdigest()
            expected=frame(length)
            for key,value in expected.items():assert row[key]==value,key
            wires=list(host.packets(packet,fid,0));assert len(wires)==row['fragments']
            assert sum(len(w)+28 for w in wires)==row['L3_IPv4_UDP_bytes']
            for index,wire in enumerate(wires):
                parsed=host.parse_packet(wire);assert parsed.frame_id==fid and parsed.offset==index*1024 and parsed.frame_len==length
                assert parsed.payload==packet[index*1024:(index+1)*1024]
            wire_fragments+=len(wires)
            assert len(row['header_scenarios'])==3
            for entry,header in zip(row['header_scenarios'],(40,16,8),strict=True):
                assert {k:v for k,v in entry.items()if k!='kind'}==frame(length,header)
                assert entry['kind']==('current_wire'if header==40 else'hypothetical_unimplemented_all_codecs')
            for entry,clock in zip(row['QSPI_lower_bound_us'],CLOCKS,strict=True):assert entry['assumed_clock_hz']==clock;fraction(entry['time'],qspi(length,clock))
            fraction(row['optimistic_combined_us_per_fragment_at40MHz'],(PERIOD-qspi(length,40_000_000))/row['fragments'])
            assert len(row['residual_thresholds'])==12
            for entry,(clock,reserve)in zip(row['residual_thresholds'],((c,r)for c in CLOCKS for r in RESERVES),strict=True):
                assert(entry['assumed_clock_hz'],entry['assumed_other_stage_reserve_us'])==(clock,reserve)
                left=PERIOD-qspi(length,clock)-reserve;fraction(entry['frame_remainder_us'],left);fraction(entry['maximum_amortized_combined_us_per_fragment'],left/row['fragments'])
            flat.append(dict(scene=case['scene'],**row))
        assert case['summary']==aggregate(case['rows'])
    assert len(flat)==457 and data['summary']==aggregate(flat)
    assert len(data['sweeps'])==48;misses=0
    for entry,(clock,reserve,unknown)in zip(data['sweeps'],((c,r,u)for c in CLOCKS for r in RESERVES for u in UNKNOWNS),strict=True):
        assert(entry['assumed_QSPI_clock_hz'],entry['assumed_other_stage_reserve_us'],entry['assumed_combined_unknown_us_per_fragment'])==(clock,reserve,unknown)
        expected=[];elapsed=[];margins=[]
        for row in flat:
            used,margin=budget(row['payload_bytes'],clock,reserve,unknown);elapsed.append(used);margins.append(margin)
            if margin<0:expected.append((row,used,margin))
        assert entry['frames']==457 and entry['missed_frames']==len(expected)and entry['passing_frames']==457-len(expected)
        assert len(entry['misses'])==len(expected)
        for recorded,(row,used,margin)in zip(entry['misses'],expected,strict=True):
            assert(recorded['scene'],recorded['id'],recorded['payload_bytes'],recorded['fragments'])==(row['scene'],row['id'],row['payload_bytes'],row['fragments'])
            fraction(recorded['modeled_serial_us'],used);fraction(recorded['deadline_margin_us'],margin);assert margin<0
        fraction(entry['maximum_modeled_serial_us'],max(elapsed));fraction(entry['minimum_deadline_margin_us'],min(margins));misses+=len(expected)
    boundary=data['protocol_MAX_boundary'];assert boundary['frame']==frame(262144);fraction(boundary['QSPI40MHz_us'],qspi(262144,40_000_000));fraction(boundary['optimistic_combined_us_per_fragment'],(PERIOD-qspi(262144,40_000_000))/256)
    print(json.dumps(dict(actual_payloads=457,actual_canonical_host_fragments=wire_fragments,exact_header_scenarios=457*3,exact_residual_thresholds=457*12,
        assumed_work_sweeps=48,every_miss_ID_and_negative_margin_checked=True,total_recorded_sweep_misses=misses,source_pins=len(data['source_sha256']),
        source_backend_JPEG_only=True,CS38_deployable=False,runtime_DMA_requested_bytes=1065,boot_scratch_and_stack_scopes_separate=True,
        QSPI_phase_lower_bound_not_measured_service=True,ESP32_CPU_RF_or_physical_FPS_simulated=False)))
if __name__=='__main__':main()
