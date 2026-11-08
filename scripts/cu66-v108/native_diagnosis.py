#!/usr/bin/env python3
"""Read retained native reports into a compact critical-path/fanout table."""
import json
from pathlib import Path

import native as frozen

AREA=frozen.AREA

def fanout(path):
    rows=[]
    for line in path.read_text().splitlines():
        cols=[x.strip() for x in line.split('|')[1:-1]]
        if len(cols)!=17 or not cols[1].isdigit():continue
        rows.append(dict(net=cols[0],fanout=int(cols[1]),driver=cols[2],worst_slack_ns=float(cols[3]),worst_delay_ns=float(cols[4]),
            clock_enable_loads=sum(map(int,cols[5:8])),set_reset_loads=sum(map(int,cols[8:11])),data_other_loads=sum(map(int,cols[11:14]))))
    assert rows and max(x['fanout'] for x in rows)==rows[0]['fanout']
    return rows

def main():
    rows=[];failed=[]
    paths=[p for folder in ('native','capacity-native','outtile-native') for p in (AREA/folder).glob('*/receipt.json')]
    for p in sorted(paths):
        r=frozen.load(p)
        if 'result' not in r:
            if r['status']!='RUNNING':failed.append(dict(trial=r['trial_id'],mode=r['start_mode'],status=r['status'],receipt=dict(path=frozen.rel(p),sha256=frozen.sha(p)),final_routed_timing_available=False))
            continue
        nets=fanout(p.parent/'reports/route-high-fanout.rpt');timing=r['result']['timing'];samples=r['memory_samples']
        rows.append(dict(trial=r['trial_id'],mode=r['start_mode'],receipt=dict(path=frozen.rel(p),sha256=frozen.sha(p)),
            status=r['status'],directives=r['directives'],timing=timing,worst_path=r['result']['worst_setup_path'],
            worst_fanout=nets[0],highest_reset_fanout=max(nets,key=lambda x:x['set_reset_loads']),highest_clock_enable_fanout=max(nets,key=lambda x:x['clock_enable_loads']),
            retained_fanout_report=dict(path=frozen.rel(p.parent/'reports/route-high-fanout.rpt'),sha256=frozen.sha(p.parent/'reports/route-high-fanout.rpt')),
            memory_available_min_bytes=min(x['MemAvailable_bytes'] for x in samples),PSI_full_avg10_max=max(x['PSI_full_avg10'] for x in samples),
            container_memory_max_bytes=max(x['container_memory_bytes'] or 0 for x in samples),wall_seconds=r['wall_seconds']))
    rows.sort(key=lambda x:(x['trial'],x['mode']))
    out=AREA/'native-diagnosis.json';frozen.write(out,dict(schema='v108-native-path-and-fanout-diagnosis-v1',status='READ_ONLY_MEASURED_NATIVE_REPORTS',rows=rows,terminal_without_final_routed_metrics=failed,
        limits=['Only completed routes with parsed reports included.','Fanout classifications are reported sink counts, not RTL repair proofs.','No new FPGA, RTL, hardware or timing execution.']))
    text='# Native critical paths and control fanout\n\nThese are actual routed component reports at the unchanged 10 ns clock.\nPlacement estimates are not used. The complete reports and receipt hashes are\nbound in [native-diagnosis.json](../../experiments/python-gamebub-v108/native-diagnosis.json).\n\n'
    text+='| Trial/mode | WNS ns | Failed setup | Critical path levels | Critical source → destination | Peak fanout | Peak SR loads | Peak CE loads |\n| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |\n'
    for r in rows:
        p=r['worst_path'];text+=f"| {r['trial']}/{r['mode']} | {r['timing']['WNS_ns']:.3f} | {r['timing']['setup_failing']:,} | {p['logic_levels']} | `{p['source']}` → `{p['destination']}` | {r['worst_fanout']['fanout']:,} | {r['highest_reset_fanout']['set_reset_loads']:,} | {r['highest_clock_enable_fanout']['clock_enable_loads']:,} |\n"
    if failed:
        text+='\nTerminal trials without final routed timing:\n\n'
        text+='\n'.join(f"- {r['trial']}/{r['mode']}: `{r['status']}`. No final routed metrics are inferred." for r in failed)+'\n'
    text+='\nLarge set/reset and clock-enable sink counts remain candidates for later RTL\nlocalization or payload-reset removal, subject to exact behavioral qualification.\nThe critical path depth also matters: directive changes alone do not remove the\nunderlying combinational dependency. No constraints were waived or relaxed.\n'
    (frozen.ROOT/'docs/cu66-v108/native-diagnosis.md').write_text(text)
    print('V108_NATIVE_DIAGNOSIS',len(rows),frozen.rel(out),frozen.sha(out))

if __name__=='__main__':main()
