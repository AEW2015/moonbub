#!/usr/bin/env python3
"""Read-only control/data replays; no external source footage needed."""
import json
from pathlib import Path
import benchmark as b
import model as r

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    data = json.loads((HERE / 'results.json').read_text())
    for path, digest in data['source_sha256'].items():
        assert b.sha(ROOT / path) == digest, path
    assert data['schema'] == 'gamebub-recovery-v24'
    assert data['control_bytes'] == 46 and data['profile_sha256_128'] == r.PROFILE_TAG.hex()
    count = messages = lost = 0
    for case in data['results']['cases']:
        n = 0
        for item in case['trace']:
            packet = bytes.fromhex(item['bytes'])
            assert len(packet) == 46 and r.parse(packet)['kind'] == item['kind']
            n += len(packet)
            messages += 1
            lost += not item['delivered']
        assert n == case['control_application_bytes']
        assert case['control_ipv4_udp_bytes'] == n + 28 * len(case['trace'])
        count += case['complete']
    # Independently rerun all functional fault sequences and actual data probes.
    assert b.run() == data['results']
    assert count == 9 and len(data['results']['cases']) == 10
    print(json.dumps(dict(campaigns=10, successful_nominal_or_single_loss=9,
                          parsed_control_messages=messages, lost_controls_charged=lost,
                          persistent_loss_host_safe_stop=True, reboot_epoch_sequence=[1, 2, 3],
                          stale_epoch_data_rejected=True, physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
