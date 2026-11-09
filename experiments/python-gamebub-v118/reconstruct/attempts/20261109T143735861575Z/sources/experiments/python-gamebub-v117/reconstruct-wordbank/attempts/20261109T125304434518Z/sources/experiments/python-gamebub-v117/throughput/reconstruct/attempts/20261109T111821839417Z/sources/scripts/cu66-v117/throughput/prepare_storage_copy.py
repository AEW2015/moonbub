#!/usr/bin/env python3
"""Preserve the qualified initial R and derive the bounded private COPY CE cut."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v117-throughput'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def edits(text,steps):
 for e in steps:assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
 return text

def main():
 source=SRC/'cu66_reconstruct_stream_v91k.sv';bench=SRC/'tb_reconstruct.cpp';runner=ROOT/'scripts/cu66-v117/throughput/qualify_reconstruct.py'
 if (SRC/'reconstruct-storage-copy-recipe.json').exists():
  q=json.loads((SRC/'reconstruct-storage-copy-recipe.json').read_text());assert sha(source)==q['derived_sha256'];assert edits((ROOT/q['original']).read_text(),q['edits'])==source.read_text();print('V117_STORAGE_COPY_PREPARED_NOT_RUN');return
 assert sha(source)=='4dbd9c944f17507093513a0927cf71779842555b5b24e6b5e152db917ad6926a'
 assert sha(bench)=='01d502d1b946fc2e0f944e907011ea7ac08b19ceb697f212c1ac350f830c3022'
 initial=SRC/'initial';initial.mkdir()
 for p in [source,bench,runner,SRC/'reconstruct_probe.sv',SRC/'reconstruct-edit-recipe.json',SRC/'reconstruct-probe-recipe.json']:shutil.copyfile(p,initial/p.name)
 steps=[]
 def step(a,b):steps.append(dict(before=a,after=b))
 step('logic owner_head,owner_tail,owner_copy;','logic owner_head,owner_tail,owner_copy,storage_copy;')
 step('    assign owner_copy=running&&state==COPY&&!kill;','''    // The physical inactive-slot write has only registered local ownership.
    // On a kill edge the private copy may occur, but no logical owner is granted.
    assign storage_copy=state==COPY;
    assign owner_copy=running&&state==COPY&&!kill;''')
 step('always_ff @(posedge clk)if(owner_copy&&owner_tail==1\'(b))value<=engine_out_pixels[w*8+:8];','always_ff @(posedge clk)if(storage_copy&&owner_tail==1\'(b))value<=engine_out_pixels[w*8+:8];')
 step('always_ff @(posedge clk)if(owner_copy&&owner_tail==1\'(b))begin','always_ff @(posedge clk)if(storage_copy&&owner_tail==1\'(b))begin')
 extra='''`ifndef SYNTHESIS
    logic revoked_storage_copy_checked;
    always_ff @(posedge clk)begin
        if(!owner_initialized)revoked_storage_copy_checked<=0;
        else begin
            if(revoked_storage_copy_checked)assert(owner_state[0]==O_FREE&&owner_state[1]==O_FREE&&!out_valid)
                else $fatal(1,"killed private reconstruction copy acquired a logical owner");
            revoked_storage_copy_checked<=storage_copy&&kill;
            if(storage_copy)begin
                assert(owner_state[owner_tail]==O_MATH&&engine_out_valid)
                    else $fatal(1,"private reconstruction copy without reserved complete response");
                assert(owner_state[owner_head]!=O_READY||owner_tail!=owner_head)
                    else $fatal(1,"private reconstruction copy overwrote READY head");
                if(kill)assert(!owner_copy&&!out_valid)else $fatal(1,"killed reconstruction copy published");
                else assert(owner_copy)else $fatal(1,"normal private and logical reconstruction copy diverged");
            end
        end
    end
`endif
'''
 step('endmodule',extra+'endmodule');source.write_text(edits(source.read_text(),steps))
 q=json.loads((initial/'reconstruct-edit-recipe.json').read_text());q['edits']+=steps;q['derived_sha256']=sha(source);q['contract']+=' Physical payload COPY enable is registered COPY/bank only; immediate logical publication/engine consume remains kill-masked.';write(SRC/'reconstruct-edit-recipe.json',q)
 write(SRC/'reconstruct-storage-copy-recipe.json',dict(schema='v117-private-copy-control-cut-v1',original=rel(initial/source.name),original_sha256=sha(initial/source.name),derived=rel(source),derived_sha256=sha(source),edits=steps,original_logical_copy_mask_retained=True,all_initial_assertion_blocks_retained=True,qualified_initial_receipt='experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T110312411774Z/receipt.json',qualified_initial_receipt_sha256=sha(ROOT/'experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T110312411774Z/receipt.json')))
 bsteps=[]
 def bstep(a,b):bsteps.append(dict(before=a,after=b))
 bstep('full_owner_cycles=0,fixture_drains=0;','full_owner_cycles=0,fixture_drains=0,private_copy_cancel_cases=0;')
 bstep(' auto&r(){return *d.rootp;}',''' auto&r(){return *d.rootp;}
 std::array<uint32_t,16> storage(unsigned bank){std::array<uint32_t,16> a{};for(unsigned w=0;w<16;++w)a[w]=r().reconstruct_probe__DOT__owner_pixels[bank][w];return a;}
 std::array<uint32_t,16> engine_storage(){std::array<uint32_t,16> a{};for(unsigned w=0;w<16;++w)a[w]=r().reconstruct_probe__DOT__engine_out_pixels[w];return a;}''')
 bstep(' // Reset/cancel over all gather/memory/conversion/copy phases and stalled final byte.',''' // Kill at second COPY while a different, older READY head is stalled.
 // The inactive payload really captures, while publication revokes and the
 // entire previously offered head storage remains byte-exact.
 for(bool reset:{false,true}){b.phase="private_copy_kill_"+std::to_string(reset);b.begin(true);b.hold_output=true;b.until_state(11);b.step();b.until_state(11);
  const unsigned head=b.r().reconstruct_probe__DOT__owner_head,tail=b.r().reconstruct_probe__DOT__owner_tail;
  need(head!=tail&&b.d.out_valid&&!b.d.out_ready,"second COPY did not retain older stalled head");
  const auto saved_head=b.storage(head),expected_private=b.engine_storage();const unsigned expected_id=b.r().reconstruct_probe__DOT__engine_out_id;
  b.cancel(reset);need(b.storage(head)==saved_head,"kill COPY overwrote stalled head storage");
  need(b.storage(tail)==expected_private&&b.r().reconstruct_probe__DOT__owner_math_id[tail]==expected_id,"inactive COPY did not physically capture on kill edge");
  need(!b.d.out_valid&&b.owners()==0&&!b.d.done,"killed private COPY published a logical owner");
  ++b.private_copy_cancel_cases;++directed;b.begin(true);b.prefix();b.cancel();
 }
 // Reset/cancel over all gather/memory/conversion/copy phases and stalled final byte.''')
 bstep('<<",\\\"key_frame_cycles\\\":"<<key_cycles','<<",\\\"private_copy_cancel_cases\\\":"<<b.private_copy_cancel_cases<<",\\\"key_frame_cycles\\\":"<<key_cycles')
 bench.write_text(edits(bench.read_text(),bsteps));write(SRC/'reconstruct-storage-bench-recipe.json',dict(schema='v117-private-copy-cancel-additive-bench-v1',original=rel(initial/bench.name),original_sha256=sha(initial/bench.name),derived=rel(bench),derived_sha256=sha(bench),edits=bsteps,old_semantic_checks_removed=0))
 probe=SRC/'reconstruct_probe.sv';pq=json.loads((SRC/'reconstruct-probe-recipe.json').read_text());body=source.read_text();at=body.index(');');adapter=body[:at].rstrip()+pq['probe_ports']+body[at:];adapter=adapter.replace(');',');'+pq['probe_assignment'],1).replace(pq['original_module'],pq['adapter_module'],1);probe.write_text(adapter);pq['production']['sha256']=sha(source);pq['adapter']['sha256']=sha(probe);pq['original_before_ports']=body[:at];write(SRC/'reconstruct-probe-recipe.json',pq)
 text=runner.read_text().replace("('reconstruct-edit-recipe.json',)","('reconstruct-edit-recipe.json','reconstruct-storage-copy-recipe.json','reconstruct-storage-bench-recipe.json')")
 text=text.replace("Path(__file__).resolve()]","Path(__file__).resolve(),SRC/'reconstruct-storage-copy-recipe.json',SRC/'reconstruct-storage-bench-recipe.json',SRC/'initial/cu66_reconstruct_stream_v91k.sv',SRC/'initial/tb_reconstruct.cpp',ROOT/'scripts/cu66-v117/throughput/prepare_storage_copy.py']")
 text=text.replace("and q['directed_checks']>=40", "and q['directed_checks']>=46 and q['private_copy_cancel_cases']==2")
 text=text.replace("all_original_assertion_blocks_retained=True,old_geometry_domain_retained", "all_original_assertion_blocks_retained=True,physical_copy_has_only_registered_local_CE=True,logical_copy_immediate_kill_mask_retained=True,old_geometry_domain_retained")
 runner.write_text(text)
 print('V117_STORAGE_COPY_PREPARED_NOT_RUN',sha(source),sha(bench),sha(runner))
if __name__=='__main__':main()
