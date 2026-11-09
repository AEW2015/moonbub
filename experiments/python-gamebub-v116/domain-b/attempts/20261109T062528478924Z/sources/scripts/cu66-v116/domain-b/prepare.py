#!/usr/bin/env python3
"""Reversible V116B domain predicate from the already-held coefficient tuple."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v116b-domain'
AREA=ROOT/'experiments/python-gamebub-v116/domain-b'
OLD=ROOT/'fpga/experiments/cu66-v107-meta-flags/cu66_coefficient_elastic.sv'
BASE='ea53b408aab5e522dfb2c4ffc2eefee41d58af37032cedc409e74815ab35dab9'
DOMAIN="in_qscale==3||!(in_value[15:11]==5'd0||in_value[15:11]==5'b11111||in_value==16'h0800)"
META="in_plane>2||in_tile>=(in_plane==0?13'd5400:13'd1350)||in_qcell!=quant_cell(in_plane,in_tile)"


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')


def main():
    SRC.mkdir(parents=True,exist_ok=True);AREA.mkdir(parents=True,exist_ok=True)
    assert sha(OLD)==BASE
    shadow='''`ifndef SYNTHESIS
    // The frozen input-side predicate is a verification-only independent
    // shadow. Its initialized certificate persists across all warm kills,
    // exactly like the original unreset payload and check registers.
    logic domain_shadow_seen=0;
    logic domain_shadow;
    always_ff @(posedge clk)begin
        if(!kill&&active&&in_valid&&in_ready)begin
            domain_shadow<=('''+DOMAIN+''');domain_shadow_seen<=1;
        end
        if(domain_shadow_seen)
            assert(out_domain_bad==domain_shadow)
                else $fatal(1,"V116B held domain differs from frozen accepted-input predicate");
    end
`endif
'''
    edits=[
        ('    assign out_domain_bad=tuple_checks[0];','''    assign out_domain_bad=tuple_checks[0];
    // Metadata remains registered. Domain uses the same already-held tuple;
    // no input-side selection cone enters a domain predicate FF.
    assign tuple_checks[0]=('''+DOMAIN.replace('in_','out_')+''');'''),
        ('                tuple_checks<={('+META+'),('+DOMAIN+')};','                tuple_checks[1]<=('+META+');'),
        ('endmodule',shadow+'endmodule')]
    text=OLD.read_text()
    for before,after in edits:assert text.count(before)==1;text=text.replace(before,after,1)
    candidate=SRC/OLD.name;candidate.write_text(text)
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',OLD.read_text(),re.S):assert block in text
    recipes=[]
    def adapt(source,name,changes):
        s=source.read_text()
        for before,after in changes:assert s.count(before)==1;s=s.replace(before,after,1)
        p=SRC/name;p.write_text(s)
        recipes.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(p),candidate_sha256=sha(p),edits=[dict(before=a,after=b)for a,b in changes]))
    for variant,source in [('original',OLD),('candidate',candidate)]:
        adapt(source,'domain_'+variant+'.sv',[('module cu66_coefficient_elastic (','module domain_'+variant+' (')])
    frozen=ROOT/'fpga/experiments/cu66-v107-meta-flags/verification'
    adapt(frozen/'tb_stage.cpp','tb_stage.frozen.cpp',[])
    ports=json.loads((frozen/'ports.json').read_text())['stage']
    header=OLD.read_text().split(');',1)[0]+');'
    header=header.replace('module cu66_coefficient_elastic (','module meta_stage_probe (',1).replace(');',', output logic [10:0] probe_quant_cell, output logic mismatch, output logic [63:0] pair_edges);')
    lines=[header,'initial pair_edges=0;']
    for p in ports:
        if p['direction']=='output':lines.append('logic '+p['signed']+p['packed']+' old_'+p['name']+';')
    for module,instance,old in [('domain_original','original',True),('domain_candidate','dut',False)]:
        conns=['.'+p['name']+'('+('old_' if old and p['direction']=='output' else '')+p['name']+')'for p in ports]
        lines.append(module+' '+instance+'('+','.join(conns)+');')
    lines.append('assign probe_quant_cell=dut.quant_cell(in_plane,in_tile);')
    lines.append('assign mismatch=('+ ' || '.join('(old_'+p['name']+'!='+p['name']+')'for p in ports if p['direction']=='output')+') || original.quant_cell(in_plane,in_tile)!=probe_quant_cell;')
    lines+=['always @(posedge clk or negedge clk)assert(!mismatch) else $fatal(1,"V116B every-edge full-public comparison");',
            'always_ff @(posedge clk)pair_edges<=pair_edges+1;', 'endmodule']
    (SRC/'meta_stage_probe.sv').write_text('\n'.join(lines)+'\n')
    write(SRC/'edit-recipe.json',dict(schema='v116b-held-coefficient-domain-v1',production=dict(original=rel(OLD),original_sha256=BASE,candidate=rel(candidate),candidate_sha256=sha(candidate),edits=[dict(before=a,after=b)for a,b in edits]),adapters=recipes,probe_sha256=sha(SRC/'meta_stage_probe.sv'),probe_ports_reference=dict(path=rel(frozen/'ports.json'),sha256=sha(frozen/'ports.json')),compared_public_outputs=[p['name']for p in ports if p['direction']=='output'],all_original_SVA_blocks_text_exact=True,declared_public_cycle_delta=0,metadata_flag_remains_registered=True,domain_shadow_synthesis_excluded=True,shadow_seen_persists_warm_kills=True,scope='All public2-state values every edge, including raw invalid views; unowned4-state initialization before first accepted tuple remains unspecified.'))
    write(AREA/'preparation.json',dict(status='PREPARED_NOT_RTL_QUALIFIED',actual_RTL_run=False,production=rel(candidate),production_sha256=sha(candidate),source_override={rel(OLD):rel(candidate)}))
    print('V116B_DOMAIN_PREPARED_NOT_RUN',sha(candidate))


if __name__=='__main__':main()
