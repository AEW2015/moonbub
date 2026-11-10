#!/usr/bin/env python3
"""Prepare fresh reversible V125 fixtures. Never invokes an older preparer."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'fpga/experiments/cu66-v122-bounds'
AREA=ROOT/'fpga/experiments/cu66-v125-tile'
V=AREA/'verification'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')


def main():
    V.mkdir(parents=True,exist_ok=True)
    source=AREA/'cs88_admission_v91i2a.sv'
    oldv=json.loads((OLD/'verification-recipe.json').read_text())
    template=next(x for x in oldv['adapters'] if x['candidate'].endswith('admission_candidate.sv'))
    adapters=[];unchanged=[]
    def derive(original,target,edits):
        text=original.read_text()
        for e in edits:
            assert text.count(e['before'])==1,e['before']
            text=text.replace(e['before'],e['after'],1)
        target.write_text(text)
        adapters.append(dict(original=str(original.relative_to(ROOT)),original_sha256=sha(original),candidate=str(target.relative_to(ROOT)),candidate_sha256=sha(target),edits=edits))
    for variant,original in [('original',OLD/source.name),('candidate',source)]:
        edits=[dict(e) for e in template['edits']]
        edits[0]['after']='module admission_'+variant+' ('
        derive(original,V/('admission_'+variant+'.sv'),edits)
    for original in (OLD/'verification').iterdir():
        if not original.is_file() or original.name in ['admission_original.sv','admission_candidate.sv','tb_admission_legacy.cpp','tb_bounds.cpp']:continue
        target=V/original.name;target.write_bytes(original.read_bytes())
        unchanged.append(dict(original=str(original.relative_to(ROOT)),candidate=str(target.relative_to(ROOT)),sha256=sha(target)))
    original=OLD/'verification/tb_admission_legacy.cpp'
    edits=[
      dict(before='class Bench {\n',after='#include "tile_monitor.hpp"\nclass Bench {\n'),
      dict(before='#include "bounds_priming.hpp"\n',after='#include "bounds_priming.hpp"\n#include "tile_priming.hpp"\n'),
      dict(before='        x.clk=1;x.eval();require(!x.mismatch,"full module public output mismatch high");',after='        const auto tile_observed=tile_before(x,true);\n        x.clk=1;x.eval();require(!x.mismatch,"full module public output mismatch high");\n        tile_after(x,tile_observed,true);'),
      dict(before='static uint64_t prepared_mode_ports(unsigned seed) {\n',after='static uint64_t prepared_mode_ports(unsigned seed) {\n const uint64_t primer_start=tile_priming_edges;\n'),
      dict(before='  d.eval();require(!d.mismatch,"preedge public output mismatch");',after='  if(c.guard==0U&&(c.state==6U||c.state==10U||c.state==11U))prime_tile_key(d,r);\n  d.eval();require(!d.mismatch,"preedge public output mismatch");'),
      dict(before='  d.clk=1;d.eval();require(!d.mismatch,"postedge public output mismatch");',after='  const auto tile_observed=tile_before(d,false);\n  d.clk=1;d.eval();require(!d.mismatch,"postedge public output mismatch");\n  tile_after(d,tile_observed,false);'),
      dict(before='<<cases+2<<',after='<<cases+2+tile_priming_edges-primer_start<<'),
      dict(before=' d.final();return cases+2;\n}',after=' std::cout<<"{\\\"type\\\":\\\"v125_retained_mode_ledger\\\",\\\"status\\\":\\\"TEST_PASS\\\",\\\"semantic_cases\\\":"<<cases<<",\\\"original_clock_edges\\\":"<<cases+2<<",\\\"primer_clock_edges\\\":"<<tile_priming_edges-primer_start<<",\\\"total_clock_edges\\\":"<<cases+2+tile_priming_edges-primer_start<<"}\\n";\n d.final();return cases+2+tile_priming_edges-primer_start;\n}'),
    ]
    derive(original,V/original.name,edits)
    original=OLD/'verification/tb_bounds.cpp'
    derive(original,V/original.name,[dict(before='int main(int argc,char**argv)',after='int inherited_bounds_main(int argc,char**argv)')])
    caller=ROOT/'fpga/experiments/cu66-v124-owner/verification'
    for variant in ['original','candidate']:
        derive(caller/'ready_candidate.sv',V/('ready_'+variant+'.sv'),[
            dict(before='module ready_candidate #(',after='module ready_'+variant+' #('),
            dict(before='cs88_admission_v91i2a admission (',after='controller_admission_'+variant+' admission (')]) if variant=='original' else None
        if variant=='candidate':
            derive(caller/'ready_candidate.sv',V/'ready_candidate.sv',[
                dict(before='cs88_admission_v91i2a admission (',after='controller_admission_candidate admission (')])
        original=(OLD if variant=='original' else AREA)/source.name
        derive(original,V/('controller_admission_'+variant+'.sv'),[
            dict(before='module cs88_admission_v91i2a (',after='module controller_admission_'+variant+' (')])
    for name in ['ready_probe.sv','caller_pair.hpp','tb_controller.cpp']:
        original=caller/name;target=V/name;target.write_bytes(original.read_bytes())
        unchanged.append(dict(original=str(original.relative_to(ROOT)),candidate=str(target.relative_to(ROOT)),sha256=sha(target)))
    text=source.read_text()
    hidden=re.search(r'    function automatic logic hidden\(.*?    endfunction',text,re.S).group()
    count=re.search(r'    function automatic logic \[31:0\] tile_count\(.*?    endfunction',text,re.S).group()
    start=text.index('    logic prepared_tile_hidden,')
    end=text.index('`ifndef SYNTHESIS\n    always_ff',start)
    register_body=text[start:end]
    key_terminal_call="prepare_tile_key(plane==2?plane:plane+2'd1,32'd0);"
    plane_clear_call="prepare_tile_key(plane+2'd1,32'd0);"
    assert text.count(key_terminal_call)==text.count(plane_clear_call)==1
    wrapper='''module scalar_probe (
    input logic clk,reset,start,abort_packet,capture,group_capture,group_begin,
    input logic key_terminal_capture,plane_clear_capture,
    input logic [1:0] plane,input logic [31:0] tile,group_end,receipt_epoch,
    output logic out_hidden,out_terminal,out_group,
    output logic tile_valid,group_valid,
    output logic [31:0] tile_epoch,tile_key,group_epoch,group_key,group_end_key,
    output logic [1:0] tile_plane,group_plane
);
'''
    tail='''
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)begin
            tile_pred_owner_valid<=0;group_pred_owner_valid<=0;
        end else begin
            if(group_begin)group_pred_owner_valid<=0;
            if(capture)begin
                if(key_terminal_capture)KEY_TERMINAL_CALL
                else if(plane_clear_capture)begin
                    if(plane!=2)PLANE_CLEAR_CALL
                end else if(group_capture)prepare_group_key(plane,tile,group_end);
                else prepare_tile_key(plane,tile);
            end
        end
    end
    assign out_hidden=prepared_tile_hidden;
    assign out_terminal=prepared_tile_terminal;
    assign out_group=prepared_group_terminal;
    assign tile_valid=tile_pred_owner_valid;assign group_valid=group_pred_owner_valid;
    assign tile_epoch=tile_pred_owner_epoch;assign tile_key=tile_pred_owner_tile;
    assign tile_plane=tile_pred_owner_plane;
    assign group_epoch=group_pred_owner_epoch;assign group_key=group_pred_owner_tile;
    assign group_end_key=group_pred_owner_end;assign group_plane=group_pred_owner_plane;
endmodule
'''
    tail=tail.replace('KEY_TERMINAL_CALL',key_terminal_call).replace('PLANE_CLEAR_CALL',plane_clear_call)
    (V/'scalar_probe.sv').write_text(wrapper+hidden+'\n'+count+'\n'+register_body+tail)
    extraction=dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),target=str((V/'scalar_probe.sv').relative_to(ROOT)),target_sha256=sha(V/'scalar_probe.sv'),wrapper=wrapper,tail=tail,fragments=[hidden,count,register_body],terminal_call_fragments=[key_terminal_call,plane_clear_call],scope='Exact production functions/tasks/register declarations and terminal successor calls. Wrapper clocks explicit capture/hold/cancel/terminal-scalar operations, not original coordinate state. plane_clear preserves original plane2 no-write guard.')
    # Old semantic require bodies stay byte-identical even where clocks are added.
    bodies=lambda t:__import__('collections').Counter(re.findall(r'require\(.*?\);',t,re.S))
    for e in adapters:
        if e['original'].endswith('.cpp'):assert not bodies((ROOT/e['original']).read_text())-bodies((ROOT/e['candidate']).read_text())
    new_inputs=[dict(path=str((V/name).relative_to(ROOT)),sha256=sha(V/name)) for name in
        ['tile_priming.hpp','tile_monitor.hpp','tb_scalar.cpp','tb_tile.cpp','tb_caller.cpp']]
    save(AREA/'verification-recipe.json',dict(schema='v125-tile-verification-derivation-v1',adapters=adapters,unchanged=unchanged,new_verification_inputs=new_inputs,scalar_extraction=extraction,old_require_checks_removed=0,new_predicate_or_owner_forces=0,prepared_key_priming_is_natural_traffic=False))
    print('V125_TILE_VERIFICATION_PREPARED',len(adapters),len(unchanged))


if __name__=='__main__':main()
