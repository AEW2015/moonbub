#!/usr/bin/env python3
"""Independently audit the selected V97 host byte budget and JPEG artifacts."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v97/host'
OUT = ROOT/'experiments/python-gamebub-v97/host-audit'
EXPECTED_ROWS = {'jpeg': 12, 'opaque': 457}
SOURCE_FILES = (
    'scripts/cu66-v97/run_host.py',
    'host/moonshine/protocol.py',
    'host/moonshine/protocol97.py',
    'host/moonshine/transport97_sender.py',
    'host/moonshine/encoding.py',
)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def ceildiv(n, d):
    return (n + d - 1)//d


def audit_lane(rows, payload_size, app_header, name):
    totals = {'payload_bytes': 0, 'datagrams': 0, 'application_header_bytes': 0,
              'application_bytes': 0, 'ipv4_udp_header_bytes': 0,
              'ipv4_udp_bytes': 0}
    checked = []
    for row in rows:
        payload = int(row['payload_bytes'])
        packets = ceildiv(payload, payload_size)
        app_headers = app_header*packets + (16 if app_header == 12 else 0)
        # Common 16-byte frame-start metadata is sent once in the first compact
        # fragment; the legacy 40-byte header already repeats all metadata.
        if name == 'legacy':
            app_headers = app_header*packets
        app = payload + app_headers
        ipudp_headers = 28*packets
        ipudp = app + ipudp_headers
        if name == 'compact':
            assert row['datagrams'] == packets, (row, packets)
            assert row['compact_application_bytes'] == app, (row, app)
            assert row['compact_ipv4_udp_bytes'] == ipudp, (row, ipudp)
        else:
            assert row['legacy_datagrams'] == packets, (row, packets)
            assert row['legacy_application_bytes'] == app, (row, app)
            assert row['legacy_ipv4_udp_bytes'] == ipudp, (row, ipudp)
        totals['payload_bytes'] += payload
        totals['datagrams'] += packets
        totals['application_header_bytes'] += app_headers
        totals['application_bytes'] += app
        totals['ipv4_udp_header_bytes'] += ipudp_headers
        totals['ipv4_udp_bytes'] += ipudp
        checked.append({'payload_bytes': payload, 'datagrams': packets,
                        'application_header_bytes': app_headers,
                        'application_bytes': app,
                        'ipv4_udp_bytes': ipudp})
    return totals, checked


def main():
    root_path = AREA/'results.json'
    root_report = json.loads(root_path.read_text())
    selected_rel = root_report.get('selected_report')
    assert selected_rel and not Path(selected_rel).is_absolute()
    selected_path = ROOT/selected_rel
    assert selected_path.is_file()
    report = json.loads(selected_path.read_text())
    assert report['status'] == root_report['status'] == 'PASS_PC_PREPARE_AND_FRAMING'
    root_compare = dict(root_report)
    root_compare.pop('selected_report', None)
    assert root_compare == report, 'selected report differs from root pointer'
    assert len(report['jpeg_rows']) == EXPECTED_ROWS['jpeg']
    assert len(report['opaque_rows']) == EXPECTED_ROWS['opaque']
    assert report['synthetic_jpeg_frames'] == EXPECTED_ROWS['jpeg']
    assert report['opaque_frames'] == EXPECTED_ROWS['opaque']
    assert report['setup_exchange_bytes'] == 80
    assert report['actual_esp32_execution'] is False
    assert report['hardware_30fps_proven'] is False

    receipt_sources = report['source_sha256']
    expected_sources = set(SOURCE_FILES) | {
        'experiments/python-gamebub-v92/wire/results.json',
    }
    assert expected_sources <= receipt_sources.keys()
    current_source_hashes = {}
    for name, expected in receipt_sources.items():
        path = ROOT/name
        assert path.is_file(), ('missing pinned source', name)
        actual = sha(path)
        assert actual == expected, ('source changed since host run', name)
        current_source_hashes[name] = actual
    attempt_dir = selected_path.parent
    for name in SOURCE_FILES:
        snapshot = attempt_dir/'sources'/name
        assert snapshot.is_file() and sha(snapshot) == receipt_sources[name], (
            'attempt source snapshot mismatch', name)

    # Every image is reopened from the selected attempt and fully decoded by
    # Pillow. No transport module or protocol implementation is imported.
    pillow_root = Path('/home/lori/gamebub-streaming-prototype/.venv')
    if str(pillow_root/'lib') not in sys.path:
        for site in sorted((pillow_root/'lib').glob('python*/site-packages')):
            sys.path.insert(0, str(site))
    from PIL import Image
    jpeg_artifacts = []
    jpeg_by_name = {f'jpeg-{i:02}.jpg': row for i, row in enumerate(report['jpeg_rows'])}
    for name, row in sorted(jpeg_by_name.items()):
        path = attempt_dir/name
        expected_hash = report['artifacts_sha256'].get(name)
        assert path.is_file() and expected_hash and sha(path) == expected_hash, (
            'JPEG artifact hash', name)
        with Image.open(path) as image:
            assert image.format == 'JPEG', (name, image.format)
            assert image.size == (720, 480), (name, image.size)
            image.load()
            assert image.size == (720, 480)
        assert path.stat().st_size == row['payload_bytes']
        assert expected_hash == row['payload_sha256']
        jpeg_artifacts.append({'file': name, 'sha256': expected_hash,
                               'bytes': row['payload_bytes'],
                               'format': 'JPEG', 'size': [720, 480],
                               'fully_decoded': True})

    by_cohort = {}
    for row in report['opaque_rows']:
        by_cohort.setdefault(int(row['cohort']), []).append(row)
    assert sorted(by_cohort) == [0, 1, 2, 3]
    assert sum(map(len, by_cohort.values())) == EXPECTED_ROWS['opaque']

    lanes = {}
    for lane, size, header in (('compact', 1400, 12), ('legacy', 1024, 40)):
        jpeg, _ = audit_lane(report['jpeg_rows'], size, header, lane)
        opaque, _ = audit_lane(report['opaque_rows'], size, header, lane)
        lanes[lane] = {'jpeg': jpeg, 'opaque': opaque,
                       'combined_data_only': {k: jpeg[k] + opaque[k] for k in jpeg}}

    compact = lanes['compact']['combined_data_only']
    legacy = lanes['legacy']['combined_data_only']
    sessions = {'jpeg': 1, 'opaque': len(by_cohort), 'total': 1+len(by_cohort)}
    setup = {'jpeg_application_bytes': 80,
             'opaque_application_bytes': 80*len(by_cohort),
             'total_application_bytes': 80*sessions['total'],
             'ipv4_udp_headers_if_two_datagrams_per_session': 28*2*sessions['total']}
    compact_app_with_setup = compact['application_bytes'] + setup['total_application_bytes']
    compact_ipv4_udp_with_setup = compact['ipv4_udp_bytes'] + setup['total_application_bytes'] + setup['ipv4_udp_headers_if_two_datagrams_per_session']

    lane_summaries = {}
    for key in ('jpeg', 'opaque'):
        c = lanes['compact'][key]
        l = lanes['legacy'][key]
        lane_setup = setup[f'{key}_application_bytes']
        lane_setup_headers = 28*2*sessions[key]
        lane_summaries[key] = {
            'compact_data_only': c,
            'legacy_data_only': l,
            'setup_sessions': sessions[key],
            'compact_setup_application_bytes': lane_setup,
            'compact_setup_ipv4_udp_header_bytes_if_two_datagrams_each': lane_setup_headers,
            'application_savings_after_setup_bytes': l['application_bytes'] - (c['application_bytes']+lane_setup),
            'application_savings_after_setup_percent_of_legacy': round(100*(l['application_bytes']-(c['application_bytes']+lane_setup))/l['application_bytes'], 6),
            'ipv4_udp_savings_after_setup_bytes': l['ipv4_udp_bytes'] - (c['ipv4_udp_bytes']+lane_setup+lane_setup_headers),
        }

    summary = {
        'jpeg_rows': len(report['jpeg_rows']),
        'opaque_cs92_rows': len(report['opaque_rows']),
        'total_rows': len(report['jpeg_rows'])+len(report['opaque_rows']),
        'opaque_cohorts': {str(k): len(v) for k, v in sorted(by_cohort.items())},
        'sessions': sessions,
        'setup_ack_charge': setup,
        'compact_data_only': compact,
        'legacy_data_only': legacy,
        'compact_application_bytes_with_setup': compact_app_with_setup,
        'legacy_application_bytes': legacy['application_bytes'],
        'application_savings_with_setup_bytes': legacy['application_bytes']-compact_app_with_setup,
        'compact_ipv4_udp_bytes_with_setup': compact_ipv4_udp_with_setup,
        'legacy_ipv4_udp_bytes': legacy['ipv4_udp_bytes'],
        'ipv4_udp_savings_with_setup_bytes': legacy['ipv4_udp_bytes']-compact_ipv4_udp_with_setup,
        'lanes': lane_summaries,
        'MAC_retry_wifi_airtime_included': False,
        'quality_comparison_claimed': False,
    }
    receipt = {
        'schema': 'cu66-v97-host-audit-v1',
        'status': 'PASS',
        'root_report': str(root_path.relative_to(ROOT)),
        'root_report_sha256': sha(root_path),
        'selected_attempt_report': str(selected_path.relative_to(ROOT)),
        'selected_attempt_report_sha256': sha(selected_path),
        'selected_attempt_source_sha256': current_source_hashes,
        'receipt_code_sha256': sha(Path(__file__).resolve()),
        'jpeg_artifacts': jpeg_artifacts,
        'summary': summary,
        'scope': ('Independent arithmetic recount of compact 12-byte fragment plus '
                  '16-byte frame-start framing versus legacy MSV1 framing on the '
                  'selected 12-JPEG and 457 opaque CS92 rows. Pillow fully decoded '
                  'only the 12 JPEG outputs. No protocol/parser/sender import, '
                  'quality comparison, MAC cost, retry cost, or hardware claim.'),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'byte-budget.json').write_text(json.dumps(summary, indent=2)+'\n')
    (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('PASS_V97_HOST_AUDIT', summary['total_rows'],
          'rows; compact-app-savings-with-setup=',
          summary['application_savings_with_setup_bytes'], 'bytes')


if __name__ == '__main__':
    main()
