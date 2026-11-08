#!/usr/bin/env python3
"""Prepare only: unmask fixed Rice prefix taps, retaining exact public/state contract."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v109-rice';AREA=ROOT/'experiments/python-gamebub-v109/rice';OLD=ROOT/'fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv';HASH='f39c3f90d0242097ea3cd2693e6f4d99e58e33a0b49c644c720497f50e6777dc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(OLD)==HASH;s=OLD.read_text();edits=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1;s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit('        // Keep the original valid-bit guards and balanced first-one priority.','        // Availability qualifies consumption below; fixed taps avoid its decode\n        // before the balanced priority tree. Public and stored-state timing is exact.')
 edit("            if (available > 7'(i) && reservoir[63-i])",'            if (reservoir[63-i])')
 guard='''`ifndef SYNTHESIS
    // Independent guarded-use reference. Unused raw rank may differ when
    // unowned bits are arbitrary; every selected PREFIX semantic must match.
    logic [3:0] guarded_masked_rank;
    logic [4:0] guarded_masked_zeros;
    logic guarded_masked_found;
    logic [5:0] guarded_masked_take;
    always_comb begin
        guarded_masked_rank=15;
        for(integer p=14;p>=0;p=p-1)
            if(available>7'(p) && reservoir[63-p])guarded_masked_rank=4'(p);
        guarded_masked_zeros=window<6'(guarded_masked_rank)?5'(window):5'(guarded_masked_rank);
        guarded_masked_found=6'(guarded_masked_rank)<window;
        guarded_masked_take=guarded_masked_zeros==15?6'd15:
            (guarded_masked_found?6'(guarded_masked_zeros)+1'b1:window);
    end
    always_ff @(posedge clk)if(state==PREFIX && !serial && can_step)begin
        assert(zeros==guarded_masked_zeros && found_one==guarded_masked_found &&
            take_bits==guarded_masked_take) else $fatal(1,"guarded PREFIX semantic mismatch");
    end
`endif
'''
 edit('endmodule',guard+'endmodule');path=SRC/'br88_rice_elastic.sv';path.write_text(s);reverse=s
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==OLD.read_text()
 e=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(path.relative_to(ROOT)),candidate_sha256=sha(path),edits=edits)
 write(SRC/'edit-recipe.json',dict(schema='v109-rice-guarded-prefix-tap-recipe-v1',status='PREPARED_NOT_RTL_QUALIFIED_NOT_SELECTED',production={path.name:e},added_public_cycles=0,private_differences='Only unused combinational prefix candidates/ranks/zeros/take/extraction outside guarded uses may differ for arbitrary unowned reservoir bits. Every public output, invalid output, counter and stored register remains exact.'))
 header=OLD.read_text().split(');',1)[0]+');';ports=[];inherited=None
 for item in header.split('(',1)[1].rsplit(');',1)[0].split(','):
  item=item.strip();m=re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)',item,re.S)
  if m:direction,signed,packed,item=m.groups();inherited=(direction,signed or '',packed or '')
  assert inherited and re.fullmatch(r'\w+',item),item
  ports.append(dict(name=item,direction=inherited[0],signed=inherited[1],packed=inherited[2]))
 adapters=[];out=SRC/'verification'
 for suffix,p in [('original',OLD),('candidate',path)]:
  before='module br88_rice_elastic (';after='module rice_'+suffix+' (';text=p.read_text();assert text.count(before)==1;text=text.replace(before,after,1);q=out/('rice_'+suffix+'.sv');q.write_text(text);adapters.append(dict(source=str(p.relative_to(ROOT)),path=str(q.relative_to(ROOT)),source_sha256=sha(p),sha256=sha(q),renames=[[before,after]]))
 extra=', output logic probe_outputs_equal, probe_internal_equal, probe_guarded_equal, probe_word_bad, output logic [31:0] probe_size, probe_loaded, probe_consumed, probe_cache_remaining, probe_cache_load, output logic [63:0] probe_reservoir, output logic [1:0] probe_state, output logic [3:0] probe_failed, output logic [4:0] probe_suffix_left);'
 lines=[header.replace('module br88_rice_elastic (','module rice_probe (',1).replace(');',extra)]
 for p in ports:
  if p['direction']=='output':lines.append(f"logic {p['signed']}{p['packed']}old_{p['name']};")
 for mod,inst,isold in [('rice_original','old_dut',True),('rice_candidate','new_dut',False)]:lines.append(mod+' '+inst+'('+','.join('.'+p['name']+'('+('old_' if isold and p['direction']=='output' else '')+p['name']+')' for p in ports)+');')
 lines.append('assign probe_outputs_equal = '+' && '.join('(old_'+p['name']+'=='+p['name']+')' for p in ports if p['direction']=='output')+';')
 # All V107 comparisons retained, plus raw full reservoir equality. This list
 # includes every actual stored register; public counters are in output checks.
 internal=['state','active','use16','serial','failed','size_bits','loaded','consumed','reservoir','available','k','escape_width','quotient','suffix_left','suffix_acc','remaining','load_remaining','word_bad','cached_remaining','cached_load_remaining']
 lines.append('assign probe_internal_equal = '+' && '.join('(old_dut.'+n+'==new_dut.'+n+')' for n in internal)+';')
 lines.append('''assign probe_guarded_equal=(old_dut.needed==new_dut.needed) && (old_dut.can_step==new_dut.can_step) &&
 ((new_dut.state!=1 || new_dut.serial || !new_dut.can_step) ||
  ((old_dut.zeros==new_dut.zeros) && (old_dut.found_one==new_dut.found_one) && (old_dut.take_bits==new_dut.take_bits))) &&
 ((new_dut.state!=1 || !new_dut.serial) || ((old_dut.take_bits==new_dut.take_bits) && (old_dut.extracted==new_dut.extracted))) &&
 ((new_dut.state!=2) || ((old_dut.take_bits==new_dut.take_bits) && (old_dut.suffix_value==new_dut.suffix_value) && (old_dut.decoded_value==new_dut.decoded_value)));''')
 for outname,n in [('word_bad','word_bad'),('size','size_bits'),('loaded','loaded'),('consumed','consumed'),('cache_remaining','cached_remaining'),('cache_load','cached_load_remaining'),('reservoir','reservoir'),('state','state'),('failed','failed'),('suffix_left','suffix_left')]:lines.append('assign probe_'+outname+'='+('(new_dut.available==0 ? 64\'d0 : new_dut.reservoir >> (7\'d64-new_dut.available))' if n=='reservoir' else 'new_dut.'+n)+';')
 lines.append('endmodule');(out/'rice_probe.sv').write_text('\n'.join(lines)+'\n')
 hist=ROOT/'fpga/experiments/cu66-v91/tb_rice.cpp';h=hist.read_text();reps=[('Vbr88_rice_elastic','Vrice_probe'),('int main(int argc,char** argv)','int historical_rice_main(int argc,char** argv)'),('d.clk=1; d.eval(); d.clk=0; d.eval();','rice_pre(d); d.clk=1; d.eval(); rice_post(d); d.clk=0; d.eval();')]
 for before,after in reps:assert before in h;h=h.replace(before,after)
 (out/'historical_rice.cpp').write_text(h)
 bench=ROOT/'fpga/experiments/cu66-v107-rice/tb_rice.cpp';b=bench.read_text();bench_edits=[('OLD(reservoir)=oracle.reservoir;NEW(reservoir)=available?oracle.reservoir<<(64-available):0;','BOTH(reservoir,available?oracle.reservoir<<(64-available):0);'),('require(d.probe_outputs_equal&&d.probe_internal_equal,"actual complete parser pre/post comparison");','require(d.probe_outputs_equal&&d.probe_internal_equal,"actual complete parser pre/post comparison");\n require(d.probe_guarded_equal,"guarded prefix/suffix semantics");')]
 for before,after in bench_edits:assert b.count(before)==1;b=b.replace(before,after,1)
 (out/'tb_rice.cpp').write_text(b)
 write(out/'adapters.json',dict(schema='v109-rice-complete-lossless-adapters-v1',adapters=adapters,historical_original=str(hist.relative_to(ROOT)),historical_sha256=sha(hist),historical_renames=reps,bench_original=str(bench.relative_to(ROOT)),bench_original_sha256=sha(bench),bench_edits=bench_edits,internal_comparisons=internal,public_output_comparisons=[p['name'] for p in ports if p['direction']=='output'],old_assertions_or_oracles_removed=False,prepared_state_change='Old V107 is MSB-aligned; adapt inherited V106-original low-reservoir preparation to the same actual high alignment for BOTH modules; independent normalized low-queue oracle unchanged.'))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL_NOT_SELECTED',production_sha256=sha(path),original_sha256=HASH,public_added_cycles=0,all_public_invalid_counter_and_stored_state_equality_required=True,original_assertions_retained=True))
 print('RICE_PREPARED_NOT_RTL_NOT_SELECTED',sha(path))
if __name__=='__main__':main()
