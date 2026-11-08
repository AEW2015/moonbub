#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parents[3]
src=ROOT/'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv'
p=ROOT/'fpga/experiments/cu66-v107-payload-reset'
a=src.read_text()
assert hashlib.sha256(a.encode()).hexdigest()=='1ce06c26460a63b69ca9d742edb04ee9654827f883212c4bfe71293e0ed71084'
b=a.replace('state<=IDLE;coefficients<=0;chroma<=0;scale_code<=0;','state<=IDLE;')
b=b.replace('                coefficients<=in_coefficients;chroma<=in_chroma;scale_code<=in_scale_code;\n','')
needle='    always_ff @(posedge clk)begin\n'
assert b.count(needle)==1
b=b.replace(needle,'''    // Private, unowned while IDLE: deliberately capture even during kill or
    // without valid. Every MULTIPLY entry follows an accepted IDLE edge, which
    // replaces all payload bits. Owned MULTIPLY/HOLD_TILE jobs never reload.
    always_ff @(posedge clk)if(state==IDLE)begin
        coefficients<=in_coefficients;chroma<=in_chroma;scale_code<=in_scale_code;
    end
'''+needle,1)
(p/'cu66_dequant.sv').write_text(b)
(p/'dequant_original.sv').write_text(a.replace('module cu66_dequant (','module dequant_original (',1))
(p/'dequant_candidate.sv').write_text(b.replace('module cu66_dequant (','module dequant_candidate (',1))
head=a.split(');',1)[0].replace('module cu66_dequant (','module dequant_probe (')+', output logic mismatch);'
outs=[('logic','in_ready'),('logic','out_valid'),('logic [31:0]','out_id'),('logic [1279:0]','out_dequantized'),('logic','out_error')]
portnames=['clk','rst','abort_i','in_valid','in_ready','in_id','in_coefficients','in_chroma','in_scale_code','out_valid','out_ready','out_id','out_dequantized','out_error']
text=head+'\n'+'\n'.join(t+' old_'+n+';' for t,n in outs)+'\n'
for name,old in [('original',True),('candidate',False)]:
 text+='dequant_'+name+' '+name+'('+','.join('.'+n+'('+('old_' if old and n in {v for t,v in outs} else '')+n+')' for n in portnames)+');\n'
text+='assign mismatch='+' || '.join('(old_'+n+'!='+n+')' for t,n in outs)+';\nendmodule\n'
(p/'dequant_probe.sv').write_text(text)
r=dict(schema='v107-dequant-private-reset-edit-v1',baseline=str(src.relative_to(ROOT)),baseline_sha256=hashlib.sha256(a.encode()).hexdigest(),candidate=str((p/'cu66_dequant.sv').relative_to(ROOT)),candidate_sha256=hashlib.sha256(b.encode()).hexdigest(),private_reset_bits_removed=1027,public_reset_fields_retained=['state','group_index','out_id','out_error','out_dequantized'],private_load_predicate='state==IDLE; independent of rst, abort_i and in_valid',changes=[dict(start=i,end=j,old=a[i:j],new=b[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal'])
(p/'edit-recipe.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print('DEQUANT_PREPARED',r['candidate_sha256'])
