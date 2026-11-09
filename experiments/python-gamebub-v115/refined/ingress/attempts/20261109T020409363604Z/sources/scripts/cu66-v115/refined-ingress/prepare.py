#!/usr/bin/env python3
"""Reversible zero-public-cycle header length reduction at owned WAIT29."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-refined-ingress';V=S/'verification';OLD=R/'fpga/experiments/cu66-v115-ingress'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def main():
 source=OLD/'br88_packet_ingress_sync_v91h.sv';assert sha(source)=='b24bdd7db9077d76d30da8203a494584cd179ccd62ed65d87a768519dc858412';text=source.read_text();edits=[]
 def edit(a,b):
  nonlocal text
  assert text.count(a)==1,(a[:80],text.count(a));text=text.replace(a,b,1);edits.append(dict(before=a,after=b,occurrences=1))
 insertion='''    // REFINED_HEADER_LENGTH_BEGIN: owned WAIT29 E0 through predicate E3.
    // Two unsigned32 operands fit exactly in33 bits. Two such pairs fit in34;
    // size minus46 is retained at the original34-bit width, including wrap.
    // Payload pipelines have no reset/global CE. Only a coherent owned E3
    // predicate is committed; later unrelated ram_data cannot replace it.
    logic [31:0] header_length0_s0, header_length1_s0;
    logic [31:0] header_length2_s0, header_length3_s0;
    logic [33:0] header_size_s0, header_expected_s1, header_expected_s2;
    logic [32:0] header_pair01_s1, header_pair23_s1;
    logic [33:0] header_total_s2;
    logic [2:0] header_length_valid_pipe;
    logic header_length_live, header_length_mismatch;
    logic header_length_capture, header_length_flush;
    assign header_length_capture=prefix_header_capture&&fetch_index==6'd29;
    assign header_length_flush=cancelled||context_failure||(context_active&&ctx_done);
    always_ff @(posedge clk)begin
        if(header_length_flush)begin header_length_valid_pipe<=0;header_length_live<=0;end
        else begin
            header_length_valid_pipe<={header_length_valid_pipe[1:0],header_length_capture};
            if(header_length_valid_pipe[2])header_length_live<=1;
        end
    end
    always_ff @(posedge clk)begin
        // E0: the first three words are already stored, and the fourth word's
        // current high byte is forwarded from this exact owned response.
        header_length0_s0<=cached32(14);header_length1_s0<=cached32(18);
        header_length2_s0<=cached32(22);
        header_length3_s0<={ram_data,fetch_bytes[28],fetch_bytes[27],fetch_bytes[26]};
        header_size_s0<={2'd0,size_bytes};
        // E1: each full carry stays in an explicit33-bit pair.
        header_pair01_s1<={1'b0,header_length0_s0}+{1'b0,header_length1_s0};
        header_pair23_s1<={1'b0,header_length2_s0}+{1'b0,header_length3_s0};
        header_expected_s1<=header_size_s0-34'd46;
        // E2: the pair carry bits are retained in the final34-bit sum.
        header_total_s2<={1'b0,header_pair01_s1}+{1'b0,header_pair23_s1};
        header_expected_s2<=header_expected_s1;
        // E3: hold the one owned predicate until the next capture/kill.
        if(header_length_valid_pipe[2])header_length_mismatch<=header_total_s2!=header_expected_s2;
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!header_length_flush&&header_length_valid_pipe[2])begin
        assert(header_total_s2==({2'd0,cached32(14)}+{2'd0,cached32(18)}+{2'd0,cached32(22)}+{2'd0,cached32(26)}))
            else $fatal(1,"refined header sum lost full34-bit carry or forwarded high byte");
        assert(header_expected_s2==({2'd0,size_bytes}-34'd46))
            else $fatal(1,"refined header expected length lost34-bit underflow");
    end
    always_ff @(posedge clk)if(state==HEADER&&!header_length_flush)begin
        assert(header_length_live)else $fatal(1,"HEADER consumed a stale or unowned length predicate");
        assert(header_length_mismatch==(({2'd0,cached32(14)}+{2'd0,cached32(18)}+{2'd0,cached32(22)}+{2'd0,cached32(26)})!=({2'd0,size_bytes}-34'd46)))
            else $fatal(1,"refined header predicate differs from literal original expression");
    end
`endif
    // REFINED_HEADER_LENGTH_END

'''
 marker='    // COUNT_THRESHOLD_PIPELINE_BEGIN: nine registered positions E0..E8.';edit(marker,insertion+marker)
 expr="else if({2'd0,cached32(14)}+{2'd0,cached32(18)}+{2'd0,cached32(22)}+{2'd0,cached32(26)}!=({2'd0,size_bytes}-34'd46)) fail_packet(4);"
 edit(expr,'else if(header_length_mismatch) fail_packet(4);')
 candidate=S/source.name;candidate.write_text(text);back=text
 for e in reversed(edits):assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'],1)
 assert back==source.read_text()
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',source.read_text(),re.S):assert block in text
 write(S/'edit-recipe.json',dict(schema='v115-refined-header-length-owned-four-edge-pipeline-v1',original=rel(source),original_sha256=sha(source),candidate=rel(candidate),candidate_sha256=sha(candidate),edits=edits,public_cycle_delta=0,exact_widths=dict(operands=32,pair_sums=33,total=34,expected=34),capture='prefix_header_capture && fetch_index==29; includes current ram_data as len3 high byte',commit='E3,30 ordinary edges before HEADER in the unstalled two-edge fetch schedule; valid cleared on original cancel/failure/done guard',predicate='Exact literal original34-bit four-word sum != (zero-extended size_bytes -34d46)',payload_reset=False))
 # Public-cycle pair: the old body is copied with a module rename only.
 reference=V/'reference_ingress.sv';reference.write_text(source.read_text().replace('module br88_packet_ingress_sync_v91h #(','module br88_packet_ingress_sync_v91h_reference #(',1))
 wrapper_source=OLD/'verification/ingress_probe.sv';wrapper=wrapper_source.read_text();wrapper_edits=[]
 def wedit(a,b):
  nonlocal wrapper
  assert wrapper.count(a)==1;wrapper=wrapper.replace(a,b,1);wrapper_edits.append(dict(before=a,after=b))
 wedit('output logic probe_selection_context','output logic probe_selection_context,\n    output logic [2:0] probe_length_pipe, output logic probe_length_live,\n    output logic [63:0] probe_public_pair_checks')
 head=source.read_text().split(') (',1)[1].split(');',1)[0];ports=[];decl=[]
 for m in re.finditer(r'\b(input|output)\s+logic\s+(.*?)(?=\b(?:input|output)\s+logic|$)',head,re.S):
  direction,body=m[1],m[2].strip().rstrip(',').strip();names=re.sub(r'\[[^]]*\]','',body).replace('signed','').strip().split(',');names=[n.strip()for n in names]
  for n in names:ports.append((direction,n))
  if direction=='output':
   for n in names:body=re.sub(r'\b'+n+r'\b','reference_'+n,body)
   decl.append('    logic '+body+';')
 added='\n'.join(decl)+'\n    br88_packet_ingress_sync_v91h_reference #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) reference_dut('+','.join('.'+n+'('+('reference_'+n if d=='output'else n)+')'for d,n in ports)+');\n'
 added+='    assign probe_length_pipe=dut.header_length_valid_pipe;\n    assign probe_length_live=dut.header_length_live;\n    initial probe_public_pair_checks=0;\n    always_ff @(posedge clk)begin\n        probe_public_pair_checks<=probe_public_pair_checks+1;\n'
 for d,n in ports:
  if d=='output':added+=f'        assert({n}===reference_{n})else $fatal(1,"refined ingress public-cycle mismatch: {n}");\n'
 added+='    end\n'
 wedit('endmodule',added+'endmodule');(V/'ingress_probe.sv').write_text(wrapper)
 # Extend the unchanged initial dense/owner bench only after its complete old
 # coverage gate has executed; new tests gain exact pair assertions every edge.
 bench_source=OLD/'verification/tb_ingress.cpp';bench=bench_source.read_text();bench_edits=[]
 def bedit(a,b):
  nonlocal bench
  assert bench.count(a)==1;bench=bench.replace(a,b,1);bench_edits.append(dict(before=a,after=b))
 a='   if(target==6)target_hit=d.debug_state==5&&d.stage_word_valid;'
 bedit(a,a+'\n   if(target>=7&&target<=9)target_hit=d.probe_length_pipe==(1U<<unsigned(target-7));\n   if(target==10)target_hit=d.probe_length_live&&d.stage_purpose==0&&d.probe_fetch_index<42;')
 gate='need(w.requests==w.responses+w.canceled_reads,"actual synchronous read owner conservation");'
 extra='''
 const unsigned initial_cancel_retries=w.cancels,initial_successful_packets=w.packets;
 unsigned refined_cancel_checks=0,refined_length_checks=0;
 for(const auto&target:std::array<std::pair<int,int>,5>{{{0,29},{7,0},{8,0},{9,0},{10,0}}})for(unsigned action=0;action<6;++action){
  need(!w.run(*sparse,action%4,1,target.first,target.second,action),"refined pipeline cancel point not reached");
  need(w.run(*sparse,action%4,1,-1,-1,0,0,false),"refined pipeline non-reset retry failed");++refined_cancel_checks;
 }
 const uint32_t remaining=uint32_t(sparse->packet.size()-46);
 const std::array<std::array<uint32_t,4>,10> length_cases{{
  {{0xffffffffU,0xffffffffU,0xffffffffU,0xffffffffU}},
  {{0x40000000U,0x40000000U,0x40000000U,0x40000000U}},
  {{0x80000000U,0x80000000U,0x80000000U,0x80000000U}},
  {{0xffffffffU,remaining+1U,0,0}},
  {{0xffffffffU,0xffffffffU,remaining+2U,0}},
  {{remaining,0,0,0}},{{0,remaining,0,0}},
  {{remaining+1U,0,0,0}},{{remaining-1U,0,0,0}},
  {{0,0,0,0x01000000U}}
 }};
 for(unsigned i=0;i<length_cases.size();++i){auto c=*sparse;c.id+="-refined-length-"+std::to_string(i);for(unsigned j=0;j<4;++j)set32(c.packet,14+4*j,length_cases[i][j]);crc(c.packet);
  w.run(c,0,1,-1,-1,0,4);++refined_length_checks;need(w.run(*sparse,0,1,-1,-1,0,0,false),"refined length-reject clean retry failed");
 }
 // CRC has the original first-cause priority even when length arithmetic is bad.
 {auto c=*sparse;c.id+="-refined-crc-priority";set32(c.packet,26,0xffffffffU);crc(c.packet);c.packet.back()^=1;w.run(c,0,1,-1,-1,0,3);++refined_length_checks;need(w.run(*sparse,0,1,-1,-1,0,0,false),"refined CRC clean retry failed");}
 need(initial_cancel_retries==54&&initial_successful_packets==218&&refined_cancel_checks==30&&refined_length_checks==11,"refined additive coverage incomplete");
 need(w.requests==w.responses+w.canceled_reads,"refined complete synchronous read conservation");
 need(w.d.probe_public_pair_checks==w.edges,"exact public pair checker did not execute every clock");
'''
 bedit(gate,gate+extra)
 a='<<",\\"clock_edges\\":"<<w.edges';b='<<",\\"refined_cancel_checks\\":"<<refined_cancel_checks<<",\\"refined_length_checks\\":"<<refined_length_checks<<",\\"initial_cancel_retries\\":"<<initial_cancel_retries<<",\\"initial_successful_packets\\":"<<initial_successful_packets<<",\\"public_cycle_pair_checks\\":"<<w.d.probe_public_pair_checks'+a
 bedit(a,b);(V/'tb_ingress.cpp').write_text(bench)
 adapters=dict(schema='v115-refined-ingress-additive-exact-public-cycle-pair-v1',reference_module=dict(original=rel(source),original_sha256=sha(source),copy=rel(reference),copy_sha256=sha(reference),module_rename_only=True),wrapper=dict(original=rel(wrapper_source),original_sha256=sha(wrapper_source),candidate=rel(V/'ingress_probe.sv'),candidate_sha256=sha(V/'ingress_probe.sv'),edits=wrapper_edits),bench=dict(original=rel(bench_source),original_sha256=sha(bench_source),candidate=rel(V/'tb_ingress.cpp'),candidate_sha256=sha(V/'tb_ingress.cpp'),edits=bench_edits),parser_unchanged=True,initial_coverage_gate_retained=True)
 write(V/'adapters.json',adapters);print('REFINED_INGRESS_PREPARED_NOT_RUN',sha(candidate))
if __name__=='__main__':main()
