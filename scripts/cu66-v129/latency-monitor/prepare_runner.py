#!/usr/bin/env python3
"""Copy the verified live-parent runner into a separate monitor-only namespace."""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[3]
src=root/'scripts/cu66-v129/integration/live_guard/qualify.py'
dst=Path(__file__).with_name('run_parent.py')
s=src.read_text()
def change(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old))
    s=s.replace(old,new,1)
change("ROOT = Path(__file__).resolve().parents[4]", "ROOT = Path(__file__).resolve().parents[3]")
change("AREA = ROOT/'experiments/python-gamebub-v129/integrated-study/live-guard'", "AREA = ROOT/'experiments/python-gamebub-v129/latency-monitor/full-parent'")
change("'v129-cuts-live-guard-'+stamp", "'v129-monitor-live-guard-'+stamp")
change("'gamebub-v129-cuts-live-guard-'+stamp", "'gamebub-v129-monitor-live-guard-'+stamp")
change("args.root_grant=='ROOT_V129_PARENT'", "args.root_grant=='ROOT_V129_MONITOR'")
change("files = sorted(set(sources+endpoints+inputs+support+proof_files+", "files = sorted(set([ROOT/'fpga/experiments/cu66-v129-observe/tb_keyframe.cpp',ROOT/'fpga/experiments/cu66-v129-observe/monitor.hpp',ROOT/'scripts/cu66-v129/latency-monitor/prepare.py',ROOT/'scripts/cu66-v129/latency-monitor/prepare_runner.py']+sources+endpoints+inputs+support+proof_files+")
change("*sv,snap(SRC/'tb_keyframe.cpp')], variant+'-compile.log'", "*sv,snap(ROOT/'fpga/experiments/cu66-v129-observe/tb_keyframe.cpp')], variant+'-compile.log'")
change("for seed, profile in [(116701,0),(116702,1)]:", "for seed, profile in [(116702,1)]:")
change("variants = [('byte',0),('row',1)] if args.variant == 'both' else [(args.variant,int(args.variant == 'row'))]", "assert args.variant == 'row'; variants = [('row',1)]")
change("                v, c, s = verdict[0], live[0], service[0]", """                observed=[r for r in rows if r.get('type')=='v129_latency_monitor']
                assert len(observed)==1
                o=observed[0]
                assert o['simulation_only'] and o['primary_is_priority_not_cause']
                assert sum(o['mask_counts'])==sum(o['priority_counts'])==o['cycles']
                assert all(sum(channel)==o['cycles'] for channel in o['handshake_no_valid_stalled_accepted'])
                report['monitor_record']=o
                v, c, s = verdict[0], live[0], service[0]""")
change("status='PASS_V129_SELECTED_COMPONENT_'", "status='PASS_V129_MONITOR_ONLY_SELECTED_COMPONENT_'")
dst.write_text(s)
print('derived_runner_sha256',hashlib.sha256(dst.read_bytes()).hexdigest())
