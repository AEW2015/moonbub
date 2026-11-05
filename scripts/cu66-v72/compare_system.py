#!/usr/bin/env python3
"""Compare frozen V71 and V72 exact command-model key/P transactions."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v72/system'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    paths=[ROOT/'fpga/experiments/cu66-v71/system/full-strip/results.json',AREA/'full-strip/results.json']
    old,new=[json.loads(p.read_text())for p in paths]
    assert old['clocks']==new['clocks'] and old['strip'] and new['strip']
    assert old['status']==new['status']=='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS'
    assert old['summary']['total_underruns']==new['summary']['total_underruns']==0
    common=old['source_sha256'].keys()&new['source_sha256'].keys()
    assert common and all(old['source_sha256'][p]==new['source_sha256'][p]for p in common)
    period=new['clocks']['memory_period_ps'];rows=[]
    for a,b,ta,tb in zip(old['frames'],new['frames'],old['timings'],new['timings'],strict=True):
        assert (a['fid'],a['key'],a['generation'])==(b['fid'],b['key'],b['generation'])
        assert a['actual_writes']==b['actual_writes']==664320
        assert b['actual_write_commands']==133920 and b['actual_write_bus_beats']==1071360
        assert b['painter_write_commands']==48000 and b['painter_write_words']==384000
        rows.append(dict(fid=b['fid'],key=bool(b['key']),v71=a,v72=b,
            v71_transaction_model_ms=a['cycles']*period/1e9,
            v72_transaction_model_ms=b['cycles']*period/1e9,
            transaction_cycle_reduction_percent=100*(a['cycles']-b['cycles'])/a['cycles'],
            v71_validated_decode_model_ms=ta['validated_decode_model_cycles']*period/1e9,
            v72_validated_decode_model_ms=tb['validated_decode_model_cycles']*period/1e9,
            v71_composition_model_ms=ta['composition_model_cycles']*period/1e9,
            v72_composition_model_ms=tb['composition_model_cycles']*period/1e9,
            write_command_reduction_percent=100*(a['actual_writes']-b['actual_write_commands'])/a['actual_writes'],
            v71_single_write_data_beats=a['actual_writes'],v72_write_bus_beats=b['actual_write_bus_beats'],
            v72_enabled_word_fraction=b['actual_writes']/b['actual_write_bus_beats']))
    result=dict(status='PASS_EXACT_OUTPUT_COMPARISON',frames=rows,clocks=new['clocks'],shared_source_pins_compared=len(common),
        input_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},script_sha256=sha(Path(__file__).resolve()),
        summary=dict(v71_underruns=old['summary']['total_underruns'],v72_underruns=new['summary']['total_underruns'],new_source_presentations=new['summary']['distinct_complete_presentations']),
        limitations=['decoder-paced key/P pair, not a fixed-arrival 30fps campaign','unequal transaction lengths change background LCD traffic; not normalized read/refresh count or underrun-rate comparison','CPU/HUD execution and live transport not in model time; not validated target sub10ms latency','masked BL8 increases physical write beats despite fewer commands; command savings are not byte-bandwidth savings','no FPGA fit/Fmax/CDC or physical30fps qualification'])
    (AREA/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in rows:print(f"FRAME{r['fid']} v71_ms={r['v71_transaction_model_ms']:.5f} v72_ms={r['v72_transaction_model_ms']:.5f} reduction={r['transaction_cycle_reduction_percent']:.3f}% validated_model_ms={r['v72_validated_decode_model_ms']:.5f} write_commands_reduced={r['write_command_reduction_percent']:.3f}%")
    print('V72_COMPARISON_PASS exact=true zeroLCDunderruns=true physical30fps_proven=false')

if __name__=='__main__':main()
