#!/usr/bin/env python3
"""Bind V97 PC, independent audit, native Rust and live RTL receipts."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v97'
BASELINE = 'bd8fcc49c1c6b069432dd1ae93109640359fea8e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins = {}
    def read(name):
        path = ROOT / name
        pins[str(path.relative_to(ROOT))] = sha(path)
        return json.loads(path.read_text())
    def verify(report, path):
        assert report['status'] == 'pass' or report['status'].startswith('PASS'), (path, report['status'])
        for key in ('source_sha256', 'sources'):
            for name, digest in report.get(key, {}).items():
                assert sha(ROOT/name) == digest, ('stale executable source/input',path,name)
        for key in ('artifacts_sha256','artifacts'):
            for name, digest in report.get(key, {}).items():
                assert sha((ROOT/path).parent/name) == digest, ('changed artifact',path,name)
        for command in report.get('commands',[]):
            status = command.get('returncode', command.get('exit_code'))
            assert status == 0, (path,command)
    host_pointer = read('experiments/python-gamebub-v97/host/results.json')
    host_path = host_pointer['selected_report'];host = read(host_path);verify(host,host_path)
    audit = read('experiments/python-gamebub-v97/host-audit/receipt.json')
    assert audit['status'] == 'PASS'
    assert sha(ROOT/audit['root_report']) == audit['root_report_sha256']
    assert sha(ROOT/audit['selected_attempt_report']) == audit['selected_attempt_report_sha256']
    assert sha(ROOT/'scripts/cu66-v97/check_host.py') == audit['receipt_code_sha256']
    for name,digest in audit['selected_attempt_source_sha256'].items():assert sha(ROOT/name)==digest
    native_pointer=read('experiments/python-gamebub-v97/protocol/index.json')
    native_path=native_pointer['attempt_json'];native=read(native_path);verify(native,native_path)
    native_dir=(ROOT/native_path).parent
    assert sha(native_dir/'native-tests') == native['binary_sha256']
    assert 'warning:' not in (native_dir/'native-compile.log').read_text().lower()
    native_log=(native_dir/'native-tests.log').read_text()
    assert '23 passed; 0 failed' in native_log
    assert native['python']['cases']==138 and native['python']['rows']==865
    assert native['native_metrics']['gateway_plus_receive_bytes']==4480
    ffi_pointer=read('experiments/python-gamebub-v97/protocol/ffi-index.json')
    ffi_path=ffi_pointer['receipt'];ffi=read(ffi_path);verify(ffi,ffi_path)
    ffi_dir=(ROOT/ffi_path).parent
    assert sha(ffi_dir/'libv97_gateway.a')==ffi['staticlib_sha256']
    assert sha(ffi_dir/'ffi-tests')==ffi['ffi_tests_sha256']
    assert '3 passed; 0 failed' in (ffi_dir/'ffi-tests.log').read_text()
    assert not (ffi_dir/'ffi-staticlib-compile.log').read_text().strip()
    assert not (ffi_dir/'ffi-test-compile.log').read_text().strip()
    rtl_pointer=read('fpga/experiments/cu66-v97-forward/results.json')
    rtl_path=rtl_pointer['selected_report'];rtl=read(rtl_path);verify(rtl,rtl_path)
    rtl_dir=(ROOT/rtl_path).parent
    assert rtl['native_trace_join_requested'] and rtl['native_live_join_requested']
    assert rtl['native_live']['receipt_sha256']==sha(ROOT/ffi_path)
    assert rtl['native_live']['staticlib_sha256']==ffi['staticlib_sha256']
    assert rtl['native_trace']['producer_manifest']['sha256']==sha(ROOT/native_path)
    verdict=rtl['verdict'];live=rtl['live_join'][0];trace=rtl['native_join'][0]
    assert verdict['status']=='TEST_PASS' and live['status']==trace['status']=='PASS'
    assert verdict['max_fifo']==verdict['max_reserved']==2048 and verdict['max_slots']==2
    assert len(rtl['live_frames'])==live['frames']==11 and live['logical_bytes']==231416
    assert live['rejected_frames']==2 and live['ignored_padding_bytes']==20
    assert sum(frame['bytes'] for frame in rtl['live_frames'])==live['logical_bytes']
    assert trace['frames']==12 and trace['ignored_padding_bytes']==19
    # Replay each real complete payload CRC independently, including rewritten
    # recovery frame IDs. Synthetic tail fixtures are transport bytes, not JPEGs.
    fixture_bytes={}
    for item in ffi['inputs']:
        data=(ffi_dir/'data'/(item['name']+'.bin')).read_bytes()
        assert hashlib.sha256(data).hexdigest()==item['payload_sha256']
        fixture_bytes[item['name']]=data
    import zlib
    for row in rtl['live_frames']:
        fixture=row['fixture'].removesuffix('-recovery')
        data=fixture_bytes[fixture]
        assert len(data)==row['bytes'] and zlib.crc32(data)==row['crc32']
    # The runtime worker is unchanged apart from exposing the portable module.
    module=ROOT/'firmware/handheld/src/streaming/mod.rs'
    addition='// Portable V97 candidate; the network worker below continues to use MSV1.\npub mod protocol97;\n'
    current=module.read_text();assert current.count(addition)==1
    original=subprocess.check_output(['git','show',BASELINE+':firmware/handheld/src/streaming/mod.rs'],cwd=ROOT,text=True)
    assert current.replace(addition,'',1)==original
    pins[str(module.relative_to(ROOT))]=sha(module)
    for path in ('host/moonshine/protocol.py','firmware/handheld/src/streaming/protocol.rs'):
        original=subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
        assert (ROOT/path).read_bytes()==original
        pins[path]=sha(ROOT/path)
    summary=audit['summary']
    assert summary['total_rows']==469 and summary['sessions']['total']==5
    assert summary['compact_application_bytes_with_setup']==8699013
    assert summary['legacy_application_bytes']==8960501
    assert summary['compact_ipv4_udp_bytes_with_setup']==8878045
    assert summary['legacy_ipv4_udp_bytes']==9202701
    pins[str(Path(__file__).resolve().relative_to(ROOT))]=sha(Path(__file__).resolve())
    result=dict(schema='cu66-v97-qualified-summary-v1',status='PASS',input_sha256=pins,
                protocol=dict(native_tests=23,ffi_tests=3,shared_cases=138,shared_rows=865,
                              accepted_fragments=600,rejections=121),
                memory=native['native_metrics'],
                host=dict(jpeg_frames=12,opaque_frames=457,checks=host['host_checks'],
                          jpeg_prepare_ns=host['synthetic_jpeg_prepare_ns'],opaque_crc_packetize_ns=host['opaque_crc_packetize_ns'],
                          framing=summary,ipv4_udp_savings_percent=100*summary['ipv4_udp_savings_with_setup_bytes']/summary['legacy_ipv4_udp_bytes']),
                rtl=dict(verdict=verdict,live=live,trace=trace,live_frames=rtl['live_frames']),
                runtime_worker_behavior_changed=False,portable_module_exported=True,
                checkpoint='V97 portable transport, host preparation and live native-Rust/RTL ingress checkpoint; deployed worker/driver and hardware calibration open.',
                actual_esp32_execution=False,renode_run=False,qspi_pin_cosimulation=False,
                sunshine_live_capture_tested=False,hardware_30fps_proven=False,validated_under10ms_proven=False,
                exclusions=['Native x86_64 Rust and synchronous parallel FPGA interface; no ESP32 CPU/FreeRTOS/Wi-Fi/lwIP/DMA arbitration timing.',
                            'No production QSPI capability/register adapter or V97 UDP worker; MSV1 worker retained.',
                            'Opaque CS92 bodies validate transport bytes only, not custom decoding/reference semantics.',
                            'Ingress commit is not C2/HUD/root/seal validation or display publication.',
                            'Synthetic JPEG preparation and frozen codec payloads; no independent raw-capture rate/quality comparison.',
                            'No RF/MAC/retry/feedback costs in framing budgets; no target heap-fit or DMA-capability proof.'])
    (AREA/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS_V97_SUMMARY','liveframes',live['frames'],'RTLchecks',verdict['checks'],'wire_saving_percent',round(result['host']['ipv4_udp_savings_percent'],3))


if __name__=='__main__':
    main()
