"""Qualify only executed original-map address component evidence, not hardware."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/tile-address';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rtl=d/'cu71_tile_memory_address_pipe.sv';wanted=sha(rtl);runs={};metrics={}
for name,mode in [('unit-bound02','unit'),('pins-fast01','pins'),('pins-slow01','pins'),('synth01','synth')]:
    p=d/'evidence'/name;result=json.loads((p/'result.json').read_text());assert result['source_sha256']==wanted and result['mode']==mode
    freeze=json.loads((p/'source-freeze.json').read_text())
    for file,h in freeze['actual_inputs'].items():assert sha(p/file)==h,('Actual input changed',name,file)
    for file,h in freeze['original_sources'].items():assert sha(Path(file))==h,('Original input changed',name,file)
    for item in freeze['derivation']:
        parent=Path(item['parent']);assert sha(parent)==item['parent_sha256']
        derived=p/parent.name;assert sha(derived)==item['candidate_sha256']
        if 'module instance'in item['replacement']:
            assert parent.read_text().replace('cu71_tile_memory tiles(','cu71_tile_memory_address_pipe tiles(')==derived.read_text()
        elif 'slow model'in item['replacement']:
            assert parent.read_text().replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757)','.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768)')==derived.read_text()
        else:raise AssertionError(item)
    execution=json.loads((p/'execution.json').read_text());assert all(x['returncode']==0 for x in execution)
    log=(p/('synthesis.log'if mode=='synth'else'simulation.log')).read_text();assert 'FATAL'not in log and 'ERROR:'not in log
    if mode=='unit':
        marker=next(x for x in log.splitlines()if x.startswith('CU71_TILE_ADDRESS_PASS'))
        m={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',marker)}
        assert m['full_tiles']==48600 and m['physical_words']==777600 and m['checks']==48660 and m['cancellations']==92
        metrics[name]=m
    if mode=='pins':
        marker=next(x for x in log.splitlines()if x.startswith('CU71_MEMORY_RGB_BURST_PASS'))
        m={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',marker)}
        assert m['checks']==5168 and m['aborts']==42 and m['tiles']==235 and m['writes']==14432 and m['reads']==2103
        assert result['slow']==('slow'in name)
        assert sha(p/'model.sv')==sha(r/'fpga/experiments/cu66-v71/memory/evidence/rgb-reference-fast01/model.sv')
        assert sha(p/'cu70_memory_map.svh')==sha(r/'fpga/experiments/cu66-v71/memory/evidence/rgb-reference-fast01/cu70_memory_map.svh')
        assert sha(p/'moonshine_sdram_burst.sv')=='05a9a9471f9c9eb61209c55579b82f9d228cc01328044589eec989b200d6f65a'
        metrics[name]=m
    if mode=='synth':
        lines=(p/'timing.rpt').read_text().splitlines();i=next(i for i,x in enumerate(lines)if x.strip().startswith('WNS(ns)'));values=lines[i+2].split()
        assert float(values[0])>0 and int(values[2])==0
        metrics[name]=dict(setup_WNS_ns=float(values[0]),setup_failing=int(values[2]),hold_WHS_ns=float(values[4]),hold_failing=int(values[6]),part='xc7a100tcsg324-1',clock_ns=10,IO_max_ns=1,IO_min_ns=0,routed=False)
    runs[name]=dict(path=str(p),bindings={n:sha(p/n)for n in('source-freeze.json','execution.json','result.json')})
q=d/'qualification.json';assert not q.exists()
report=dict(status='PASS_ORIGINAL_MAP_COMPONENT_AND_SETUP_ESTIMATE_FULL_BOARD_PENDING',source_sha256=wanted,parent_source=dict(path='fpga/experiments/cu66-v71/memory/cu71_tile_memory.sv',sha256=sha(r/'fpga/experiments/cu66-v71/memory/cu71_tile_memory.sv')),measured_parent_path=dict(report_sha256=sha(r/'fpga/experiments/cu66-v71/board/implementation03/setup-paths.rpt'),setup_ns=-9.606,levels=22,scope='Actual routed upstream command selection/division/address DSP cascade'),runs=runs,metrics=metrics,valid_tile_added_setup_clocks=10,scope='Unit full canonical word-addressed BFM contents and original RTL oracle; separate actual unchanged controller and checked SDRAM pin-model fast/slow component suites. Not full-frame LCD cadence, routed candidate timing or hardware.',tradeoff='100ns added valid-tile setup at100MHz; component suite cycles124922parent→127444candidate. No throughput gain claimed from added latency; goal is removing unschedulable combinational path.',hardware=False,BIT=False,full_board_gate='Required setup/hold/DRC/CDC/route plus integrated key/P/canonical/HUD/LCD regressions remain outstanding.')
q.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],sha(q))
