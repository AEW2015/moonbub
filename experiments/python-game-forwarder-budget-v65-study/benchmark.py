"""Pin actual source constraints; enumerate optimistic transport budget misses."""
import json,re
import helpers as h
import model as m

def evidence():
    protocol=h.RUST_PROTOCOL.read_text();stream=h.RUST_STREAMING.read_text();driver=h.RUST_FPGA.read_text();device=h.RUST_DEVICE.read_text();host=h.HOST_PROTOCOL.read_text();rtl=h.FPGA_CORE.read_text()
    assert re.search(r'pub const HEADER: usize = 40;',protocol)and re.search(r'pub const CHUNK: usize = 1024;',protocol)
    assert 'pub const MAX_FRAME: u32 = 256 * 1024;'in protocol
    assert 'DmaBuffer::new(protocol::HEADER + protocol::CHUNK + 1)?'in stream and 'DmaBuffer::new(16 * 1024)?'in stream
    assert '.name("Streaming".into())'in stream and '.stack_size(16 * 1024)'in stream
    assert 'session(host, generation)'in stream and stream.index('ensure_core()?;')<stream.index('session(host, generation)')
    assert 'MALLOC_CAP_DMA | esp_idf_svc::sys::MALLOC_CAP_INTERNAL'in stream
    assert 'forward(&bytes[protocol::HEADER..])?'in stream and 'Some(Hertz(40_000_000))'in stream
    assert 'Operation::Write(&[command])'in driver and 'Operation::WriteWithWidth(&address, width)'in driver and 'Operation::WriteWithWidth(&data, width)'in driver
    assert 'let width = LineWidth::Quad;'in driver and '*clock <= max_clock'in driver
    assert 'MAX_SPI_READ_CLOCK: Hertz = Hertz(16_000_000)'in driver
    assert 'let spi_rates = [40.MHz(), 20.MHz(), 16.MHz(), 10.MHz()]'in device
    assert 'packet[5] != 1'in protocol and '"FPGA JPEG unsupported"'in stream and 'jpeg_core #(.SUPPORT_WRITABLE_DHT(0))'in rtl
    assert 'payload_size: int = MAX_PAYLOAD'in host and 'MAX_PAYLOAD = 1024'in host
    return dict(current_transport='MSV1/version1/codec1 restricted JPEG ONLY',current_FPGA_backend='jpeg_core; CS38 backend absent',
        current_CS38_deployable=False,CS38_requires='Explicit codec negotiation/version/backend plus supported FPGA decoder/credit/reference recovery path; byte budget alone cannot add these.',
        header_bytes=40,fragment_payload_limit=1024,protocol_MAX_FRAME_bytes=262144,
        runtime_internal_DMA_buffer_bytes=1065,runtime_DMA_formula='HEADER+CHUNK+1',extra_runtime_byte='Reject oversize/truncated datagram length beyond allowed1064B.',
        boot_programming_DMA_scratch_bytes=16384,boot_scratch_scope='ensure_core programming block before session buffer exists; not added as simultaneous runtime DMA.',
        streaming_thread_stack_declared_bytes=16384,stack_scope='Separate persistent task stack declaration, not measured maximum stack use or DMA buffer.',
        memory_scope='Not total ESP32 SRAM: Wi-Fi/lwIP/socket queues, SDK/SPI descriptors or bounce buffers, other tasks/heap and actual state layout remain unmeasured.',
        QSPI_payload_command_single_bits=8,QSPI_address_quad_bits=32,QSPI_data_lanes=4,
        QSPI_transaction_phase_clocks='8 command+32/4 address+8*payload/4 data=16+2*payload',
        forward_requested_max_clock_hz=40000000,declared_driver_rates_hz=[40000000,20000000,16000000,10000000],
        read_requested_max_clock_hz=16000000,clock_scope='Driver chooses first declared rate<=requested maximum; actual pin clock/divider/stalls not measured.',
        nominal_clean_success_MMIO=dict(reads_per_fragment=3,begin_reads_per_frame=4,begin_writes_per_frame=5,commit_reads_per_frame=2,commit_writes_per_frame=1,
            scope='Identity(two reads)+credit read per forward; clean ready begin and commit only. These phase/SDK costs remain in the unknown allowance, not subtracted twice.'),
        blocking_task='recv_from→parse/bitwiseCRC→begin-if-SOF→Device::try_lock/identity+credit→blocking spi_write→stats→commit/reply-if-EOF→yield_now; lock busy or credit failure drops/aborts.',
        fragmentation_scope='Canonical host default full1024B payloads except tail; receiver also accepts smaller sequential fragments, which increase overhead.',
        source_crc_scope='8 source-level bit rounds per payload byte, not compiled instructions/cycles.',
        protocol_scope='Sequential/no reordering queue; valid in-order successful frames assumed. Failure recovery, socket wait and contention/drop rates unmeasured.')

def aggregate(rows):
    fields=('payload_bytes','fragments','L3_IPv4_UDP_bytes','nominal_L3_bits_per_second_at30','total_QSPI_clocks')
    return dict(frames=len(rows),**{name:dict(total=sum(r[name]for r in rows),mean=sum(r[name]for r in rows)/len(rows),maximum=max(r[name]for r in rows),minimum=min(r[name]for r in rows))for name in fields},
        minimum_optimistic_combined_us_per_fragment_at40MHz=min(r['optimistic_combined_us_per_fragment_at40MHz']['value']for r in rows),
        maximum_QSPI_phase_lower_bound_us_at40MHz=max(r['QSPI_lower_bound_us'][0]['time']['value']for r in rows))

def main():
    before=h.pins();audit=evidence();cases=[];flat=[]
    for source_case in h.packets():
        rows=[]
        for src in source_case['rows']:
            b=src['payload_bytes'];base=m.frame(b);row=dict(src,**{k:v for k,v in base.items()if k!='payload_bytes'})
            row['header_scenarios']=[dict(kind='current_wire'if header==40 else'hypothetical_unimplemented_all_codecs',**m.frame(b,header=header))for header in(40,16,8)]
            row['QSPI_lower_bound_us']=[dict(assumed_clock_hz=clock,time=m.fraction(m.qspi_us(b,clock)))for clock in m.CLOCKS]
            row['optimistic_combined_us_per_fragment_at40MHz']=m.fraction(m.residual(b)[1])
            row['residual_thresholds']=[dict(assumed_clock_hz=clock,assumed_other_stage_reserve_us=reserve,
                frame_remainder_us=m.fraction(m.residual(b,clock,reserve)[0]),maximum_amortized_combined_us_per_fragment=m.fraction(m.residual(b,clock,reserve)[1]))for clock in m.CLOCKS for reserve in m.RESERVES_US]
            rows.append(row);flat.append(dict(scene=source_case['scene'],**row))
        cases.append(dict(scene=source_case['scene'],rows=rows,summary=aggregate(rows)))
    assert len(flat)==457
    sweeps=[]
    for clock in m.CLOCKS:
        for reserve in m.RESERVES_US:
            for unknown in m.UNKNOWN_US:
                misses=[];elapsed=[];margins=[]
                for row in flat:
                    used,margin,passes=m.scenario(row['payload_bytes'],clock,unknown,reserve);elapsed.append(used);margins.append(margin)
                    if not passes:misses.append(dict(scene=row['scene'],id=row['id'],payload_bytes=row['payload_bytes'],fragments=row['fragments'],modeled_serial_us=m.fraction(used),deadline_margin_us=m.fraction(margin)))
                sweeps.append(dict(assumed_QSPI_clock_hz=clock,assumed_other_stage_reserve_us=reserve,assumed_combined_unknown_us_per_fragment=unknown,
                    frames=457,passing_frames=457-len(misses),missed_frames=len(misses),misses=misses,
                    maximum_modeled_serial_us=m.fraction(max(elapsed)),minimum_deadline_margin_us=m.fraction(min(margins)),
                    interpretation='Optimistic successful-forwarding inequality only; CPU/lock/MMIO/jitter/reserves are assumed, not measurements.'))
    assert h.pins()==before
    output=dict(schema='gamebub-forwarder-budget-v65',source_sha256=before,audit=audit,cases=cases,summary=aggregate(flat),sweeps=sweeps,
        assumptions=dict(fps=30,frame_period_us=m.fraction(m.PERIOD_US),fragmentation='full1024excepttail',IPv4_UDP_minimum_header_bytes=28,
            QSPI_clocks_hz=list(m.CLOCKS),combined_unknown_us_per_fragment=list(m.UNKNOWN_US),other_stage_reserve_us=list(m.RESERVES_US),
            default_reserve_scope='0 is only maximum residual envelope; other FPGA/decode/display/host stages are NOT measured or free.5/10ms are explicit hypothetical reserves.',
            RF_scope='L3IPv4UDPdata bytes only; no802.11/MAC/PHY/ACK/retries/FEC/security overhead, link contention, input/audio/feedback traffic or RFgoodput measurement.',
            feedback_scope='Current32Bfeedback+28BIPv4UDP per successful frame is an additional reverse-path minimum14400bit/s at30, plus heartbeat/input/error messages; excluded from data-only figures.',
            pipeline_scope='Blocking app task can coexist with OS network ingress; no measured scheduling/queue/drop/decode/presentation model. FPGA/currentJPEG decode+publication must get real measured budget.'),
        protocol_MAX_boundary=dict(frame=m.frame(m.MAX_FRAME),QSPI40MHz_us=m.fraction(m.qspi_us(m.MAX_FRAME,40000000)),optimistic_combined_us_per_fragment=m.fraction(m.residual(m.MAX_FRAME)[1])),
        current_firmware_accepts_CS38=False,firmware_modified=False,ESP32_ISA_or_RF_execution_simulated=False,physical_30fps_proven=False,
        scope=['457 actual retainedCS38 complete bytecounts are carried hypothetically through currentMSV1-sized fragments; currentfirmware/FPGA remainJPEG-only and cannotrunthiscodec.',
            'HEADER40 appliesonlynetwork; firmware stripsit beforeQSPI. Hypothetical16/8Bheaders changeL3costonly here and benefitALLcodecs; noimplementedlayout/negotiation/CPUgain claimed.',
            'All arithmetic is exact rational where time is fractional. Every assumed-overhead deadline miss is retained, including negative margins.',
            'Residualbudget is maxAMORTIZED combinedunmodeled successful-frame time perfragment afterQSPIphaselowerbound/reserve; not per-callmeasuredCPU, sustainedRF, memoryfit, or end-to-endFPS proof.'])
    (h.HERE/'results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output['summary']),flush=True)
    for s in sweeps:
        if s['assumed_QSPI_clock_hz']==40000000:print(json.dumps({k:v for k,v in s.items()if k not in('misses','interpretation')}),flush=True)
if __name__=='__main__':main()
