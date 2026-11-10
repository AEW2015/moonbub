#!/usr/bin/env python3
"""Source-bind scoped padding writers, consumer and ordered reject kernel."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'fpga/experiments/cu66-v128-padding'
V=AREA/'verification'
OLD=ROOT/'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'
NEW=AREA/'cs88_admission_v91i2a.sv'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return {'path':str(Path(p).relative_to(ROOT)),'sha256':sha(p)}

def fragments():
 old,new=OLD.read_text(),NEW.read_text();recipe=json.loads((AREA/'edit-recipe.json').read_text())
 total="    logic prepared_header_total_matches;\n    always_ff @(posedge clk)if(state==HEADER_BYTE)\n        prepared_header_total_matches<=header_packet_total=={3'd0,size_bytes};\n"
 owner_start=old.index('`ifndef SYNTHESIS\n',old.index(total)+len(total));owner_end=old.index('`endif',owner_start)+len('`endif')
 owner=old[owner_start:owner_end]+'\n'
 fs=old.index('    function automatic logic [31:0] h32(');fe=old.index('    function automatic logic hidden(',fs)
 helpers=old[fs:fe]
 hs=old.index("                    if(h32(0)!=32'h43533838");he=old.index('                    else begin\n                        fid<=h32(8)',hs)
 reject=old[hs:he]
 writer='                    header[header_index[6:0]]<=byte_value;\n'
 old_consumer='''                    logic padding_ok;
                    padding_ok=1;
                    for(integer k=116;k<128;k=k+1)if(header[k]!=0)padding_ok=0;
'''
 new_consumer='''                    logic padding_ok;
                    padding_ok=prepared_header_padding_ok;
'''
 for fragment in (total,owner,helpers,reject,writer):
  assert old.count(fragment)==1 and new.count(fragment)==1
 assert old.count(old_consumer)==1 and new.count(new_consumer)==1
 cache=recipe['production_cache_fragment'];newowner=recipe['additive_assertion_fragment'];assert new.count(cache)==new.count(newowner)==1
 return dict(total=total,owner=owner,helpers=helpers,reject=reject,writer=writer,old_consumer=old_consumer,new_consumer=new_consumer,cache=cache,newowner=newowner)


def build():
 f=fragments();sources=[]
 ports='''    input logic clk,reset,start,abort_packet,
    input logic [7:0] state,byte_value,
    input logic [31:0] header_index,receipt_epoch,size_bytes,snapshot_fid,
    input logic snapshot_valid,
    input logic [63:0] snapshot_generation,
    input logic [34:0] header_packet_total,
    output logic observed_padding,
    output logic [7:0] error,
    output logic observed_cache,owner_complete
'''
 for candidate in (False,True):
  name='padding_candidate_kernel' if candidate else 'padding_original_kernel'
  selected_ports=ports if candidate else ports.replace('    output logic [7:0] error,\n    output logic observed_cache,owner_complete\n','    output logic [7:0] error\n')
  pre='module '+name+'(\n'+selected_ports+');\n    localparam logic [7:0] HEADER_BYTE=4, HEADER_CHECK=5;\n    logic [7:0] header [0:127];\n    logic evaluated_padding;\n'
  if candidate:pre+=f['cache']+f['newowner']
  pre+=f['total']+f['owner']+f['helpers']
  consumer=f['new_consumer'] if candidate else f['old_consumer'];consumer=consumer.replace('                    logic padding_ok;\n','')
  consumer=re.sub(r'\bpadding_ok\b','evaluated_padding',consumer)
  reject=re.sub(r'\bpadding_ok\b','evaluated_padding',f['reject'])
  for n in range(4,9):assert reject.count(f'reject({n});')==1;reject=reject.replace(f'reject({n});',f"error<=8'd{n};")
  body='''    always_comb begin
'''+consumer+'''    end
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)error<=0;
        else begin
            if(state==HEADER_BYTE)begin
'''+f['writer']+'''            end
            if(state==HEADER_CHECK)begin
                    observed_padding<=evaluated_padding;
'''+reject+'''                    else error<=0;
            end
        end
    end
'''
  if candidate:body+='    assign observed_cache=prepared_header_padding_ok;\n    assign owner_complete=padding_owner_valid && padding_owner_next==128;\n'
  body+='endmodule\n';sources.append(pre+body)
 top='''module padding_probe(
    input logic clk,reset,start,abort_packet,
    input logic [7:0] state,byte_value,
    input logic [31:0] header_index,receipt_epoch,size_bytes,snapshot_fid,
    input logic snapshot_valid,
    input logic [63:0] snapshot_generation,
    input logic [34:0] header_packet_total,
    output logic old_padding,new_padding,new_cache,new_owner_complete,mismatch,
    output logic [7:0] old_error,new_error
);
'''
 common='''        .clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),
        .state(state),.byte_value(byte_value),.header_index(header_index),
        .receipt_epoch(receipt_epoch),.size_bytes(size_bytes),.snapshot_fid(snapshot_fid),
        .snapshot_valid(snapshot_valid),.snapshot_generation(snapshot_generation),
        .header_packet_total(header_packet_total),
'''
 top+='    padding_original_kernel original(\n'+common+'''        .observed_padding(old_padding),.error(old_error)
    );
    padding_candidate_kernel candidate(
'''+common+'''        .observed_padding(new_padding),.error(new_error),.observed_cache(new_cache),.owner_complete(new_owner_complete)
    );
    assign mismatch=(old_padding!=new_padding)||(old_error!=new_error);
endmodule
'''
 return '\n'.join(sources)+top,f


def build_files():
 bundle,fragments=build()
 starts=list(re.finditer(r'^module (\w+)\(',bundle,re.M))
 assert len(starts)==3
 outputs={}
 for i,match in enumerate(starts):
  end=starts[i+1].start() if i+1<len(starts) else len(bundle)
  outputs[match.group(1)+'.sv']=bundle[match.start():end]
 assert ''.join(outputs.values())==bundle
 return outputs,fragments


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 files,f=build_files();target=V/'padding_probe.sv';bench=V/'tb_padding.cpp'
 if a.write:
  V.mkdir(exist_ok=True)
  for name,text in files.items():
   out=V/name;assert not out.exists(),'Never overwrite prepared fixture';out.write_text(text)
 assert all((V/name).read_text()==text for name,text in files.items())
 if bench.exists():
  recipe={'schema':'v128-padding-source-extraction-v1','status':'FIXTURE_PREPARED_NOT_RTL_EXECUTED','preparer':pin(Path(__file__)),'original':pin(OLD),'candidate':pin(NEW),'target':pin(target),'kernel_modules':[pin(V/name) for name in files],'kernel_bundle_sha256':hashlib.sha256(''.join(files.values()).encode()).hexdigest(),'bench':pin(bench),'source_fragments':f,
   'private_new_payload_or_owner_forces':0,'scoped_source_kernel':True,'full_admission_model':False,'actual_FSM_executed':False,
   'verification_adaptations':['Evaluate the source local padding expression in combinational temporary evaluated_padding; NBA-capture its held observable value only on original noncancel HEADER_CHECK edge; unchanged reject predicates read current evaluated_padding.','Retain source HEADER_BYTE/header-write and HEADER_CHECK consumers with original reset/start/abort priority.','Copy original ordered error4..8 predicates exactly; replace reject task actions by corresponding error assignment and success by error0.','Parameterize source-state/header-index ports as prepared contexts; these are not natural fetch/read caller transactions.'],
   'kernel_includes_current_byte_forwarding':True,'kernel_includes_original_and_new_owner_assertions':True,'seeds':[128701,128702],
   'full_component_actual_admission_required_separately':True}
  if a.write:(AREA/'verification-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
  elif (AREA/'verification-recipe.json').exists():assert json.loads((AREA/'verification-recipe.json').read_text())==recipe
 print(json.dumps({'status':'PASS_READONLY_EXTRACTION' if not a.write else 'PREPARED_NOT_RTL_EXECUTED','source_fragments':len(f),'kernel_modules':len(files),'target_sha256':sha(target),'bench_present':bench.exists()}))
if __name__=='__main__':main()
