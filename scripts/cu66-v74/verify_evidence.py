#!/usr/bin/env python3
"""Read-only V74 source, retained-command, memory, display and system evidence audit."""
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v74'
FAIL=[];REPORT=[]
def fail(s): FAIL.append(s)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):
    p=ROOT/rel
    if not p.is_file(): fail(f"required evidence missing: {rel}");return None
    try:return json.loads(p.read_text())
    except Exception as e: fail(f"invalid JSON {rel}: {e}");return None
def check_pins(data,label):
    pins=data.get('source_sha256')
    if not isinstance(pins,dict) or not pins: fail(f"{label}: source_sha256 missing/empty");return 0
    for rel,h in pins.items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts: fail(f"{label}: unsafe source pin {rel}");continue
        p=ROOT/rel
        if not p.is_file():fail(f"{label}: pinned file missing {rel}")
        elif sha(p)!=h:fail(f"{label}: source hash mismatch {rel}")
    return len(pins)
def log_path(result_rel,name):
    p=ROOT/name
    return p if p.is_file() else (ROOT/result_rel).parent/name
def commands(result_rel,data, require=True):
    cs=data.get('commands')
    if not isinstance(cs,list) or (require and not cs):fail(f"{result_rel}: commands missing/empty");return 0
    for i,c in enumerate(cs or []):
        if not isinstance(c,dict):fail(f"{result_rel} command {i}: malformed");continue
        if c.get('exit_code')!=0:fail(f"{result_rel} command {i}: exit_code={c.get('exit_code')}")
        name=c.get('log')
        if not name:fail(f"{result_rel} command {i}: log path missing");continue
        p=log_path(result_rel,name)
        if not p.is_file():fail(f"{result_rel} command {i}: log missing {name}");continue
        if c.get('sha256')!=sha(p):fail(f"{result_rel} command {i}: log hash mismatch {name}");continue
        s=p.read_text(errors='replace')
        if re.search(r'(^|\s)(FAIL|FATAL)(\s|:|$)',s,re.M):fail(f"{result_rel} command {i}: FAIL/FATAL marker {name}")
        argv=c.get('argv',[]);isbuild=('--build'in argv or ('iverilog'in argv and '-o'in argv) or ('-s'in argv and 'yosys'in argv) or 'build'in Path(name).name.lower())
        probe=any(x in Path(name).name.lower() for x in ('version','sha256'))
        if not isbuild and not probe and '/elaboration/' not in result_rel:
            markers=('PASS','SYSTEM_PASS','SYSTEM_CONTROL_PASS','MEMORY_V74_PASS','MEMORY_V74_RESET_PASS','MEMORY_V74_CACHE_PASS','MEMORY_V74_ROWS_PASS','MEMORY_V74_P1WIDE_PASS','CASE_PASS','PASS_UNPLACED_FAMILY_MAPPING')
            if not any(m in s for m in markers):fail(f"{result_rel} command {i}: no runtime PASS marker in {name}")
    return len(cs or [])
def audited(rel,status=None):
    d=read(rel)
    if d is None:return None
    if status and d.get('status')!=status:fail(f"{rel}: status {d.get('status')!r}, expected {status}")
    n=check_pins(d,rel);c=commands(rel,d)
    REPORT.append(f"{rel}: pins={n}, commands={c}")
    return d

def baseline():
    p=subprocess.run([sys.executable,str(ROOT/'scripts/cu66-v74/verify_baseline.py')],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:fail('frozen baseline verifier failed: '+(p.stdout+p.stderr).strip().replace('\n',' | '))
    else:REPORT.append(p.stdout.strip())

def direct_yuv():
    rel='fpga/experiments/cu66-v74/direct-yuv-results.json';d=read(rel)
    if d is None:return
    if d.get('schema')!='cu66-v74-direct-yuv-traffic-v1':fail(f'{rel}: schema mismatch')
    if 'estimate only' not in d.get('scope','').lower() or 'no exact-pixel' not in d.get('scope','').lower():fail(f'{rel}: estimate/exact-pixel scope missing')
    pins=d.get('source_sha256',{});script='scripts/cu66-v74/direct_yuv.py';maprel='fpga/experiments/cu66-v70/memory/memory_map.hpp'
    for name in (script,maprel):
        if name not in pins or not (ROOT/name).is_file() or pins.get(name)!=sha(ROOT/name):fail(f'{rel}: producer/map hash invalid: {name}')
    if d.get('checks',{}).get('physical_address_bounds_pass') is not True:fail(f'{rel}: bounds selfcheck missing')
    for n,total in ((256,860160),(512,805632),(720,518400),(1024,518400)):
        r=d.get('cache_results',{}).get(f'strip8_rolling_lru_{n}',{})
        if r.get('wire_bytes_total')!=total or r.get('stripes')!=90:fail(f'{rel}: strip/cache {n} totals mismatch')
        if any(s.get('wire_bytes')!=s.get('miss_bursts_after_rolling_cache',-1)*16 for s in r.get('stripes_detail',[])):fail(f'{rel}: BL8 accounting mismatch for {n}')
    if d.get('assumptions',{}).get('eight_physical_row_deadline_us',0)<147.4:fail(f'{rel}: incorrect display deadline')
    REPORT.append(f'{rel}: address/cache checks, 90 strips, 16-byte BL8 accounting verified; traffic estimate only')

def display():
    rel='fpga/experiments/cu66-v74/display/results.json';d=audited(rel,'PASS')
    if d is None:return
    if (d.get('total_rasters')!=39 or d.get('total_compared_RGB_words')!=14976000 or d.get('start_rejects')!=30 or d.get('total_fault_probes')!=16):fail(f'{rel}: expected 39 rasters, 14,976,000 compared words, 16 fault probes, 30 start rejects')
    runs=d.get('runs',[])
    if len(runs)!=3 or {r.get('seed') for r in runs}!={0,7201,7202}:fail(f'{rel}: seed/runs incomplete')
    for r in runs:
        cases=[x for x in r.get('per_case',[]) if x.get('mode')==0]
        if len(cases)!=13 or r.get('full_rasters')!=13:fail(f'{rel}: seed {r.get("seed")} lacks 13 complete cases')
        if any((x.get('read_commands'),x.get('read_words'),x.get('write_commands'),x.get('write_words'),x.get('painted'))!=(35040,280320,48000,384000,345600) for x in cases):fail(f'{rel}: painter read/write counter semantics mismatch')

def memory():
    rel='fpga/experiments/cu66-v74/memory/adapters/results.json';d=audited(rel,'PASS')
    if d is None:return
    runs=d.get('runs',[]);caches=d.get('cache_runs',[]);rows=d.get('row_runs',[]);wide=d.get('p1wide_runs',[])
    if len(runs)!=28 or len(caches)!=4 or len(rows)!=8 or len(wide)!=4:fail(f'{rel}: expected run/cache/row/P1wide counts 28/4/8/4')
    for r in runs:
        if r.get('scenario')=='reset':
            if (r.get('probes'),r.get('fresh_bursts'),r.get('fresh_words'))!=(4,4,32):fail(f'{rel}: reset recovery counters mismatch')
        else:
            if (r.get('aborts'),r.get('burst_checks'),r.get('wide_read_checks'),r.get('wide_read_aborts'),r.get('lcd_bursts'),r.get('lcd_words'),r.get('lcd_rejects'))!=(39,23,17,9,250,2000,3):fail(f'{rel}: memory behavioral counts mismatch: {r}')
            # Reconcile the complete nine-field per-client profile and shared cache totals.
            if r.get('p0_hits',-1)+r.get('p0_misses',-1)!=r.get('row_reads',-2):fail(f'{rel}: P0 hit/miss/request identity mismatch')
            if r.get('cache_hits',-1)!=r.get('p0_hits',-2)+r.get('p1_hits',-2) or r.get('cache_misses',-1)!=r.get('p0_misses',-2)+r.get('p1_misses',-2):fail(f'{rel}: global/client cache totals mismatch')
            if r.get('read_wait',-1)>r.get('p0_wait',-2) or r.get('read_service',-1)>r.get('p0_service',-2):fail(f'{rel}: read-only P0 counters exceed total P0 counters')
            if r.get('lcd_line_max',99999)>1842:fail(f'{rel}: LCD line interval exceeds 1842 clocks')
    if any((r.get('checks'),r.get('cache_misses'))!=(19,1) for r in caches):fail(f'{rel}: cache counters mismatch')
    if any((r.get('checks'),r.get('cache_misses'))!=(31,1) for r in wide):fail(f'{rel}: P1 wide counters mismatch')
    if any(r.get('first_tile_misses')!=8 or r.get('second_tile_misses')!=(0 if r.get('cache_lines')==8 else 8) for r in rows):fail(f'{rel}: row cache counters mismatch')
    # Both simulators must produce identical rows for every matched configuration.
    for group,key in ((runs,('tac_ns','seed','scenario')),(caches,('tac_ns',)),(rows,('tac_ns','cache_lines')),(wide,('tac_ns',))):
        pairs={}
        for row in group:pairs.setdefault(tuple(row.get(k) for k in key),[]).append(row)
        for ident,pair in pairs.items():
            if len(pair)!=2 or {x.get('backend') for x in pair}!={'verilator','iverilog'}:fail(f'{rel}: missing matched backend pair {ident}')
            elif any({k:v for k,v in x.items() if k!='backend'}!={k:v for k,v in pair[0].items() if k!='backend'} for x in pair[1:]):fail(f'{rel}: backend mismatch {ident}')

def elaboration():
    rel='fpga/experiments/cu66-v74/memory/elaboration/results.json';d=audited(rel,'PASS_GENERIC_AND_CONVERTED_SIMULATION')
    if d is None:return
    if d.get('schema')!='cu74-frontend-memory-inspection-v1' or not d.get('converted_native_case_counters_identical'):fail(f'{rel}: schema/native-converted counter parity missing')
    if d.get('family_map',{}).get('status')!='PASS_UNPLACED_FAMILY_MAPPING':fail(f'{rel}: family mapping result/scope missing')
    # Reconcile retained generic Yosys report to the structured producer result.
    stat=read('fpga/experiments/cu66-v74/memory/elaboration/stat.json')
    if stat is None or stat.get('design')!=d.get('statistics'):fail(f'{rel}: retained generic stat.json differs from structured statistics')
    net=read('fpga/experiments/cu66-v74/memory/elaboration/netlist.json')
    if net is None or len(net.get('modules',{}))!=1:fail(f'{rel}: retained generic netlist missing expected painter module')
    elif net:
        from collections import Counter
        cells=next(iter(net['modules'].values())).get('cells',{});types=Counter(c.get('type') for c in cells.values())
        if len(cells)!=d.get('statistics',{}).get('num_cells') or dict(types)!=d.get('statistics',{}).get('num_cells_by_type'):fail(f'{rel}: generic netlist cell inventory differs from structured statistics')
        if types.get('$mem_v2')!=len(d.get('memories',[])):fail(f'{rel}: generic netlist collected memory count differs from memory inventory')
    if d.get('logical_memory_bytes')!=23056 or sum(x.get('logical_bits',0) for x in d.get('memories',[]))!=184460 or len(d.get('memories',[]))!=34:fail(f'{rel}: generic data/control memory inventory mismatch')
    # Converted RTL must reproduce native per-case cycles and traffic counters.
    native=read('fpga/experiments/cu66-v74/display/results.json')
    converted=d.get('converted_simulation',[])
    if not native or len(converted)!=3 or len(native.get('runs',[]))!=3:fail(f'{rel}: converted/native run set incomplete')
    else:
        if not d.get('converted_native_case_counters_identical'):fail(f'{rel}: native/converted parity flag false')
        for a,b in zip(native['runs'],converted):
            if a.get('seed')!=b.get('seed') or a.get('per_case')!=b.get('per_case'):fail(f'{rel}: converted/native case counters differ for seed {a.get("seed")}')
        mode0=sum(sum(1 for c in x.get('per_case',[]) if c.get('mode')==0) for x in converted)
        if native.get('total_rasters')!=39 or native.get('total_fault_probes')!=16 or native.get('start_rejects')!=30 or mode0!=39:fail(f'{rel}: native/converted full campaign expected 39/16/30 and 39 converted rasters')
    n=0
    for name,h in d.get('family_map',{}).get('files',{}).items():
        p=ROOT/name;n+=1
        if not p.is_file() or sha(p)!=h:fail(f'{rel}: stale family-map artifact {name}')
    if n!=3:fail(f'{rel}: expected three derived family-map artifacts, found {n}')
    limit=' '.join(d.get('limitations',[])).lower()
    if 'not exact-device fit/placement/routing/fmax/cdc proof' not in limit:fail(f'{rel}: unplaced/no-Fmax limitation missing')
    ooc_rel='fpga/experiments/cu66-v74/build/status.json';ooc=read(ooc_rel)
    if ooc is not None:
        if ooc.get('schema')!='cu74-exact-target-ooc-preflight-v1' or ooc.get('status')!='UNAVAILABLE_EXACT_PART' or ooc.get('exit_code')!=2:fail(f'{ooc_rel}: expected exact-part unavailable status and exit 2')
        sources=ooc.get('hardware_sources',[]);pins=ooc.get('source_sha256',{})
        if len(sources)!=20 or set(sources)!=set(pins):fail(f'{ooc_rel}: expected 20 hardware-only source paths and pins')
        for p,h in pins.items():
            if not (ROOT/p).is_file() or sha(ROOT/p)!=h:fail(f'{ooc_rel}: hardware source hash mismatch {p}')
        if ooc.get('synthesis_started') or ooc.get('implementation_started'):fail(f'{ooc_rel}: OOC preflight unexpectedly started synthesis/implementation')
        for name,h in ooc.get('logs_sha256',{}).items():
            p=ROOT/'fpga/experiments/cu66-v74/build'/name
            if not p.is_file() or sha(p)!=h:fail(f'{ooc_rel}: retained OOC log hash mismatch {name}')
        REPORT.append(f'{ooc_rel}: 20 source pins; exact target unavailable exit=2; no synthesis or implementation')

def control():
    rel='fpga/experiments/cu66-v74/system/control-results.json';d=audited(rel,'PASS')
    if d is None:return
    exp={'actual_keys_parsed':2,'completed_HUD_words':2,'denied_writes':7,'abort_drained':2,'early_HUD_drain_rejected':1,'accepted_frames':0,'actual_writes':2,'actual_reads':2,'refreshes':133,'clocks':99261}
    for k,v in exp.items():
        if d.get('counts',{}).get(k)!=v:fail(f'{rel}: {k} mismatch')
    if not any('30fps' in str(x).lower() for x in d.get('not_proven',[])):fail(f'{rel}: cadence limitation missing')

def system(rel,count):
    d=audited(rel,'PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS')
    if d is None:return
    sm=d.get('summary',{});frames=d.get('frames',[]);timings=d.get('timings',[])
    if d.get('cadence_status')!='NOT_QUALIFIED' or sm.get('physical_fps_proven')!=0 or sm.get('total_underruns')!=0:fail(f'{rel}: cadence/underrun state is not explicit and clean')
    if len(frames)!=count or len(timings)!=count or sm.get('complete_frames')!=count or sm.get('distinct_complete_presentations')!=count:fail(f'{rel}: expected {count} distinct complete frames/timings')
    if any((f.get('actual_writes'),f.get('actual_write_commands'),f.get('actual_write_bus_beats'),f.get('painter_read_commands'),f.get('painter_read_words'),f.get('painter_write_commands'),f.get('painter_write_words'))!=(664320,101520,812160,35040,280320,48000,384000) for f in frames):fail(f'{rel}: V74 transaction/painter counters mismatch')
    for f,t in zip(frames,timings):
        if (f.get('fid'),f.get('generation'))!=(t.get('fid'),t.get('generation')):fail(f'{rel}: frame/timing identity mismatch')
        if not(t.get('packet_complete_cycle',0)<=t.get('admission_cycle',0)<t.get('validated_ready_cycle',0)<t.get('rgb_ready_cycle',0)<=t.get('commit_ack_cycle',0)):fail(f'{rel}: event ordering invalid')
    limits=' '.join(d.get('limitations',[])).lower()
    if 'no physical30fps' not in limits:fail(f'{rel}: no-physical-30fps limitation missing')

def comparison():
    rel='fpga/experiments/cu66-v74/system/comparison.json';d=read(rel)
    if d is None:return
    if d.get('status')!='PASS_EXACT_OUTPUT_COMPARISON':fail(f'{rel}: comparison status mismatch')
    script='scripts/cu66-v74/compare_system.py'
    if d.get('script_sha256')!=sha(ROOT/script):fail(f'{rel}: producer script hash mismatch')
    for path,h in d.get('input_sha256',{}).items():
        if not (ROOT/path).is_file() or sha(ROOT/path)!=h:fail(f'{rel}: source result input hash mismatch {path}')
    full=read('fpga/experiments/cu66-v74/system/full-strip/results.json');hist=read('fpga/experiments/cu66-v74/system/history-4-strip/results.json');old=read('fpga/experiments/cu66-v73/system/full-strip/results.json')
    if not full or not hist or not old:return
    for key,pins,desc in [('shared_frozen_source_pins',(old['source_sha256'],full['source_sha256']),'frozen'),('shared_new_history_source_pins',(full['source_sha256'],hist['source_sha256']),'history')]:
        common=set(pins[0])&set(pins[1]);
        if not common or any(pins[0][p]!=pins[1][p] for p in common) or d.get(key)!=len(common):fail(f'{rel}: {desc} source-pin intersection mismatch')
    if d.get('p0_counter_semantics')!='V73 p0_row_reads carries four useful words per request; V74 carries eight. Both count accepted API calls, not logical rows across versions.':fail(f'{rel}: P0 counter semantics missing')
    for f in d.get('frames',[]):
        a,b=f.get('v73',{}),f.get('v74',{})
        if (a.get('fid'),a.get('key'),a.get('generation'))!=(b.get('fid'),b.get('key'),b.get('generation')):fail(f'{rel}: source identity mismatch')
        if (b.get('actual_write_commands'),b.get('actual_write_bus_beats'),b.get('painter_read_commands'),b.get('painter_read_words'))!=(101520,812160,35040,280320):fail(f'{rel}: V74 comparison counters mismatch')

def main():
    baseline();direct_yuv();display();memory();elaboration();control()
    system('fpga/experiments/cu66-v74/system/full-strip/results.json',2)
    system('fpga/experiments/cu66-v74/system/history-4-strip/results.json',4)
    comparison()
    if FAIL:
        print('V74_EVIDENCE_FAIL');print('\n'.join(' - '+x for x in FAIL));sys.exit(1)
    print('V74_EVIDENCE_INTEGRITY_AND_SCOPE_PASS')
    print('\n'.join(REPORT))
if __name__=='__main__':main()
