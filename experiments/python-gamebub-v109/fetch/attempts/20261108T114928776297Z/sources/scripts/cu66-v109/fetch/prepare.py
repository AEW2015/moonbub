#!/usr/bin/env python3
import hashlib,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'fpga/experiments/cu66-v108-capacity/br88_packet_ingress_sync_v91h.sv';OUT=ROOT/'fpga/experiments/cu66-v109-fetch';V=OUT/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert sha(BASE)=='6514a5f2e2c1b597dfb2cddffeb3e637034d5fe79cdb07861ecd1081034c83c6'
 text=BASE.read_text();edits=[]
 def edit(a,b):
  nonlocal text
  assert text.count(a)==1,a;text=text.replace(a,b,1);edits.append(dict(before=a,after=b,expected_occurrences=1))
 edit('    logic [31:0] fetch_base, fetch_address, fetched_word;', '''    logic [31:0] fetch_base, fetch_address, fetched_word;
    // Owned at the existing request edge; private and deliberately unreset.
    logic [31:0] expected_fetch_addr;
    always_ff @(posedge clk)if(state==FETCH_REQ)expected_fetch_addr<=fetch_address;''')
 edit('ram_epoch==context_epoch&&ram_addr==fetch_address&&fetch_kind==F_HEADER;', 'ram_epoch==context_epoch&&ram_addr==expected_fetch_addr&&fetch_kind==F_HEADER;')
 edit('if(ram_epoch!=context_epoch || ram_addr!=fetch_address) fail_packet(4);','if(ram_epoch!=context_epoch || ram_addr!=expected_fetch_addr) fail_packet(4);')
 edit('        assert(!stage_read_rsp || (state==FETCH_WAIT && ram_epoch==context_epoch && ram_addr==fetch_address))', '''        assert(!(state==FETCH_WAIT && stage_read_rsp && ram_epoch==context_epoch) || expected_fetch_addr==fetch_address)
            else $fatal(1,"cached fetch address owner mismatch");
        assert(!stage_read_rsp || (state==FETCH_WAIT && ram_epoch==context_epoch && ram_addr==fetch_address))''')
 p=OUT/BASE.name;p.write_text(text)
 old=BASE.read_text();rebuilt=old
 for e in edits:rebuilt=rebuilt.replace(e['before'],e['after'],1)
 assert rebuilt==text
 for e in reversed(edits):assert rebuilt.count(e['after'])==1;rebuilt=rebuilt.replace(e['after'],e['before'],1)
 assert rebuilt==old
 recipe=dict(schema='v109-fetch-existing-request-edge-v1',status='PREPARED_NOT_RTL_QUALIFIED',public_added_cycles=0,production={BASE.name:dict(original=str(BASE.relative_to(ROOT)),original_sha256=sha(BASE),candidate_sha256=sha(p),edits=edits)})
 (OUT/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
 # Complete production bodies; module identifiers are the only adapter edits.
 adapters=[]
 for variant,source in [('original',BASE),('candidate',p)]:
  a='module br88_packet_ingress_sync_v91h ';b='module ingress_'+variant+' ';body=source.read_text();assert body.count(a)==1;q=V/('ingress_'+variant+'.sv');q.write_text(body.replace(a,b,1));adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(q.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(q),renames=[[a,b]]))
 spec=importlib.util.spec_from_file_location('old_verify',ROOT/'scripts/cu66-v108/capacity/verification.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);ports=mod.ports(BASE.read_text());probe='module ingress_capture_probe (\n'+',\n'.join(' '+x['direction']+' '+x['prefix']+x['name']+x['tail'] for x in ports)
 extras=''' output logic mismatch,verify_capture,verify_capacity_live,
 output logic [31:0] verify_a1,verify_a2,verify_a3,verify_capacity_upper,verify_capacity_lower,verify_expected_addr,
 output logic verify_capacity_wrap,output logic [2:0] verify_threshold_live,
 output logic [5:0] verify_fetch_index'''
 probe+=',\n'+extras+'\n);\n'
 for x in ports:
  if x['direction']=='output':probe+=' '+x['prefix']+'old_'+x['name']+x['tail']+';\n'
 for variant in ('original','candidate'):
  probe+=' ingress_'+variant+' '+('old_dut' if variant=='original' else 'new_dut')+'('+','.join('.'+x['name']+'('+('old_' if variant=='original' and x['direction']=='output' else '')+x['name']+')' for x in ports)+');\n'
 probe+=' assign mismatch=!('+'&&'.join('(old_'+x['name']+'=='+x['name']+')' for x in ports if x['direction']=='output')+');\n'
 for name,expr in dict(capture='prefix_header_capture',a1='plan_align1',a2='plan_align2',a3='plan_align3',capacity_live='capacity_live',threshold_live='threshold_live',capacity_upper='meta_capacity_upper',capacity_lower='meta_capacity_lower',capacity_wrap='meta_capacity_wrap',expected_addr='expected_fetch_addr',fetch_index='fetch_index').items():probe+=' assign verify_'+name+'=new_dut.'+expr+';\n'
 (V/'ingress_capture_probe.sv').write_text(probe+'endmodule\n')
 fixture=ROOT/'fpga/experiments/cu66-v108-capacity/verification/tb_capture.cpp';body=fixture.read_text();needle='  const unsigned start=index-3;';replacement='''  // Synthetic WAIT fixtures describe a prior request at base0+index. This
  // expected address is independent of deliberately foreign ram_addr/epoch.
  NEW(expected_fetch_addr)=uint32_t(index);
  const unsigned start=index-3;''';assert body.count(needle)==1;body=body.replace(needle,replacement,1);(V/'tb_capture.cpp').write_text(body)
 (V/'adapters.json').write_text(json.dumps(dict(schema='v109-fetch-complete-body-adapters-v1',adapters=adapters,all_public_ports_compared=True,fixture_source=str(fixture.relative_to(ROOT)),fixture_source_sha256=sha(fixture),fixture_edits=[[needle,replacement]],fixture_sha256=sha(V/'tb_capture.cpp')),indent=2,sort_keys=True)+'\n')
 print('FETCH_PREPARED',sha(p))
if __name__=='__main__':main()
