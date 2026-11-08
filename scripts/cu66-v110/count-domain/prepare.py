#!/usr/bin/env python3
"""Prepare the narrow caller-validated AC start-bound specialization and exact adapters."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-count-domain';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v110/count-domain'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 production={}
 for name,base,edits in [
 ('br88_context.sv','fpga/experiments/cu66-v106-context/br88_context.sv',[
 ('module br88_context (',"module br88_context #(\n    parameter bit PREVALIDATED_EVENT_COUNT=1'b0\n) ("),
 ('k0>19 || k1>11 || event_count>start_limit','k0>19 || k1>11 || (!PREVALIDATED_EVENT_COUNT && event_count>start_limit)')]),
 ('br88_packet_ingress_sync_v91h.sv','fpga/experiments/cu66-v109-request/br88_packet_ingress_sync_v91h.sv',[
 ('    br88_context context_decoder (',"    br88_context #(.PREVALIDATED_EVENT_COUNT(1'b1)) context_decoder ("),
 ('`ifndef SYNTHESIS\n    function automatic logic [31:0] capacity_expected_upper', '''`ifndef SYNTHESIS
    // Independent mathematical caller contract, evaluated only on actual start.
    // No threshold cache or context start_limit is used as the expected value.
    always_ff @(posedge clk)if(state==CONTEXT_START && !cancelled)begin
        assert(context_blocks!=0 && context_blocks<=17'd65536)
            else $fatal(1,"prevalidated context block domain");
        if(band==0)
            assert({32'd0,counts[band]}=={47'd0,context_blocks})
                else $fatal(1,"prevalidated DC count relation");
        else
            assert({32'd0,counts[band]} <= {47'd0,context_blocks} *
                (band==1 ? 64'd5 : band==2 ? 64'd15 : 64'd43))
                else $fatal(1,"prevalidated AC count relation");
    end
    function automatic logic [31:0] capacity_expected_upper''')])]:
  old=ROOT/base;text=old.read_text();record=[]
  for a,b in edits:assert text.count(a)==1;text=text.replace(a,b,1);record.append(dict(before=a,after=b,expected_occurrences=1))
  new=SRC/name;new.write_text(text);production[name]=dict(original=base,original_sha256=sha(old),candidate=str(new.relative_to(ROOT)),candidate_sha256=sha(new),edits=record)
 assert production['br88_context.sv']['original_sha256']=='9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277'
 assert production['br88_packet_ingress_sync_v91h.sv']['original_sha256']=='ac7260e749ace036495a162882fdb30fdb129d2c7ddde8df67bc2a8957f8f4b1'
 write(SRC/'edit-recipe.json',dict(schema='v110-count-domain-caller-specialization-v1',added_public_cycles=0,production=production,precondition='Specialization enabled only for validated synchronous ingress; on actual consumed start AC event_count<=blocks*band_width; generic default false retains original unconditional validation.',remaining_product='limit<=start_limit and WAIT_RUN position bound/error6 unchanged',all_original_assertions_retained=True))
 adapters=[]
 def adapt(source,name,edits):
  text=source.read_text()
  for a,b in edits:assert text.count(a)==1;text=text.replace(a,b,1)
  dest=V/name;dest.write_text(text);adapters.append(dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),path=str(dest.relative_to(ROOT)),sha256=sha(dest),renames=edits))
 oldctx=ROOT/'fpga/experiments/cu66-v106-context/br88_context.sv';a=json.loads((oldctx.parent/'adapter.json').read_text())
 for variant,source in [('original',oldctx),('candidate',SRC/'br88_context.sv')]:
  adapt(source,'context_'+variant+'.sv',[('module br88_context','module context_'+variant),('\n);',a['extra_ports']),('\nendmodule',a['assignments']+'\nendmodule')])
 oldprobe=oldctx.parent/'context_probe.sv';probe=oldprobe.read_text();probe_edits=[]
 def pe(a,b):
  nonlocal probe
  assert probe.count(a)==1;probe=probe.replace(a,b,1);probe_edits.append([a,b])
 ports=json.loads((oldctx.parent/'ports.json').read_text());outs=[p for p in ports if p['direction']=='output'];ins=[p for p in ports if p['direction']=='input']
 pe('    output logic mismatch,','    output logic mismatch,\n    output logic specialized_owner_domain, specialized_mismatch,')
 decl='\n'.join('    logic '+('signed 'if p['signed']else '')+(p['width']+' 'if p['width']else '')+'special_'+p['name']+';'for p in outs)+'\n    logic [15:0] special_sparse_block;logic [5:0] special_sparse_index;\n'
 decl+='''    logic start_count_precondition;
    assign start_count_precondition=band==0 || band>3 ||
        ({32'd0,event_count} <= {47'd0,blocks} * (band==1 ? 64'd5 : band==2 ? 64'd15 : 64'd43));
    always_ff @(posedge clk)
        if(reset || abort_context)specialized_owner_domain<=1;
        else if(start)specialized_owner_domain<=start_count_precondition;
'''
 instance='    context_candidate #(.PREVALIDATED_EVENT_COUNT(1\'b1)) specialized (\n'+',\n'.join('        .'+p['name']+'('+('special_'+p['name'] if p['direction']=='output'else p['name'])+')'for p in ports)+',\n        .verify_sparse_block(special_sparse_block),.verify_sparse_index(special_sparse_index));\n'
 comp=' ||\n        '.join('special_'+p['name']+'!=original_'+p['name']for p in outs)+' || special_sparse_block!=original_sparse_block || special_sparse_index!=original_sparse_index'
 pe('    assign verify_original_geometry=',decl+instance+'    assign specialized_mismatch=specialized_owner_domain && ('+comp+');\n    assign verify_original_geometry=')
 pe('        mismatch=original_sparse_block','        mismatch=specialized_mismatch || original_sparse_block')
 (V/'context_probe.sv').write_text(probe)
 # Keep original full context/geometry/golden fixture verbatim, append a separate start-domain extension.
 oldtb=oldctx.parent/'tb_context.cpp';(V/'inherited_context.cpp').write_text(oldtb.read_text().replace('int main(','int inherited_context_main(',1))
 (V/'tb_count_domain.cpp').write_text('''#include "inherited_context.cpp"
static void domain_starts(unsigned seed) {
 Sim s(seed);unsigned cases=0,enabled=0,excluded=0;
 const std::array<unsigned,16> blocks={0,1,2,3,7,255,256,1023,1024,32767,32768,65534,65535,65536,65537,131071};
 for(bool serial:{false,true})for(bool word16:{false,true})for(unsigned b:blocks)for(unsigned band=0;band<6;++band) {
  const uint64_t width=band==1?5:band==2?15:band==3?43:1,lim=uint64_t(b)*width;
  std::vector<uint32_t> counts={0,1,uint32_t(lim?lim-1:0),uint32_t(lim),uint32_t(lim+1),0x80000000U,0xffffffffU};
  for(uint32_t count:counts)for(unsigned bad=0;bad<3;++bad) {
   Case c;c.id="domain-start";c.blocks=b;c.band=band;c.events=count;c.k0=bad==1?255:0;c.k1=band==0?255:bad==2?255:0;
   s.start(c,word16,serial,0x99112233);const bool domain=band==0||band>3||uint64_t(count)<=lim;
   require(bool(s.d.specialized_owner_domain)==domain,"independent specialized precondition ownership");
   const bool badcfg=b==0||b>65536||band>3||(band==0&&(c.k0>13||c.k1!=255||count!=b))||(band!=0&&(c.k0>19||c.k1>11||uint64_t(count)>lim));
   require(s.d.error==(badcfg?4:0),"independent unchanged generic config/error priority");
   if(domain)++enabled;else ++excluded;
   s.d.abort_context=1;s.step();s.d.abort_context=0;require(s.d.specialized_owner_domain,"abort restores comparator domain");++cases;
  }
 }
 std::cout<<"{\\"type\\":\\"domain_start_verdict\\",\\"status\\":\\"TEST_PASS\\",\\"cases\\":"<<cases<<",\\"enabled_cases\\":"<<enabled<<",\\"excluded_AC_count_cases\\":"<<excluded<<"}\\n";
}
int main(int argc,char**argv){try{require(argc==4,"arguments");domain_starts(unsigned(std::stoul(argv[2])));return inherited_context_main(argc,argv);}catch(const std::exception&e){std::cerr<<"COUNT_DOMAIN_FAIL "<<e.what()<<'\\n';return 1;}}
''')
 # Exact whole-ingress bodies, with original generic context independent of enabled candidate.
 olding=ROOT/'fpga/experiments/cu66-v109-request/br88_packet_ingress_sync_v91h.sv'
 adapt(oldctx,'br88_context_reference.sv',[('module br88_context','module br88_context_reference')])
 adapt(olding,'ingress_original.sv',[('module br88_packet_ingress_sync_v91h ','module ingress_original '),('    br88_context context_decoder (','    br88_context_reference context_decoder (')])
 adapt(SRC/'br88_packet_ingress_sync_v91h.sv','ingress_candidate.sv',[('module br88_packet_ingress_sync_v91h ','module ingress_candidate ')])
 prev=olding.parent/'verification';fixtures={};fixture_edits={}
 for n in ['ingress_capture_probe.sv','tb_capture.cpp','tb_fetch.cpp']:
  text=(prev/n).read_text();ed=[]
  if n=='tb_capture.cpp':ed=[
   ('#include "Vingress_capture_probe_br88_context.h"','#include "Vingress_capture_probe__Syms.h"'),
   ('NEW(expected_fetch_addr)=uint32_t(index);','BOTH(expected_fetch_addr,uint32_t(index));'),
   ('#define CTXO r.__PVT__ingress_capture_probe__DOT__old_dut__DOT__context_decoder','#define CTXO(n) r.ingress_capture_probe__DOT__old_dut__DOT__context_decoder__DOT__##n'),
   ('#define CTXN r.__PVT__ingress_capture_probe__DOT__new_dut__DOT__context_decoder','#define CTXN(n) r.ingress_capture_probe__DOT__new_dut__DOT__context_decoder__DOT__##n'),
   ('#define CBOTH(n,v) do{const auto z=(v);CTXO->n=z;CTXN->n=z;}while(0)','#define CBOTH(n,v) do{const auto z=(v);CTXO(n)=z;CTXN(n)=z;}while(0)'),
   ('CTXN->done','CTXN(done)')]
  if n=='tb_fetch.cpp':ed=[('NEW(prepared_request_addr)=address;','BOTH(prepared_request_addr,address);'),('NEW(prepared_request_in_bounds)=address<c.size&&address<49152U;','BOTH(prepared_request_in_bounds,address<c.size&&address<49152U);')]
  for a,b in ed:assert text.count(a)==1;text=text.replace(a,b,1)
  (V/n).write_text(text);fixtures[str((prev/n).relative_to(ROOT))]=sha(prev/n);fixture_edits[n]=ed
 write(V/'adapters.json',dict(schema='v110-count-domain-actual-whole-context-and-ingress-adapters-v1',adapters=adapters,context_probe_original=str(oldprobe.relative_to(ROOT)),context_probe_original_sha256=sha(oldprobe),context_probe_edits=probe_edits,context_fixture_original=str(oldtb.relative_to(ROOT)),context_fixture_original_sha256=sha(oldtb),whole_ingress_fixture_originals=fixtures,whole_ingress_fixture_edits=fixture_edits,generic_pair_unconditional=True,specialized_pair_precondition='Owned start band0 or band>3 or AC count<=unsigned64 blocks*factor; reset/abort always compared. Other invalid config fields do not exempt comparison.',all_public_ports_including_invalid_and_counters=True,all_original_assertions_and_goldens_retained=True))
 write(AREA/'preparation.json',dict(status='PREPARED_NOT_RTL_QUALIFIED',source_sha256={str(p.relative_to(ROOT)):sha(p)for p in [SRC/'br88_context.sv',SRC/'br88_packet_ingress_sync_v91h.sv',SRC/'edit-recipe.json',V/'adapters.json']},arithmetic_analysis=dict(path='experiments/python-gamebub-v110/context-validation-analysis.json',sha256=sha(ROOT/'experiments/python-gamebub-v110/context-validation-analysis.json'))))
 print('COUNT_DOMAIN_PREPARED',sha(SRC/'br88_context.sv'),sha(SRC/'br88_packet_ingress_sync_v91h.sv'))
if __name__=='__main__':main()
