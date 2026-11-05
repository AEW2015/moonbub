#!/usr/bin/env python3
"""Compare V72 scalar reference service with V73 wide-row cache ablations."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v73/system'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    paths=[ROOT/'fpga/experiments/cu66-v72/system/full-strip/results.json',AREA/'full-strip-cache1/results.json',AREA/'full-strip/results.json']
    old,one,eight=[json.loads(p.read_text())for p in paths]
    assert one['p0_cache_lines']==1 and eight['p0_cache_lines']==8
    assert one['source_sha256']==eight['source_sha256'] and old['clocks']==one['clocks']==eight['clocks']
    common=old['source_sha256'].keys()&eight['source_sha256'].keys()
    assert common and all(old['source_sha256'][p]==eight['source_sha256'][p]for p in common)
    assert all(j['status']=='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS' and j['summary']['total_underruns']==0 and j['summary']['distinct_complete_presentations']==2 for j in (old,one,eight))
    rows=[];period=eight['clocks']['memory_period_ps']
    for a,b,c,ta,tb,tc in zip(old['frames'],one['frames'],eight['frames'],old['timings'],one['timings'],eight['timings'],strict=True):
        assert (a['fid'],a['key'],a['generation'])==(b['fid'],b['key'],b['generation'])==(c['fid'],c['key'],c['generation'])
        assert all(f['actual_writes']==664320 and f['actual_write_commands']==133920 and f['actual_write_bus_beats']==1071360 for f in (a,b,c))
        assert b['p0_row_reads']==c['p0_row_reads']
        for f in (b,c):
            assert f['p0_cache_hits']+f['p0_cache_misses']==f['p0_row_reads']
            assert f['p0_read_wait_cycles']<=f['p0_wait_cycles'] and f['p0_read_service_cycles']<=f['p0_service_cycles']
        r=dict(fid=c['fid'],key=bool(c['key']),v72=a,v73_cache1=b,v73_cache8=c,
            v72_transaction_model_ms=a['cycles']*period/1e9,v73_cache1_transaction_model_ms=b['cycles']*period/1e9,v73_cache8_transaction_model_ms=c['cycles']*period/1e9,
            v72_validated_interval_model_ms=ta['validated_decode_model_cycles']*period/1e9,v73_cache1_validated_interval_model_ms=tb['validated_decode_model_cycles']*period/1e9,v73_cache8_validated_interval_model_ms=tc['validated_decode_model_cycles']*period/1e9,
            v72_composition_model_ms=ta['composition_model_cycles']*period/1e9,v73_cache8_composition_model_ms=tc['composition_model_cycles']*period/1e9,
            total_cycle_reduction_percent=100*(a['cycles']-c['cycles'])/a['cycles'],wide_row_only_cycle_reduction_percent=100*(a['cycles']-b['cycles'])/a['cycles'],cache8_over_cache1_cycle_reduction_percent=100*(b['cycles']-c['cycles'])/b['cycles'])
        if c['p0_row_reads']:
            assert c['p0_cache_misses']<b['p0_cache_misses']
            r['reference_read_command_reduction_percent']=100*(b['p0_cache_misses']-c['p0_cache_misses'])/b['p0_cache_misses']
            r['reference_useful_bytes']=c['p0_row_reads']*8
            r['cache1_reference_wire_bytes']=b['p0_cache_misses']*16
            r['cache8_reference_wire_bytes']=c['p0_cache_misses']*16
            r['v72_scalar_ref_requests_inferred']=4*c['p0_row_reads']
        rows.append(r)
    result=dict(status='PASS_EXACT_OUTPUT_COMPARISON',frames=rows,clocks=eight['clocks'],shared_v72_source_pins=len(common),
        input_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},script_sha256=sha(Path(__file__).resolve()),
        scope='samepacket/clock exactoutput comparison; wide-row cache1 isolates row requests, cache8 isolates added reference locality',
        limitations=['V72 scalar-ref count inferred from unchanged reference-tile work and frozen32word/tile adapter; not a V72instrumented counter','decoder-paced key/P and short history are not fixedarrival30fps campaigns','duration and phase change background LCD/refresh work; not normalized totalreadcount/underrunrate comparison','processorHUDexecution and live transport not charged in model; no targetsub10ms or physical30fps/fit/Fmax/CDC proof'])
    (AREA/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in rows:print(f"FRAME{r['fid']} V72_ms={r['v72_transaction_model_ms']:.5f} cache1_ms={r['v73_cache1_transaction_model_ms']:.5f} cache8_ms={r['v73_cache8_transaction_model_ms']:.5f} reduction={r['total_cycle_reduction_percent']:.3f}%")
    print('V73_COMPARISON_PASS exact=true zeroLCDunderruns=true target30fps_proven=false')
if __name__=='__main__':main()
