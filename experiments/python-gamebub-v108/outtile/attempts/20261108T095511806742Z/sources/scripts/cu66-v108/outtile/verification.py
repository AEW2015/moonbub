#!/usr/bin/env python3
"""Prepare whole-body old/new adapters and extend every existing IDCT check."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v108-outtile'
BASE=ROOT/'fpga/experiments/cu66-v107-idct-reset'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=json.loads((BASE/'adapter.json').read_text());recipe=json.loads((SRC/'edit-recipe.json').read_text());adapters=[]
    added_ports=',\n    output logic [63:0] verify_written,verify_payload_write,\n    output logic [1535:0] verify_payload\n);'
    added_assign='''
    assign verify_written=out_written;
    for(genvar w=0;w<64;w=w+1)begin: output_observation
        assign verify_payload[w*24+:24]=output_words[w].payload;
        assign verify_payload_write[w]=(state==DC_SECOND_ACC)||
            (state==SECOND_ACC&&k==7&&group_index==2'((w%8)/2));
    end
'''
    for variant,p in [('original',ROOT/recipe['original_path']),('candidate',SRC/'cu66_idct8x8.sv')]:
        text=p.read_text();changes=[('module cu66_idct8x8 (','module idct_'+variant+' ('),('\n);',a['extra_ports'])]
        for before,after in changes:
            assert text.count(before)==1;text=text.replace(before,after,1)
        if variant=='candidate':
            before='\n);';assert text.count(before)==1;text=text.replace(before,added_ports,1)
        inserts=a['assignments']+(added_assign if variant=='candidate' else '')
        assert text.count('endmodule')==1;text=text.replace('endmodule',inserts+'endmodule',1)
        q=SRC/('idct_'+variant+'.sv');q.write_text(text)
        adapters.append(dict(source=str(p.relative_to(ROOT)),source_sha256=sha(p),path=str(q.relative_to(ROOT)),sha256=sha(q),module_rename=changes[0],extra_ports=a['extra_ports'],extra_assignments=a['assignments'],candidate_extra_ports=added_ports if variant=='candidate' else None,candidate_extra_assignments=added_assign if variant=='candidate' else None))
    probe=(BASE/'idct_probe.sv').read_text()
    before='    output logic [111:0] verify_basis\n);';after='    output logic [111:0] verify_basis,\n    output logic [63:0] verify_written,verify_payload_write,\n    output logic [1535:0] verify_payload\n);';assert probe.count(before)==1;probe=probe.replace(before,after,1)
    before='        .verify_basis(verify_basis),.verify_source_tile(verify_source_tile));';after='        .verify_basis(verify_basis),.verify_source_tile(verify_source_tile),\n        .verify_written(verify_written),.verify_payload_write(verify_payload_write),.verify_payload(verify_payload));';assert probe.count(before)==1;probe=probe.replace(before,after,1)
    (SRC/'idct_probe.sv').write_text(probe)
    bench=(BASE/'tb_idct.cpp').read_text();edits=[]
    def change(before,after):
        nonlocal bench
        assert bench.count(before)==1,before
        bench=bench.replace(before,after,1);edits.append(dict(before=before,after=after))
    change('#include "Vidct_probe.h"','#include "Vidct_probe.h"\n#include "Vidct_probe___024root.h"')
    needle=' explicit Bench(unsigned seed,const std::string&path):rng(seed),trace(path)'
    helper=''' uint64_t expected_written=0,poison_words=0,public_word_checks=0,exposed_word_commits=0,kill_payload_collisions=0,clear_edges=0;
 std::mt19937 poison_rng;
 void check_words(){need(d.verify_written==expected_written,"independent exact public-word written-mask owner");for(unsigned word=0;word<64;++word){const auto p=bits(d.verify_payload,word*24,24);const auto o=bits(d.out_tile,word*24,24);need(o==((expected_written>>word&1U)?p:0U),"every public invalid/partial word visibility");++public_word_checks;}}
 void poison_hidden(){auto&r=*d.rootp;for(unsigned word=0;word<64;++word)if(!(expected_written>>word&1U)){const uint32_t noise=poison_rng()&0xffffffU;switch(word){
'''
    for word in range(64):helper+=f' case {word}:r.idct_probe__DOT__candidate__DOT__output_words__BRA__{word}__KET____DOT__payload=noise;break;\n'
    helper+=''' default:throw std::runtime_error("private word index");}++poison_words;}d.eval();need(d.probe_equal,"arbitrary masked private payload became public");check_words();}
'''
    change(needle,helper+' explicit Bench(unsigned seed,const std::string&path):rng(seed),trace(path),poison_rng(seed^0x10800000U)')
    change('  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT preedge mismatch");unsigned state=d.verify_state;',
        '  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT preedge mismatch");check_words();poison_hidden();unsigned state=d.verify_state;')
    needle='  d.clk=1;d.eval();need(d.probe_equal,"whole IDCT postedge mismatch");'
    extra='''  uint64_t writes=0;
  if(state==8)writes=~uint64_t(0);
  else if(state==4&&d.verify_k==7)for(unsigned row=0;row<8;++row)for(unsigned col=2U*d.verify_group;col<2U*d.verify_group+2;++col)writes|=uint64_t(1)<<(row*8+col);
  need(d.verify_payload_write==writes,"independent original group/DC payload write schedule");
  bool input_bad=false,input_zero=true;for(unsigned word=0;word<64;++word){const int64_t value=signed_bits(bits(d.in_tile,word*20,20),20);input_bad|=value>522240||value< -522240;input_zero&=value==0;}
  const bool clear=kill||(state==0&&d.in_valid&&d.in_ready&&(input_bad||input_zero));
  if(kill&&writes)++kill_payload_collisions;
  if(clear){expected_written=0;++clear_edges;}else{exposed_word_commits+=uint64_t(__builtin_popcountll(writes&~expected_written));expected_written|=writes;}
  d.clk=1;d.eval();need(d.probe_equal,"whole IDCT postedge mismatch");check_words();'''
    change(needle,extra)
    change('  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT falling evaluation mismatch");',
        '  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT falling evaluation mismatch");check_words();')
    needle=' need(abort_mask==1023&&b.states==1023,"all FSM states coverage");'
    change(needle,needle+'need(b.poison_words>1000&&b.kill_payload_collisions>=3&&b.exposed_word_commits>1000,"arbitrary hidden-word/kill collision/exposure coverage");')
    needle='<<b.clocks<<",\\\"multiply_edges\\\":"'
    after='<<b.clocks<<",\\\"masked_private_word_poisons\\\":"<<b.poison_words<<",\\\"all_cycle_public_word_checks\\\":"<<b.public_word_checks<<",\\\"exposed_word_commits\\\":"<<b.exposed_word_commits<<",\\\"kill_payload_write_collisions\\\":"<<b.kill_payload_collisions<<",\\\"clear_edges\\\":"<<b.clear_edges<<",\\\"multiply_edges\\\":"'
    change(needle,after)
    (SRC/'tb_idct.cpp').write_text(bench)
    (SRC/'adapters.json').write_text(json.dumps(dict(schema='v108-outtile-lossless-whole-body-adapters-v1',adapters=adapters,probe_original=str((BASE/'idct_probe.sv').relative_to(ROOT)),probe_original_sha256=sha(BASE/'idct_probe.sv'),original_probe_expression_kept=True,bench_original=str((BASE/'tb_idct.cpp').relative_to(ROOT)),bench_original_sha256=sha(BASE/'tb_idct.cpp'),bench_edits=edits,all_original_public_and_golden_checks_kept=True,actual_RTL_run=False),indent=2,sort_keys=True)+'\n')
    print('OUTTILE_VERIFICATION_PREPARED',sha(SRC/'cu66_idct8x8.sv'))
if __name__=='__main__':main()
