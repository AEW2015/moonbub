#!/usr/bin/env python3
"""Source-bind V128 paired actual scratch and extracted full-tuple algebra fixtures."""
import argparse,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
DEST=ROOT/'fpga/experiments/cu66-v128-raw/verification'
OLD=ROOT/'fpga/experiments/cu66-v127-owner/packed_scratch_v91g2.sv'
NEW=ROOT/'fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(Path(p).relative_to(ROOT)),sha256=sha(p))
def original_ports(text):
 h=text[text.index('module packed_scratch_v91g2 (')+len('module packed_scratch_v91g2 ('):text.index('\n);')]
 h=re.sub(r'//[^\n]*','',h)
 out=[];direction=typ=None
 for token in h.split(','):
  t=token.strip();m=re.match(r'^(input|output)\s+(.+)$',t,re.S)
  if m:direction=m.group(1);t=m.group(2).strip();m=re.match(r'^(logic(?:\s+signed)?(?:\s*\[[^]]+\])?)\s+(.+)$',t,re.S);assert m,t;typ=m.group(1);t=m.group(2).strip()
  m=re.fullmatch(r'(\w+)(\s*\[[^]]+\])?(?:\s*=\s*\w+)?',t);assert m,t
  out.append(dict(direction=direction,type=typ,name=m.group(1),array=(m.group(2)or'').strip()))
 return out

def declaration(p,prefix='',direction=True):
 return ('    '+(p['direction']+' 'if direction else'')+p['type']+' '+prefix+p['name']+(' '+p['array']if p['array']else''))

def generate():
 old,new=OLD.read_text(),NEW.read_text();records=[]
 def source_fragment(path,text,fragment,role):
  assert text.count(fragment)==1,(role,text.count(fragment));records.append(dict(source=pin(path),role=role,fragment=fragment));return fragment
 funcs=[]
 for name in ['zigzag','band_matches']:
  m=re.search(r'    function automatic logic[^\n]*\b'+name+r'\(.*?    endfunction',old,re.S);assert m,name;funcs.append(source_fragment(OLD,old,m.group(0),name))
 assigns=[]
 for name in ['input_sparse_order_bad','input_raster_position','input_raster_bad','input_dc_bad','input_ac_bad']:
  m=re.search(r'    assign '+name+r'=.*?;',old,re.S);assert m,name;assigns.append(source_fragment(OLD,old,m.group(0),name))
 start=old.index('    for(genvar checking_phase=0;');end=old.index('`ifndef SYNTHESIS',start)
 phase_prefix=source_fragment(OLD,old,old[start:end],'old-eight-phase-implementation')
 match=re.search(r'assert\(phase_input_bad\[checking_phase\]==(.*?)\)\s*else \$fatal\(1,"V119 full phase format decision mismatch"\)',old,re.S);assert match
 literal=match.group(1);source_fragment(OLD,old,match.group(0),'old-literal-guarded-oracle')
 begin=new.index('    // V128_RAW_VALIDATION_BEGIN:');end=new.index('    // V128_RAW_VALIDATION_END',begin)+len('    // V128_RAW_VALIDATION_END\n')
 lanes=source_fragment(NEW,new,new[begin:end],'new-two-full-tuple-lanes')
 m=re.search(r'        assign phase_input_bad\[checking_phase\]=.*?;',new,re.S);assert m
 selection=source_fragment(NEW,new,m.group(0),'new-Boolean-selection')
 fields=[('epoch','[31:0]'),('block','[15:0]'),('index','[5:0]'),('value','signed [15:0]'),('band','[1:0]')]
 tupleports=[dict(direction='input',type='logic',name='coef_select_raw',array='')]
 for lane in ['raw','context']:
  for field,width in fields:tupleports.append(dict(direction='input',type='logic '+width,name='coef_'+lane+'_'+field,array=''))
 params=[('raw_mode',''),('active_epoch','[31:0]'),('blocks','[16:0]'),('written','[31:0]'),('previous_position','[31:0]'),('previous_valid',''),('rank_threshold_mask','[63:0]'),('phase','[2:0]')]
 scalarports=tupleports+[dict(direction='input',type='logic '+w,name=n,array='')for n,w in params]+[dict(direction='input',type='logic [31:0]',name='counts',array='[0:3]')]
 scalarouts=[('reference_phase_bad','[7:0]'),('candidate_phase_bad','[7:0]'),('literal_phase_bad','[7:0]'),('reference_epoch_bad',''),('candidate_epoch_bad',''),('reference_selected_bad',''),('candidate_selected_bad',''),('block_limit_high','')]
 scalarports +=[dict(direction='output',type='logic '+w,name=n,array='')for n,w in scalarouts]
 scalar='module v128_raw_scalar_probe (\n'+',\n'.join(declaration(p)for p in scalarports)+'\n);\n'
 scalar+='\n'.join(funcs)+'\n'
 for field,width in fields:scalar+='    logic '+width+' coef_'+field+';\n    assign coef_'+field+'=coef_select_raw ? coef_raw_'+field+' : coef_context_'+field+';\n'
 scalar+='    wire [5:0] input_zigzag=zigzag(coef_index);\n    logic [31:0] input_raster_position;\n    logic input_raster_bad,input_dc_bad,input_ac_bad,input_sparse_order_bad;\n'
 scalar+='\n'.join(assigns)+'\n'+lanes
 scalar+=phase_prefix.replace('phase_input_bad','reference_phase_bad')
 scalar+='        assign literal_phase_bad[checking_phase]='+literal+';\n    end\n'
 scalar+='    for(genvar checking_phase=0;checking_phase<8;checking_phase=checking_phase+1)begin: selected_lane\n'+selection.replace('phase_input_bad','candidate_phase_bad')+'\n    end\n'
 scalar+='    assign block_limit_high=blocks[16];\n    assign reference_epoch_bad=coef_epoch!=active_epoch;\n    assign candidate_epoch_bad=input_epoch_bad;\n    assign reference_selected_bad=reference_phase_bad[phase];\n    assign candidate_selected_bad=candidate_phase_bad[phase];\nendmodule\n'
 ports=original_ports(old);coefficient={'coef_'+x for x,_ in fields}
 topports=[p for p in ports if p['name']not in coefficient]+tupleports
 topports +=[dict(direction='input',type='logic '+w,name='alg_'+n,array='')for n,w in params]
 topports +=[dict(direction='input',type='logic [31:0]',name='alg_count'+str(i),array='')for i in range(4)]
 topports +=[dict(direction='output',type='logic '+w,name='alg_'+n,array='')for n,w in scalarouts]
 topports +=[dict(direction='output',type='logic',name=n,array='')for n in ['pair_equal','pair_predicate_equal']]
 wrapper='module raw_probe (\n'+',\n'.join(declaration(p)for p in topports)+'\n);\n'
 outputs=[p for p in ports if p['direction']=='output']
 for p in outputs:wrapper+=declaration(p,'b_',False)+';\n'
 for field,width in fields:wrapper+='    wire '+width+' coef_'+field+'=coef_select_raw ? coef_raw_'+field+' : coef_context_'+field+';\n'
 for module,instance,extra,prefix in [('v128_scratch_baseline','baseline',False,'b_'),('packed_scratch_v91g2','candidate',True,'')]:
  conns=['        .'+p['name']+'('+ (prefix if p['direction']=='output'else'')+p['name']+')'for p in ports]
  if extra:conns+=['        .'+p['name']+'('+p['name']+')'for p in tupleports]
  wrapper+='    '+module+' '+instance+' (\n'+',\n'.join(conns)+'\n    );\n'
 predicates=['baseline.input_bad==candidate.input_bad','baseline.phase_input_bad==candidate.phase_input_bad','(coef_epoch!=baseline.active_epoch)==candidate.input_epoch_bad']
 wrapper+='    always_comb begin\n        pair_equal=1;\n'
 for p in outputs:
  if p['array']:wrapper+='        for(integer i=0;i<2;i=i+1)pair_equal=pair_equal && b_'+p['name']+'[i]=='+p['name']+'[i];\n'
  else:wrapper+='        pair_equal=pair_equal && b_'+p['name']+'=='+p['name']+';\n'
 wrapper+='        pair_predicate_equal='+ ' && '.join('('+p+')'for p in predicates)+';\n    end\n'
 wrapper+='    logic [31:0] alg_counts [0:3];\n'
 for i in range(4):wrapper+='    assign alg_counts['+str(i)+']=alg_count'+str(i)+';\n'
 conns=[]
 for p in scalarports:
  n=p['name'];signal=('alg_'+n if n not in {x['name']for x in tupleports}else n)
  if n=='counts':signal='alg_counts'
  conns.append('        .'+n+'('+signal+')')
 wrapper+='    v128_raw_scalar_probe algebra (\n'+',\n'.join(conns)+'\n    );\nendmodule\n'
 baseline=old.replace('module packed_scratch_v91g2 (','module v128_scratch_baseline (',1)
 return {'v128_scratch_baseline.sv':baseline,'v128_raw_scalar_probe.sv':scalar,'raw_probe.sv':wrapper},records

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();outputs,fragments=generate();DEST.mkdir(parents=True,exist_ok=True)
 if a.write:
  for name,text in outputs.items():(DEST/name).write_text(text)
 else:
  for name,text in outputs.items():assert (DEST/name).read_text()==text,name
 manifest=dict(schema='v128-raw-verification-source-binding-v1',preparer=pin(Path(__file__)),baseline=pin(OLD),candidate=pin(NEW),fragments=fragments,baseline_module_rename_only=True,original_assertions_retained=True,source_payload_or_owner_forces=0,files={str((DEST/n).relative_to(ROOT)):sha(DEST/n)for n in outputs})
 cpp=DEST/'tb_raw.cpp'
 if cpp.is_file():manifest['files'][str(cpp.relative_to(ROOT))]=sha(cpp)
 path=DEST.parent/'verification-recipe.json'
 if a.write:path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 else:assert json.loads(path.read_text())==manifest
 print('V128_RAW_VERIFICATION_PREPARED_NOT_RUN',len(outputs),len(fragments))
if __name__=='__main__':main()
