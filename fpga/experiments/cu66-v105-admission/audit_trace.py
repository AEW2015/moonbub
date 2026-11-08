#!/usr/bin/env python3
"""Offline independent packet/Cartesian-coordinate replay of retained V105 evidence."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v105/admission'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hidden(plane,tile):
    if plane:return 1046<=tile<=1064
    return any(first<=tile<=last for first,last in ((633,651),(723,741),(993,1011),(1083,1101),
        (4071,4110),(4161,4200),(4251,4290),(4431,4460),(4521,4550)))


def packet_coordinates(packet):
    """Independent grouped-map parsing; returns ordered residual tile coordinates."""
    key=packet[5]==1
    data=packet[128:128+int.from_bytes(packet[36:40],'big')]
    bit_index=0
    def bit():
        nonlocal bit_index
        assert bit_index<len(data)*8
        value=(data[bit_index//8]>>(7-bit_index%8))&1
        bit_index+=1
        return value
    coords=[]
    for plane,size in enumerate((5400,1350,1350)):
        if key:
            coords.extend((plane,tile) for tile in range(size) if not hidden(plane,tile))
            continue
        for start in range(0,size,16):
            tag=(bit()<<1)|bit()
            visible=[t for t in range(start,min(size,start+16)) if not hidden(plane,t)]
            if not visible:assert tag==3;continue
            assert tag!=3
            modes=[tag]*len(visible) if tag<2 else [bit() for _ in visible]
            if tag==2:assert any(modes) and not all(modes)
            coords.extend((plane,tile) for tile,value in zip(visible,modes) if value)
    if key:assert not data
    else:
        assert (bit_index+7)//8==len(data)
        while bit_index<len(data)*8:assert bit()==0
    return coords


def main():
    summary_path=AREA/'results.json';summary=json.loads(summary_path.read_text())
    receipt_path=ROOT/summary['selected_report'];receipt=json.loads(receipt_path.read_text())
    assert summary['status']==receipt['status']=='PASS'
    assert {k:v for k,v in summary.items() if k!='selected_report'}==receipt
    assert receipt['actual_RTL_run'] and receipt['strict_warnings'] and not receipt['assertions_disabled_or_downgraded']
    for path,pin in receipt['source_sha256'].items():assert sha(ROOT/path)==pin,('source',path)
    for path,pin in receipt['artifacts_sha256'].items():assert sha(receipt_path.parent/path)==pin,('artifact',path)
    verdict=receipt['terminal_verdict']
    assert verdict['status']=='TEST_PASS' and (verdict['cases'],verdict['positive_cases'],verdict['negative_cases'],verdict['directed_checks'])==(86,52,34,22)
    assert len(set(verdict['directed_check_names']))==22
    assert verdict['cache_noise_edges']>5_000_000 and verdict['lookup_response_edges']>500_000
    compile_command=next(x['argv'] for x in receipt['commands'] if '--cc' in x['argv'])
    assert '--assert' in compile_command and '-Wall' in compile_command
    assert '-std=c++17 -O2 -Wall -Wextra -Werror' in compile_command
    assert compile_command[compile_command.index('-j')+1]=='2'
    assert '%Warning-' not in (receipt_path.parent/'compile.log').read_text()
    assert 'Verilator 5.020' in (receipt_path.parent/'verilator.log').read_text()
    vector_path=receipt_path.parent/'sources/experiments/python-gamebub-v91i/vectors/vectors.txt'
    expected={}
    for line in vector_path.read_text().splitlines():
        row=line.split()
        if int(row[1])==0:expected[row[0]]=packet_coordinates(bytes.fromhex(row[2]))
    assert len(expected)==52
    trace=receipt_path.parent/'trace.jsonl.gz';raw_hasher=hashlib.sha256()
    rows=marks=active_bits=sentinels=jumps=0;case=None;at=0;active=set();previous=None
    passed=set();planes=set();columns=set();row_pairs=set();last_clock=-1
    with gzip.open(trace,'rb') as stream:
        for line in stream:
            raw_hasher.update(line);r=json.loads(line)
            if 'begin' in r:
                case=r['begin'];at=0;active=set();previous=None;continue
            assert r['clock']>last_clock;last_clock=r['clock'];rows+=1
            if r['kill']:
                active=set();at=0;previous=None;continue
            if r['valid']:
                plane,tile=r['plane'],r['tile'];limit=5400 if plane==0 else 1350
                assert plane in (0,1,2) and 0<=tile<=limit
                row,column=divmod(tile,90) if plane==0 else (0,0)
                cell=(row//2)*45+column//2 if plane==0 else tile
                assert (r['cell'],r['column'],r['odd'],r['base'])==(cell,column,row%2,(row//2)*45 if plane==0 else 0)
                planes.add(plane)
                if plane==0 and tile<limit:columns.add(column);row_pairs.add(row//2)
                sentinels+=tile==limit
                if previous and previous['plane']==plane and tile>previous['tile']+1:jumps+=1
                previous=r
                if r['residual']:
                    assert tile<limit and cell<1350
                    active.add(cell);marks+=1
                    if case in expected:
                        assert (plane,tile)==expected[case][at],(case,at,plane,tile);at+=1
            if r['state']==13:
                index=r['active_index']
                if index<1350:assert r['active']==int(index in active);active_bits+=1
                if case in expected:
                    assert at==len(expected[case]);passed.add(case)
    assert raw_hasher.hexdigest()==receipt['raw_trace_sha256']
    got=dict(rows=rows,residual_marks=marks,active_bits_compared=active_bits,end_sentinels=sentinels,
        group_jumps=jumps,positive_packet_mode_oracles=len(passed))
    assert all(receipt['trace_replay'][key]==value for key,value in got.items())
    assert marks==verdict['residual_marks'] and passed==set(expected)
    assert planes=={0,1,2} and columns==set(range(90)) and row_pairs==set(range(30))
    result=dict(schema='v105-admission-independent-clocked-trace-audit-v1',status='PASS',
        selected_receipt=dict(path=str(receipt_path.relative_to(ROOT)),sha256=sha(receipt_path)),
        selected_summary=dict(path=str(summary_path.relative_to(ROOT)),sha256=sha(summary_path)),
        auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),
        trace_sha256=sha(trace),raw_trace_sha256=raw_hasher.hexdigest(),clock_edges=verdict['clock_edges'],
        planes=sorted(planes),Y_columns=len(columns),Y_row_pairs=len(row_pairs),**got,
        limits=['Reachable clocked behavioral evidence; not formal arbitrary internal-state equivalence.',
                'No native timing, achieved hardware FPS or complete validated latency claim.'])
    (AREA/'trace-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('V105_ADMISSION_TRACE_AUDIT PASS',rows,marks,active_bits)


if __name__=='__main__':main()
