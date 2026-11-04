#!/usr/bin/env python3
"""Read-only deterministic replay of bounded admission/credit evidence."""
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('paced_gateway_builder',HERE/'benchmark.py')
builder=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=builder;_spec.loader.exec_module(builder)

def verify():
    data=json.loads((HERE/'results.json').read_text())
    assert data['source_sha256']==builder.pins()
    assert data==builder.build()
    assert data['case_count']==len(data['cases'])==36
    for row in data['cases']:
        r=row['result'];cfg=r['config'];p=r['policy']
        assert cfg['header']==56 and cfg['chunk']==1008 and cfg['header']+cfg['chunk']==1064
        assert r['peak_host_active_frames']<=1 and r['peak_host_latest_frames']<=1
        assert r['peak_packet_credits']<=p['window']<=6 and r['peak_receiver_mailbox']<=6
        assert r['peak_receiver_credit_ledger']<=p['window'] and r['peak_control_queries_pending']<=p['window']
        assert r['counters'].get('mailbox_full',0)==r['counters'].get('control_mailbox_full',0)==0
        assert all(a['predicted_complete_us']<=a['deadline_us'] for a in r['admissions'])
        good={c['id'] for c in r['completed']};bad={d['id'] for d in r['drops']}
        assert not good&bad and len(good)+len(bad)==r['input_frames']
        assert r['eventual_complete']==len(good)
        assert r['strict_complete']==sum(c['at_us']<r['capture_window_us'] for c in r['completed'])
        assert not r['physical_30fps_proven'] and not r['current_firmware_supports_credit_protocol']
        if row['profile']=='feedback_blackhole':
            assert r['counters'].get('credits_applied',0)==0 and r['host_active_frame'] is not None
            assert sum(x is not None for x in r['outstanding_credit_slots'])==6
            assert not r['all_admitted_packets_issued']
        else:
            assert r['all_admitted_packets_issued'] and r['host_active_frame'] is None
            assert all(x is None for x in r['outstanding_credit_slots'])
    return dict(cases=36,source_snapshot_bindings=len(data['source_sha256']),bounded_source_and_host_frames=[1,1],data_tokens=6,reserved_query_tokens=1,
        receiver_mailbox=6,maximum_datagram_bytes=1064,esp_dma_bytes=1065,mailbox_drops=0,
        lost_feedback='explicitledgerquery;nocreditinvented',blackhole='boundedstop;partialwireworkunresolved',
        installed_protocol_or_hardware_30fps_proven=False)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
