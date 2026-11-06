#!/usr/bin/env python3
"""QM87 cross-language grammar and actual receiver retain/recover checks."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import uuid
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v87/quantizers'
CONTAINER='gamebub-cu66-v69-build'


def load(path):
    spec=importlib.util.spec_from_file_location('q87_test_codec',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(method, values, needed, body):
    prefix=struct.pack('>4sBBHHH',b'QM87',1,method,1350,len(body),needed)
    raw=prefix+body
    return raw+struct.pack('>I',zlib.crc32(raw))


def crc(raw):
    return bytes(raw[:-4])+struct.pack('>I',zlib.crc32(raw[:-4]))


def packet_q(packet, newblock):
    begin=128+int.from_bytes(packet[36:40],'big')
    oldsize=int.from_bytes(packet[40:44],'big')
    raw=bytearray(packet[:begin]+newblock+packet[begin+oldsize:])
    struct.pack_into('>I',raw,40,len(newblock))
    return crc(raw)


def main():
    codec=load(ROOT/'scripts/cu66-v87/quantizer_codec.py')
    full=json.loads((AREA/'results.json').read_text())
    qualified=ROOT/full['selected_report'];run=qualified.parent
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'test-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    report=dict(schema='cu66-v87-quantizer-tests-v1',status='FAIL',checks=[],commands=[],
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'scripts/cu66-v87/quantizer_codec.py',AREA/'receiver.cpp',qualified]},
                scope='Actual native quantizer grammar plus synchronous rejection/retention/recovery; no asynchronous hardware drain or timing proof.')
    source=(AREA/'receiver.cpp').read_text().split('static bool read32')[0]
    source=source.replace('#include "../../cu66-native-v69/decoder.hpp"','#include "'+str(ROOT/'experiments/cu66-native-v69/decoder.hpp')+'"')
    source+=r'''
int main() { unsigned n=0;while(std::cin>>n) {
  unsigned method,count;std::string qhex,ophex,prevhex;std::cin>>method>>count>>qhex>>ophex>>prevhex;
  auto unhex=[](const std::string &s) {Bytes out;for(size_t i=0;i<s.size();i+=2)out.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));return out;};
  try {
    auto q=unhex(qhex),ops=unhex(ophex);std::array<unsigned,1350> prev{};bool have=prevhex!="-";
    if(have) {auto bytes=unhex(prevhex);need(bytes.size()==1350,"test prev shape");for(unsigned i=0;i<1350;++i)prev[i]=bytes[i];}
    auto values=quantizers(q,ops,have?&prev:nullptr);Bytes raw;for(auto value:values)raw.push_back(uint8_t(value));
    std::cout<<"{\"accepted\":true,\"sha256\":\""<<hex(sha256(raw))<<"\"}"<<std::endl;
  }catch(const std::exception &e) {std::cout<<"{\"accepted\":false,\"error\":\""<<e.what()<<"\"}"<<std::endl;}
}}
'''
    harness=out/'parser-test.cpp';harness.write_text(source)
    binary='/build/v87-quantizer-parser-'+stamp
    command=['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Wno-unused-function',str(harness),'-o',binary]
    result=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr)
    report['commands'].append(dict(argv=command,observed_exit_code=result.returncode));assert result.returncode==0,result.stderr
    process=subprocess.Popen(['docker','exec','-i',CONTAINER,binary],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    ops=[1]*8100
    # Independent explicit Y4/U1/V1 cell membership, not encoder helper output.
    wanted=[0,44,45,674,1349]
    for cell in wanted:
        row,col=divmod(cell,45)
        for t in ((row*2)*90+col*2,(row*2)*90+col*2+1,(row*2+1)*90+col*2,(row*2+1)*90+col*2+1,5400+cell,6750+cell):
            ops[t]=2
    assert codec.needed_cells(ops)==[i in wanted for i in range(1350)]
    report['checks'].append(dict(name='independent_Y4_U1_V1_needed_cell_geometry',status='PASS'))
    values=[(i//100)%3 for i in range(1350)]
    active=[values[i] for i in wanted]
    methods=[(0,codec.packed(values),values),(1,b'\x02',[2]*1350),(2,codec.runs(values),values),
             (3,b'\x01',[1 if i in wanted else 0 for i in range(1350)]),
             (4,codec.packed(active),[values[i] if i in wanted else 0 for i in range(1350)]),
             (5,codec.runs(active),[values[i] if i in wanted else 0 for i in range(1350)]),(6,b'',values)]
    good=[]
    def check(name,q,previous,expected=None):
        try:
            decoded=codec.decode(q,ops,previous)
            python_accepted=True
        except ValueError:
            python_accepted=False
        process.stdin.write(f"1 0 0 {q.hex()} {bytes(ops).hex()} {bytes(previous).hex() if previous is not None else '-'}\n");process.stdin.flush()
        response=json.loads(process.stdout.readline())
        assert response['accepted']==python_accepted==(expected is not None),(name,response,python_accepted)
        if expected is not None:
            assert decoded==expected
            assert response['sha256']==hashlib.sha256(bytes(expected)).hexdigest()
        report['checks'].append(dict(name=name,status='PASS_ACCEPT_PARITY' if expected is not None else 'PASS_REJECT_BOTH',native=response,block_sha256=hashlib.sha256(q).hexdigest()))
    for method,body,expected in methods:
        q=block(method,values,len(wanted),body);good.append(q)
        check(f'method_{method}',q,values if method==6 else None,expected)
    # All 1350 individual chroma cells and 5400 luma tiles map to correct cells.
    for t in range(8100):
        single=[1]*8100;single[t]=2
        if t<5400:
            row,col=divmod(t,90);expected_cell=(row//2)*45+col//2
        else:expected_cell=(t-5400)%1350
        assert codec.needed_cells(single)==[i==expected_cell for i in range(1350)]
    report['checks'].append(dict(name='all_8100_individual_tile_to_cell_mappings',status='PASS'))
    malformed=[]
    def changed(q,offset,value):
        raw=bytearray(q);raw[offset]=value;return crc(raw)
    malformed += [('magic',changed(good[0],0,0),None),('version',changed(good[0],4,2),None),('method',changed(good[0],5,7),None),
                  ('cell_count',changed(good[0],7,0),None),('required_count',changed(good[0],11,6),None),
                  ('raw_reserved',changed(good[0],12,0xc0),None),('raw_padding',changed(good[0],349,1),None),
                  ('uniform_reserved',changed(good[1],12,3),None),('run_reserved',changed(good[2],12,0xff),None),
                  ('run_underrun',block(2,values,5,b'\x00'),None),('run_overrun',block(5,values,5,b'\x05'),None),
                  ('needed_padding',changed(good[4],13,1),None),('missing_inheritance',good[6],None),
                  ('inherit_payload',block(6,values,5,b'\x00'),values),('truncated',good[0][:-1],None)]
    badcrc=bytearray(good[0]);badcrc[-1]^=1;malformed.append(('crc',bytes(badcrc),None))
    for name,q,prev in malformed:check(name,q,prev)
    process.stdin.close();assert process.wait()==0
    report['parser_exit_code']=process.returncode
    (out/'parser.stderr').write_text(process.stderr.read())
    # Whole receiver tests: each invalid delta is followed by the valid delta
    # and its exact replay in the same process; compare prior qualified digests.
    key=(run/'c0-f0-copy_group_cap65536.cs87').read_bytes()
    delta=(run/'c0-f1-copy_group_cap65536.cs87').read_bytes()
    begin=128+int.from_bytes(delta[36:40],'big');n=int.from_bytes(delta[40:44],'big')
    inherited=delta[begin:begin+n]
    native_cases=[]
    for name,offset,value in [('q_magic',0,0),('q_version',4,2),('q_method',5,7),('q_cells',7,0),('q_required',11,0)]:
        native_cases.append((name,packet_q(delta,changed(inherited,offset,value))))
    native_cases.append(('q_crc',packet_q(delta,bytes(bytearray(inherited[:-1])+bytes([inherited[-1]^1])))))
    # A syntactically valid all-zero map changes required scales and must fail
    # the reconstructed content commitment rather than publishing it.
    needed=int.from_bytes(inherited[10:12],'big')
    native_cases.append(('valid_wrong_quantizers_late_content_reject',packet_q(delta,block(1,values,needed,b'\x00'))))
    legacy=bytearray(delta);legacy[:4]=b'CS86';native_cases.append(('CS86_explicit_profile_reject',crc(legacy)))
    for name,bad in native_cases:
        p=subprocess.Popen(['docker','exec','-i',CONTAINER,full['binary']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        def receive(packet):
            p.stdin.write(struct.pack('>II',0,len(packet))+packet);p.stdin.flush();return json.loads(p.stdout.readline())
        accepted=receive(key);rejected=receive(bad);recovered=receive(delta);replayed=receive(delta)
        assert accepted['accepted'] and not rejected['accepted'] and rejected['retained_fid']==0,(name,rejected)
        if name=='valid_wrong_quantizers_late_content_reject':
            assert rejected['error']=='CS87 reconstructed content root'
        assert recovered['accepted'] and recovered['fid']==1 and not recovered['replayed']
        assert replayed==dict(recovered,replayed=True)
        p.stdin.close();assert p.wait()==0
        report['checks'].append(dict(name=name,status='PASS_NATIVE_REJECT_RETAIN_RECOVER_REPLAY',rejected=rejected,
                                     recovery_sha256=hashlib.sha256(json.dumps(recovered,sort_keys=True).encode()).hexdigest(),observed_exit_code=p.returncode))
    # Force every nonuniform stateless representation through actual pixels.
    # Start each from the same accepted key; never reuse a generated packet as
    # an oracle for a different previous quantizer-cache branch.
    spec=importlib.util.spec_from_file_location('q87_native_masks',ROOT/'experiments/python-gamebub-v82/native/data.py')
    native_data=importlib.util.module_from_spec(spec);spec.loader.exec_module(native_data)
    originals=[]
    for frame in native_data.iter_frames():
        originals.append(frame)
        if len(originals)==3:break
    spec=importlib.util.spec_from_file_location('q87_map_parser',ROOT/'scripts/cu66-v86/prototype_maps.py')
    map_parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(map_parser)
    mode_len=int.from_bytes(delta[36:40],'big')
    actual_ops=map_parser.decode_body(delta[7],delta[128:128+mode_len],originals[1]['hidden_mask'],key=False)
    kb=128+int.from_bytes(key[36:40],'big');kn=int.from_bytes(key[40:44],'big')
    key_ops=[1 if h else 2 for h in originals[0]['hidden_mask']]
    actual_values=codec.decode(key[kb:kb+kn],key_ops)
    required=codec.needed_cells(actual_ops);selected_values=[v for v,n in zip(actual_values,required) if n]
    expected_rows={(r['configuration'],r['cohort'],r['fid']):r for r in map(json.loads,(run/'frames.jsonl').read_text().splitlines())}
    for method,body in [(0,codec.packed(actual_values)),(2,codec.runs(actual_values)),
                        (4,codec.packed(selected_values)),(5,codec.runs(selected_values))]:
        q=block(method,actual_values,sum(required),body)
        assert len(q)<=354
        candidate=packet_q(delta,q)
        p=subprocess.Popen(['docker','exec','-i',CONTAINER,full['binary']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        def receive(packet):
            p.stdin.write(struct.pack('>II',0,len(packet))+packet);p.stdin.flush();return json.loads(p.stdout.readline())
        assert receive(key)['accepted']
        decoded=receive(candidate)
        assert decoded['accepted'],(method,decoded)
        expected=expected_rows[('copy_group_cap65536',0,1)]['decoded']
        assert all(decoded[k]==expected[k] for k in ('canonical_sha256','coefficient_sha256','hud_sha256','display_sha256','root','seal'))
        assert receive(candidate)==dict(decoded,replayed=True)
        # Recompute frame2's encoding from the actually accepted branch cache.
        # Required-only methods may intentionally zero irrelevant previous cells.
        scales=codec.decode(q,actual_ops,actual_values)
        next_packet=(run/'c0-f2-copy_group_cap65536.cs87').read_bytes()
        ml=int.from_bytes(next_packet[36:40],'big')
        next_ops=map_parser.decode_body(next_packet[7],next_packet[128:128+ml],originals[2]['hidden_mask'],key=False)
        next_block=codec.encode(actual_values,next_ops,scales)
        next_decoded=receive(packet_q(next_packet,next_block))
        assert next_decoded['accepted'],next_decoded
        expected_next=expected_rows[('copy_group_cap65536',0,2)]['decoded']
        assert all(next_decoded[k]==expected_next[k] for k in ('canonical_sha256','coefficient_sha256','hud_sha256','display_sha256','root','seal'))
        p.stdin.close();assert p.wait()==0
        report['checks'].append(dict(name=f'forced_method_{method}_pixels_replay_then_cache_branch',status='PASS_NATIVE_PARITY_AND_NEXT_FRAME',
                                     q_block_bytes=len(q),next_q_method=next_block[5],packet_sha256=hashlib.sha256(candidate).hexdigest(),observed_exit_code=p.returncode))
    report.update(status='PASS_CROSS_LANGUAGE_QUANTIZER_AND_NATIVE_RECOVERY',checks_count=len(report['checks']),
                  source_after_run_sha256={p:sha(ROOT/p) for p in report['source_sha256']})
    assert report['source_after_run_sha256']==report['source_sha256']
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (AREA/'tests.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print(report['status'],len(report['checks']),out/'results.json')


if __name__=='__main__':main()
