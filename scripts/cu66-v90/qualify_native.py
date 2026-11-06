#!/usr/bin/env python3
"""Native qualification of full proxy histories and exact-four-source overrides."""
import datetime,hashlib,importlib.util,json,struct,subprocess,sys,time,uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v90/native'
CONTAINER='gamebub-cu66-v69-build'
POLICIES=('proxy_LOW','proxy_HIGH','exact4_else_proxy_LOW','exact4_else_proxy_HIGH')


def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    wire=load('v90_native_packet_producer',ROOT/'scripts/cu66-v88/run_wire.py')
    original=load('v90_native_original',ROOT/'experiments/python-gamebub-v82/native/data.py')
    data=load('v90_native_components',ROOT/'experiments/python-gamebub-v88/entropy/data.py')
    oldwire=load('v90_native_oldwire',ROOT/'scripts/cu66-v86/run_wire.py')
    qcodec=load('v90_native_qcodec',ROOT/'scripts/cu66-v87/quantizer_codec.py')
    oldmap=load('v90_native_oldmap',ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
    groupmap=load('v90_native_groupmap',ROOT/'scripts/cu66-v86/prototype_maps.py')
    selected=json.loads((ROOT/'experiments/python-gamebub-v90/policy/results.json').read_text());pp=ROOT/selected['selected_report']
    proxies={(r['cohort'],r['fid'],r['cost']):r for r in map(json.loads,pp.with_name('selections.jsonl').read_text().splitlines())};assert len(proxies)==914
    op=ROOT/'experiments/python-gamebub-v90/exact/oracle-selections.json';oracle_report=json.loads(op.read_text())
    oracles={(r['cohort'],r['fid'],r['cost']):r for r in oracle_report['choices']};assert len(oracles)==8
    prior=json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text());wp=ROOT/prior['selected_report']
    ground={(r['cohort'],r['fid']):r for r in map(json.loads,wp.with_name('frames.jsonl').read_text().splitlines()) if r['policy']=='AB38_control'}
    commitments={(r['cohort'],r['fid']):r for r in map(json.loads,oldwire.C2_CONTROL.read_text().splitlines())}
    receiver=ROOT/'experiments/python-gamebub-v88/wire/receiver.cpp'
    sources=[Path(__file__).resolve(),ROOT/'scripts/cu66-v88/run_wire.py',receiver,ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp',ROOT/'experiments/python-gamebub-v88/entropy/data.py',ROOT/'experiments/python-gamebub-v88/entropy/index.json',
             ROOT/'experiments/python-gamebub-v90/policy/results.json',pp,pp.with_name('selections.jsonl'),op,ROOT/oracle_report['source_report'],wp,wp.with_name('frames.jsonl'),ROOT/'scripts/cu66-v87/quantizer_codec.py',oldwire.C2_CONTROL]
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'));pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    assert sha(ROOT/oracle_report['source_report'])==oracle_report['source_report_sha256']
    report=dict(schema='cu66-v90-native-selections-v1',status='FAIL',source_sha256=pins,commands=[],policies=list(POLICIES),
                scope=['Existing qualified CS88 format and unchanged quantized pixels. Four native histories on457content sources.',
                       'Proxy selections qualify full457. Exact oracle overrides only four modeled sources; elsewhere these two histories fall back to proxy.',
                       'Native calls and exact repeats do not add distinct gameplay or prove hardware timing.'])
    binary='/build/v90-native-'+stamp;processes={};qcache={};rows=[];started=time.monotonic()
    try:
        cmd=['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(receiver),'-o',binary]
        result=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr)
        report['commands'].append(dict(argv=cmd,observed_exit_code=result.returncode));assert result.returncode==0,result.stderr
        cmd=['docker','cp',CONTAINER+':'+binary,str(out/'receiver.bin')];result=subprocess.run(cmd,capture_output=True,text=True)
        report['commands'].append(dict(argv=cmd,observed_exit_code=result.returncode));assert result.returncode==0
        for name in POLICIES:
            log=(out/(name+'.stderr')).open('wb');cmd=['docker','exec','-i',CONTAINER,binary]
            report['commands'].append(dict(argv=cmd));processes[name]=(subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log),log)
        with (out/'frames.jsonl').open('w') as stream:
            for i,(frame,native) in enumerate(zip(data.iter_frames(),original.iter_frames(),strict=True)):
                key=(frame['cohort'],frame['fid']);assert key==(native['cohort'],native['fid'])
                ops=[1 if h else 0 if not frame['key'] and frame['zero_mask'][t]=='1' else 2 for t,h in enumerate(native['hidden_mask'])]
                old=None if frame['key'] else qcache.get(frame['cohort']);values=qcodec.unpacked(frame['qmap'],1350)
                block=qcodec.encode(values,ops,old);qcache[frame['cohort']]=qcodec.decode(block,ops,old)
                options={c['mask']:c for c in wire.candidates(frame,native,commitments[key],block,oldwire,oldmap,groupmap)}
                for name in POLICIES:
                    cost='LOW' if name.endswith('LOW') else 'HIGH';lookup=(*key,cost)
                    use_oracle=name.startswith('exact4_') and lookup in oracles
                    chosen=oracles[lookup] if use_oracle else proxies[lookup]
                    packet=options[chosen['mask']]['packet'];assert len(packet)==chosen['wire_bytes']<=49152
                    assert hashlib.sha256(packet).hexdigest()==chosen['packet_sha256']
                    p=processes[name][0];p.stdin.write(struct.pack('>II',frame['cohort'],len(packet))+packet);p.stdin.flush()
                    decoded=json.loads(p.stdout.readline());assert decoded['accepted'] and not decoded['replayed'],decoded
                    for field in ('canonical_sha256','coefficient_sha256','hud_sha256','display_sha256','root','seal','generation','fid'):
                        assert decoded[field]==ground[key]['decoded'][field],(key,name,field)
                    assert decoded['wire_bytes']==len(packet)
                    # Exact accepted bytes must replay without a different cache branch.
                    p.stdin.write(struct.pack('>II',frame['cohort'],len(packet))+packet);p.stdin.flush();replay=json.loads(p.stdout.readline())
                    assert replay==dict(decoded,replayed=True)
                    row=dict(policy=name,cohort=frame['cohort'],fid=frame['fid'],cost=cost,mask=chosen['mask'],oracle_override=use_oracle,
                             packet_sha256=chosen['packet_sha256'],wire_bytes=len(packet),decoded=decoded,replayed=True)
                    stream.write(json.dumps(row,separators=(',',':'))+'\n');rows.append(row)
                    if key in {(0,0),(0,1),(0,3),(3,50)}:(out/f'c{key[0]}-f{key[1]}-{name}.cs88').write_bytes(packet)
                if i%50==0:print('V90_NATIVE_PROGRESS',i+1,flush=True)
        exits={}
        for name,(p,log) in processes.items():p.stdin.close();exits[name]=p.wait();log.close();assert exits[name]==0
        assert len(rows)==1828 and pins=={p:sha(ROOT/p) for p in pins}
        report.update(status='PASS_NATIVE_SELECTIONS_AND_EXACT_REPLAY',native_sources=457,new_packet_calls=1828,exact_replay_calls=1828,receiver_exit_codes=exits,
                      oracle_override_calls=sum(r['oracle_override'] for r in rows),selected_bytes={name:sum(r['wire_bytes'] for r in rows if r['policy']==name) for name in POLICIES})
    finally:
        for p,log in processes.values():
            if p.poll() is None:p.terminate();p.wait()
            if not log.closed:log.close()
        report['wall_seconds']=time.monotonic()-started;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('V90_NATIVE_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':main()
