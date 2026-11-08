#!/usr/bin/env python3
"""Independent portable review of retained CDC native receipts and vendor reports."""
import hashlib,json,re,shutil
from pathlib import Path
AREA=Path(__file__).resolve().parent
ROOT=AREA.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
    selection=json.loads((AREA/'results.json').read_text());chosen=ROOT/selection['selected_receipt'];assert sha(chosen)==selection['sha256']
    completed=json.loads(chosen.read_text());assert completed['status']=='MAPPED_CDC_UNIT_ROUTE_FINISHED_REVIEW_REQUIRED' and completed['observed_exit_code']==0 and completed['source_snapshot_unchanged']
    ledger=[]
    for path in sorted(AREA.glob('*/receipt.json')):
        r=json.loads(path.read_text());out=path.parent;inputs=json.loads((out/'inputs.json').read_text())
        assert sha(out/'inputs.json')==r['input_manifest_sha256']
        for name,digest in inputs['snapshot_sha256'].items():assert sha(out/'snapshot'/name)==digest,(out,name)
        for name,digest in r['retained_sha256'].items():assert sha(out/name)==digest,(out,name)
        note=out/'coordination-stop.json';classification='CANCELLED_FOR_SHARED_HEAVY_SLOT' if note.exists() else r['status']
        if note.exists():assert r['observed_exit_code']==json.loads(note.read_text())['observed_exit_code']==143
        ledger.append(dict(attempt=out.name,status=classification,receipt_status=r['status'],exit_code=r['observed_exit_code'],wall_seconds=r['wall_seconds'],receipt_sha256=sha(path)))
    assert len(ledger)==4 and [x['exit_code'] for x in ledger]==[1,1,143,0]
    out=chosen.parent;reports=out/'reports';log=(out/'vivado.log').read_text()
    assert 'V107_CDC_UNIT_ROUTE_FINISHED' in log
    assert not re.search(r'CRITICAL WARNING:|ERROR:|[Pp]ath segmentation|no valid startpoints',log)
    proof={};budgets={('commands','wgray'):5,('commands','rgray'):10,('writes','wgray'):10,('writes','rgray'):10,('acks','wgray'):10,('acks','rgray'):10,('lines','wgray'):16.667,('lines','rgray'):10,('pixels','wgray'):10,('pixels','rgray'):16.667}
    for stage in ('synth','place','route'):
        rows=[line.split('\t') for line in (reports/f'{stage}-gray-applied-proof.tsv').read_text().splitlines()[1:]];assert len(rows)==40
        seen=set()
        for fifo,source,start,end,req,budget,exception,slack,delay in rows:
            assert start.endswith('/C') and end.endswith('/D') and '_meta_reg[' in end
            assert abs(float(req)-budgets[fifo,source])<.001 and float(req)==float(budget)
            assert exception==f'MaxDelay Path {float(budget):.3f}ns -datapath_only'
            assert (fifo,source,end) not in seen;seen.add((fifo,source,end))
        proof[stage]=dict(bits=40,bundles=10,worst_slack_ns=min(float(x[7]) for x in rows))
        ignored=(reports/f'{stage}-exceptions-ignored.rpt').read_text();assert 'No ignored timing exceptions found.' in ignored
        coverage=[line for line in (reports/f'{stage}-exception-coverage.rpt').read_text().splitlines() if re.match(r'^\d+\s',line)]
        assert len(coverage)==20 and sum('Max Delay Datapath Only' in x for x in coverage)==10 and sum('False Path' in x for x in coverage)==10
        assert all(x.split()[-2:]==['100.00','100.00'] for x in coverage)
    timing=(reports/'route-timing-summary.rpt').read_text();after=timing.split('| Design Timing Summary',1)[1]
    m=re.search(r'^\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+(\d+)\s*$',after,re.M);assert m
    values=m.groups();metrics=dict(WNS_ns=float(values[0]),TNS_ns=float(values[1]),setup_failing=int(values[2]),WHS_ns=float(values[4]),THS_ns=float(values[5]),hold_failing=int(values[6]),WPWS_ns=float(values[8]),TPWS_ns=float(values[9]),pulse_failing=int(values[10]))
    assert all(metrics[x]==0 for x in ('TNS_ns','setup_failing','THS_ns','hold_failing','TPWS_ns','pulse_failing'))
    assert all(metrics[x]>=0 for x in ('WNS_ns','WHS_ns','WPWS_ns'))
    check=(reports/'route-check-timing.rpt').read_text();counts={k:int(v) for k,v in re.findall(r'checking (\w+) \((\d+)\)',check)}
    for key in ('no_clock','unconstrained_internal_endpoints','loops','multiple_clock','pulse_width_clock'):assert counts[key]==0
    assert counts['no_input_delay']==counts['no_output_delay']==279
    skew=(reports/'route-bus-skew.rpt').read_text().rsplit('\n2. Bus Skew Report Per Constraint',1)[0]
    bus=[tuple(map(float,x)) for x in re.findall(r'^\s+(?:Slow|Fast)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)\s*$',skew,re.M)]
    assert len(bus)==10 and min(x[2] for x in bus)>=0
    route=(reports/'route-status.rpt').read_text();assert re.search(r'fully routed nets\.+\s*:\s*240',route) and re.search(r'nets with routing errors\.+\s*:\s*0',route)
    cdc_text=(reports/'route-cdc.rpt').read_text();cdc={k:dict(severity=s,count=int(n)) for k,s,n in re.findall(r'^(CDC-\d+)\s+(Info|Warning|Critical)\s+(\d+)\s',cdc_text,re.M)}
    assert cdc=={'CDC-3':dict(severity='Info',count=7),'CDC-6':dict(severity='Warning',count=10),'CDC-11':dict(severity='Critical',count=8)}
    method_text=(reports/'route-methodology.rpt').read_text();method={k:int(n) for k,n in re.findall(r'^\|\s*((?:TIMING|SYNTH|LUTAR)-\d+)\s*\|\s*Warning\s*\|[^\n]*?\|\s*(\d+)\s*\|',method_text,re.M)}
    assert method=={'LUTAR-1':1,'SYNTH-4':7,'SYNTH-6':7,'TIMING-18':558}
    drc_text=(reports/'route-drc.rpt').read_text();drc={k:int(n) for k,n in re.findall(r'^\|\s*((?:CFGBVS|CHECK|REQP)-\d+)\s*\|\s*Warning\s*\|[^\n]*?\|\s*(\d+)\s*\|',drc_text,re.M)}
    assert drc=={'CFGBVS-1':1,'CHECK-3':2,'REQP-1839':20,'REQP-1840':20}
    ram=(reports/'route-ram-recognition.tsv').read_text().splitlines()[1:];assert len(ram)==7
    assert sum('RAMB36E1' in x for x in ram)==3 and sum('RAMB18E1' in x for x in ram)==4
    assert len((reports/'route-sync-attributes.tsv').read_text().splitlines()[1:])==112
    utilization=(reports/'route-utilization.rpt').read_text()
    match=re.search(r'\|\s*v107_cdc_fabric\s*\|\s*\(top\)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|',utilization);assert match
    lut,logic,lutram,srl,ff,ram36,ram18,dsp=map(int,match.groups())
    resources=dict(LUT=lut,FF=ff,RAMB36=ram36,RAMB18=ram18,DSP=dsp)
    assert resources==dict(LUT=91,FF=196,RAMB36=3,RAMB18=4,DSP=0)
    # Preserve previously hashed vendor JSON portably, without changing receipts.
    review=AREA/'review';review.mkdir(exist_ok=True)
    copied={}
    for stage in ('synth','place','route'):
        name=f'{stage}-methodology.json';a=completed['artifacts'][name];src=Path(a['external_path'])
        if src.exists():assert sha(src)==a['sha256']
        dst=review/name
        if src.exists():shutil.copyfile(src,dst)
        assert dst.exists() and sha(dst)==a['sha256']
        copied[name]=dict(sha256=sha(dst),receipt_artifact_sha256=a['sha256'])
    result=dict(schema='v107-cdc-native-portable-audit-v1',status='PASS_EVIDENCE_WITH_OPEN_CDC_AND_RESET_FINDINGS',source_receipt=str(chosen.relative_to(ROOT)),source_receipt_sha256=sha(chosen),ledger=ledger,scope='Synthetic isolated fabric unit only; not parent timing/CDC/hardware signoff',route_timing=metrics,gray_applied_checks=proof,bus_skew=dict(constraints=10,worst_slack_ns=min(x[2] for x in bus),maximum_actual_ns=max(x[1] for x in bus)),exception_coverage=dict(gray_bundles=10,peer_up_first_stages=10,all_from_to_percent=100,ignored=0),routed_nets=240,routing_errors=0,check_timing=counts,resources=resources,synchronizer_flops_with_ASYNC_REG=112,cdc=cdc,methodology=method,drc_displayed=drc,drc_report_limits_reached=True,open_findings=['CDC-11: shared startup-up source fanout into independently synchronized channels; no common parent owner/reconvergence proof.','CDC-6: ten multi-bit Gray crossings need reviewed semantics beyond physical delay/skew evidence.','LUTAR-1: ORed asynchronous reset requests require clean reset generation.','REQP-1839/1840: asynchronously reset address/control flops can disturb BRAM during reset; pointer ownership model is not technology reset/collision proof.','TIMING-18: 279 input and 279 output ports lack real parent timing; no board contract inferred.','SYNTH-4/6: deliberate shallow synchronous dual-clock BRAM, no area/BRAM optimization claim.','CFGBVS-1: unit does not specify actual board configuration voltage.'],portable_methodology_json=copied,waivers_added=False,RTL_changes_after_behavioral_PASS=False)
    write(AREA/'native-audit.json',result);print(result['status']);print(json.dumps(dict(route_timing=metrics,gray=proof['route'],bus_skew=result['bus_skew']),sort_keys=True))
if __name__=='__main__':main()
