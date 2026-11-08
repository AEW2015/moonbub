#!/usr/bin/env python3
"""Reversible V112 original-edge admission preparation and local bank validation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v112-control';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v112/control'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def build(old,expected,edits):
 assert sha(old)==expected,(old,sha(old));s=old.read_text()
 for before,after in edits:
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after,1)
 q=SRC/old.name;q.write_text(s);reverse=s
 for before,after in reversed(edits):
  assert reverse.count(after)==1;reverse=reverse.replace(after,before,1)
 assert reverse==old.read_text()
 return dict(original=str(old.relative_to(ROOT)),original_sha256=sha(old),candidate=str(q.relative_to(ROOT)),candidate_sha256=sha(q),edits=[dict(before=a,after=b,expected_occurrences=1) for a,b in edits])
def main():
 admission=ROOT/'fpga/experiments/cu66-v107-tables/cs88_admission_v91i2a.sv'
 geometry='''    // V112_VISIBILITY_BEGIN: private preparation on the existing predecessor
    // edge, using the successor key when GROUP_NEXT changes plane/tile.
    // The mask retains the generic uint32 t+k wrap and all four plane values.
    logic [15:0] group_visibility_mask;
    function automatic logic [15:0] visibility_mask(input logic [1:0] p,input logic [31:0] t);
        logic [15:0] m;
        begin
            for(integer k=0;k<16;k=k+1)
                m[k]=t+32'(k)<tile_count(p)&&!hidden(p,t+32'(k));
            return m;
        end
    endfunction
    function automatic logic [4:0] visibility_count(input logic [15:0] m);
        logic [1:0] pair_count [0:7];
        logic [2:0] quad_count [0:3];
        logic [3:0] oct_count [0:1];
        begin
            for(integer k=0;k<8;k=k+1)
                pair_count[k]={1'b0,m[2*k]}+{1'b0,m[2*k+1]};
            for(integer k=0;k<4;k=k+1)
                quad_count[k]={1'b0,pair_count[2*k]}+{1'b0,pair_count[2*k+1]};
            for(integer k=0;k<2;k=k+1)
                oct_count[k]={1'b0,quad_count[2*k]}+{1'b0,quad_count[2*k+1]};
            return {1'b0,oct_count[0]}+{1'b0,oct_count[1]};
        end
    endfunction
    always_ff @(posedge clk)begin
        if(state==HEADER_CHECK)group_visibility_mask<=visibility_mask(2'd0,32'd0);
        else if(state==GROUP_NEXT)begin
            if(tile==tile_count(plane))group_visibility_mask<=visibility_mask(plane+2'd1,32'd0);
            else group_visibility_mask<=visibility_mask(plane,tile);
        end
    end
`ifndef SYNTHESIS
    // Independent original scalar sum at the actual unchanged consume edge.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==GROUP_BEGIN)
        assert(32'(visibility_count(group_visibility_mask))==visible_group(plane,tile))
            else $fatal(1,"V112 prepared group visibility owner mismatch");
`endif
    // V112_VISIBILITY_END

'''
 ap=build(admission,'b149c94ba1a5dd7f1d09384126c762d0bb0de5aa664baa4b76c29c631aeb652e',[
 ('    task automatic reject',geometry+'    task automatic reject'),
 ('group_visible<=visible_group(plane,tile);mixed_ones<=0;',"group_visible<=32'(visibility_count(group_visibility_mask));mixed_ones<=0;")])
 scratch=ROOT/'fpga/experiments/cu66-v110-cursors/packed_scratch_v91g2.sv'
 old_bad='''17'(read_word[31:19])>=blocks || !rank_matches(read_band,read_position[5:0]) ||
                           $signed(read_word[12:0])==0 || $signed(read_word[12:0]) < -2048 ||
                           $signed(read_word[12:0]) > 2048 ||
                           (cursors[read_band]!=0 && read_position<={13'd0,head_positions[read_band]})'''
 local='''    // V112_BANK_VALIDATION_BEGIN: each bank validates its own payload before
    // read_segment selects a one-bit result. Owner/state/drain priority and
    // selected data payload remain unchanged; no speculative failure is used.
    logic [3:0] ac_bank_invalid;
    for(genvar validation_bank=0;validation_bank<4;validation_bank=validation_bank+1)begin: local_ac_validation
        wire [31:0] bank_word=32'(cache_data[validation_bank]>>(8*read_address[3:0]));
        wire [31:0] bank_position={13'd0,cache_positions[validation_bank][read_address[3:0]]};
        assign ac_bank_invalid[validation_bank]=17'(bank_word[31:19])>=blocks ||
            !rank_matches(read_band,bank_position[5:0]) ||
            $signed(bank_word[12:0])==0 || $signed(bank_word[12:0]) < -2048 ||
            $signed(bank_word[12:0]) > 2048 ||
            (cursors[read_band]!=0 && bank_position<={13'd0,head_positions[read_band]});
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!cancel&&!response_failure&&state==AC_EXTRACT &&
        cache_valid[read_segment]&&cache_address[read_segment]==18'(read_address & 32'hfffffff0))
        assert(ac_bank_invalid[read_segment]==('''+old_bad+'''))
            else $fatal(1,"V112 local AC validation mismatch");
`endif
    // V112_BANK_VALIDATION_END

'''
 sp=build(scratch,'ebc4ca022b00e9d41613155eb80859986a8a2fbb803b4541a72511105589a218',[
 ('    // Cursor payload is unowned',local+'    // Cursor payload is unowned'),
 ('if('+old_bad+') begin','if(ac_bank_invalid[read_segment]) begin')])
 write(SRC/'edit-recipe.json',dict(schema='v112-local-control-existing-edges-v1',production={Path(e['candidate']).name:e for e in (ap,sp)},added_public_cycles=0,all_original_assertions_retained=True,scope='Exact public and invalid-cycle behavior; no owner, drain, reset, metadata, counters or state transition changes. Geometry payload preparation only; scratch pure per-bank validation algebra.'))
 # Lossless production packaging for Verilator; native reads complete source.
 s=(SRC/admission.name).read_text();offsets=[s.index('module cu66_scale_tdp_v107 ('),s.index('module cu66_mode_store_v107 (')];parts=[s[:offsets[0]],s[offsets[0]:offsets[1]],s[offsets[1]:]]
 write(SRC/'packaging.json',dict(schema='v112-control-lossless-packaging-v1',production_sha256=sha(SRC/admission.name),split_byte_offsets=offsets,fragments=[dict(filename=n,bytes=len(t.encode()),sha256=hashlib.sha256(t.encode()).hexdigest())for n,t in zip(['cs88_admission_v91i2a.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv'],parts)]))
 # Complete-original/current-count adapters. Retain all inherited test code.
 adapters=[]
 def adapt(source,name,edits):
  s=source.read_text()
  for a,b in edits:assert s.count(a)==1,(source,a,s.count(a));s=s.replace(a,b,1)
  q=V/name;q.write_text(s);adapters.append(dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),path=str(q.relative_to(ROOT)),sha256=sha(q),edits=edits))
 adm=ROOT/'fpga/experiments/cu66-v107-tables';obs=json.loads((adm/'adapter.json').read_text())
 # Preserve inherited public-flat annotations used by original directed fixtures.
 old_adapter=(adm/'admission_candidate.sv').read_text()
 for variant,source in [('original',admission),('candidate',SRC/admission.name)]:
  # Derive annotations mechanically from frozen original candidate adapter.
  s=source.read_text();annotated=old_adapter.replace('module admission_candidate (','module cs88_admission_v91i2a (',1).replace(obs['extra_ports'],'\n);',1).replace(obs['assignments']['candidate'],'',1)
  clean=annotated.replace(' /* verilator public_flat_rw */','')
  assert clean==admission.read_text()
  # Annotation anchors are the unique declaration substrings around each mark.
  edits=[('module cs88_admission_v91i2a (','module admission_'+variant+' ('),('\n);\n    localparam logic [7:0] IDLE',obs['extra_ports']+'\n    localparam logic [7:0] IDLE'),('\nendmodule',obs['assignments']['candidate']+'\nendmodule')]
  for line in annotated.splitlines():
   if ' /* verilator public_flat_rw */' in line:edits.append((line.replace(' /* verilator public_flat_rw */',''),line))
  # Body includes helper modules: add port observations only at main endmodule.
  edits[2]=('\nendmodule\n\n// Isolated common-clock',obs['assignments']['candidate']+'\nendmodule\n\n// Isolated common-clock')
  adapt(source,'admission_'+variant+'.sv',edits)
 for n in ('admission_probe.sv','tb_admission.cpp'):adapt(adm/n,n,[])
 scr=ROOT/'fpga/experiments/cu66-v110-cursors/verification';a=json.loads((scr/'adapters.json').read_text())
 for variant,source in [('original',scratch),('candidate',SRC/scratch.name)]:
  edits=a['adapters'][0]['renames'];edits=[(x,y.replace('observed_original','observed_'+variant))for x,y in edits]
  adapt(source,'observed_'+variant+'.sv',edits)
 for n in ('scratch_probe.sv','tb_scratch.cpp','historical_hazards.cpp','tb_bank.cpp'):adapt(scr/n,n,[])
 # Combinational all-domain probe uses exactly the production functions.
 s=(SRC/admission.name).read_text()
 funcs=[]
 for name in ('hidden','tile_count','visible_group','visibility_mask','visibility_count'):
  start=s.index('    function automatic logic ',s.index('module cs88_admission'))
  import re
  match=re.search(r'    function automatic logic(?: \[.*?\])? '+name+r'\(',s)
  assert match,name
  end=s.index('    endfunction',match.start())+len('    endfunction')
  funcs.append(s[match.start():end])
 probe='module geometry_probe (input logic [1:0] p,input logic [31:0] t,input logic [15:0] raw_mask,output logic [15:0] mask,output logic [4:0] count,raw_count,output logic [31:0] original_count);\n'+'\n'.join(funcs)+'\n    assign mask=visibility_mask(p,t);\n    assign count=visibility_count(mask);\n    assign raw_count=visibility_count(raw_mask);\n    assign original_count=visible_group(p,t);\nendmodule\n'
 (V/'geometry_probe.sv').write_text(probe)
 write(V/'adapters.json',dict(schema='v112-complete-original-reference-adapters-v1',adapters=adapters,all_public_ports_including_invalid_and_counters=True,all_original_assertions_and_goldens_retained=True))
 write(AREA/'preparation.json',dict(status='PREPARED_NOT_RTL_QUALIFIED',source_overrides={e['original']:e['candidate']for e in (ap,sp)},source_sha256={e['candidate']:e['candidate_sha256']for e in (ap,sp)},recipe_sha256=sha(SRC/'edit-recipe.json'),adapter_sha256=sha(V/'adapters.json'),packaging_sha256=sha(SRC/'packaging.json')))
 print('V112_CONTROL_PREPARED',json.dumps({e['candidate']:e['candidate_sha256']for e in (ap,sp)}))
if __name__=='__main__':main()
