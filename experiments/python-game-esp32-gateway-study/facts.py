"""Extract build/source facts separately from unmeasured service assumptions."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PATHS=['firmware/README.md','firmware/handheld/src/streaming/mod.rs','firmware/handheld/src/streaming/protocol.rs',
       'firmware/handheld/src/device/drivers/fpga/mod.rs','firmware/handheld/sdkconfig.defaults',
       'firmware/evidence/compiled-sdkconfig.h','firmware/evidence/build-manifest.json']

def extract(root=ROOT):
    texts={p:(root/p).read_text() for p in PATHS};s=texts[PATHS[1]];p=texts[PATHS[2]];h=texts[PATHS[5]];d=texts[PATHS[3]]
    def macro(name):
        m=re.search(r'^#define '+re.escape(name)+r' (\d+)\s*$',h,re.M);assert m,name;return int(m[1])
    def const(name):
        m=re.search(r'pub const '+name+r': \w+ = (\d+);',p);assert m,name;return int(m[1])
    assert 'DmaBuffer::new(protocol::HEADER + protocol::CHUNK + 1)' in s
    assert 'Duration::from_millis(100)' in s and 'std::thread::sleep(Duration::from_millis(1))' in s
    assert '.stack_size(16 * 1024)' in s and 'Device::try_lock()' in s
    assert 'for _ in 0..8 {' in p and 'b"MSV1"' in p and 'packet[5] != 1' in p
    assert 'Some(Hertz(40_000_000))' in s and 'Hertz(16_000_000)' in d
    assert re.search(r'^#define CONFIG_SPIRAM(?:\s|_)',h,re.M) is None
    header,payload=const('HEADER'),const('CHUNK')
    manifest=json.loads(texts[PATHS[6]])
    return dict(cpu_hz=macro('CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ')*1_000_000,
                main_stack_bytes=macro('CONFIG_ESP_MAIN_TASK_STACK_SIZE'),stream_stack_bytes=16*1024,
                udp_mailbox_packets=macro('CONFIG_LWIP_UDP_RECVMBOX_SIZE'),wifi_static_rx=macro('CONFIG_ESP_WIFI_STATIC_RX_BUFFER_NUM'),
                wifi_dynamic_rx=macro('CONFIG_ESP_WIFI_DYNAMIC_RX_BUFFER_NUM'),header_bytes=header,payload_bytes=payload,
                dma_buffer_bytes=header+payload+1,crc_bit_steps_per_payload_byte=8,qspi_write_clock_cap_hz=40_000_000,
                qspi_read_clock_cap_hz=16_000_000,raw_quad_write_bits_per_second=4*40_000_000,
                worker_command_queue=2,external_psram_enabled=False,device_lock_policy='try_lock_and_drop_frame',
                payload_format='MSV1 JPEG only',ar02_gf02_implemented=False,full_frame_stored_on_esp=False,abort_retry_bound_ms=100,abort_retry_sleep_ms=1,
                credit_register_semantics='remaining current frame bytes, not FIFO free space',
                build_manifest_overall=manifest['overall'],build_manifest_reason=manifest['reason'],
                source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in PATHS})
