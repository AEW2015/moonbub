#!/usr/bin/env python3
"""Derive scan lookahead candidate and byte-exact paired verification sources."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];SRC=R/'fpga/experiments/cu66-v130-spec-read/cs88_admission_v91i2a.sv';OUT=R/'fpga/experiments/cu66-v130-active-prefetch'
s=SRC.read_text()
old='''    logic active_cell [0:1349];'''
new='''    logic active_cell [0:1349];
    // Read on the existing MODE_END and preceding ACTIVE_SCAN edges.
    // The bit is unowned after cancel; no payload reset or extra public cycle.
    logic active_scan_value;
    always_ff @(posedge clk) begin
        if(state==MODE_END)
            active_scan_value<=active_cell[0];
        else if(state==ACTIVE_SCAN && active_index<1349)
            active_scan_value<=active_cell[active_index[10:0]+11'd1];
    end
`ifndef SYNTHESIS
    logic scan_owner_valid=0;
    logic [31:0] scan_owner_index, scan_owner_epoch;
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)scan_owner_valid<=0;
        else if(state==MODE_END)begin
            scan_owner_valid<=1;scan_owner_index<=0;scan_owner_epoch<=receipt_epoch;
        end else if(state==ACTIVE_SCAN && active_index<1349)begin
            scan_owner_valid<=1;scan_owner_index<=active_index+1;scan_owner_epoch<=receipt_epoch;
        end else if(state!=ACTIVE_SCAN)scan_owner_valid<=0;
    end
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==ACTIVE_SCAN)begin
        assert(active_index<=1350)else $fatal(1,"scan index outside reachable range");
        if(active_index<1350)begin
            assert(scan_owner_valid&&scan_owner_index==active_index&&scan_owner_epoch==receipt_epoch)
                else $fatal(1,"scan lookahead owner/index mismatch");
            assert(active_scan_value==active_cell[active_index[10:0]])
                else $fatal(1,"scan lookahead data mismatch");
        end
    end
`endif'''
old2='if(active_cell[active_index[10:0]])required_cells<=required_cells+1;'
new2='if(active_scan_value)required_cells<=required_cells+1;'
assert s.count(old)==s.count(old2)==1
candidate=s.replace(old,new,1).replace(old2,new2,1)
OUT.mkdir(exist_ok=True)
(OUT/'cs88_admission_v91i2a.sv').write_text(candidate)
marker='module cu66_scale_tdp_v107';a,b=s.split(marker,1);c,d=candidate.split(marker,1);assert b==d
for name,body in [('admission_original',a),('admission_candidate',c)]:
 assert body.count('module cs88_admission_v91i2a (')==1
 # Verification-only access for injected scan-map cases; not in production.
 for old_decl,new_decl in [
  ('logic active_cell [0:1349];','logic active_cell [0:1349] /* verilator public_flat_rw */;'),
  ('logic [7:0] state, fetch_return, word_return;','logic [7:0] state /* verilator public_flat_rw */, fetch_return, word_return;'),
  ('logic [31:0] mode_cursor, active_index, word_cursor, word_index;',
   'logic [31:0] mode_cursor, active_index /* verilator public_flat_rw */, word_cursor, word_index;')]:
  assert body.count(old_decl)==1;body=body.replace(old_decl,new_decl,1)
 (OUT/(name+'.sv')).write_text(body.replace('module cs88_admission_v91i2a (','module '+name+' (',1))
m,n=b.split('module cu66_mode_store_v107',1)
(OUT/'cu66_scale_tdp_v107.sv').write_text(marker+m)
(OUT/'cu66_mode_store_v107.sv').write_text('module cu66_mode_store_v107'+n)
(OUT/'admission_pair.sv').write_text((R/'fpga/experiments/cu66-v130-spec-read/admission_pair.sv').read_text())
tb=(R/'fpga/experiments/cu66-v130-spec-read/tb_pair.cpp').read_text()
tb=tb.replace('#include "Vadmission_pair.h"','#include "Vadmission_pair.h"\n#include "Vadmission_pair___024root.h"',1)
tb=tb.replace('need(argc==3,"usage: fixture seed");','need(argc==3||argc==4,"usage: fixture seed [bad_index]");',1)
anchor='  std::cout<<"{\\\"status\\\":\\\"PASS\\\",'
scan='''  // Verification-only state injection supplies boundary maps directly to both
  // complete RTL memories; ordinary fixture/cancel testing above remains intact.
  uint64_t scan_edges=0;unsigned scan_cases=0,scan_cancel_cases=0;
  auto seed_scan=[&](unsigned shape){
   need(d.key_frame,"scan injection requires completed key-frame fixture");
   for(unsigned i=0;i<1350;++i){
    const bool bit=shape==0?false:shape==1?true:((rng()&3U)==0);
    d.rootp->admission_pair__DOT__original__DOT__active_cell[i]=bit;
    d.rootp->admission_pair__DOT__candidate__DOT__active_cell[i]=bit;
   }
   d.rootp->admission_pair__DOT__original__DOT__state=12;
   d.rootp->admission_pair__DOT__candidate__DOT__state=12;
   d.replay_req=0;d.reset=d.start=d.abort_packet=0;tick();
   need(d.debug_state==13&&d.required_cells==0,"scan preload/entry");
  };
  auto full_scan=[&](unsigned shape){
   seed_scan(shape);unsigned sum=0;
   for(unsigned i=0;i<1350;++i){
    sum+=d.rootp->admission_pair__DOT__original__DOT__active_cell[i];tick();++scan_edges;
    need(d.debug_state==13&&d.required_cells==sum,"scan count/cycle mismatch");
   }
   tick();need(d.debug_state==14&&d.required_cells==sum,"scan terminal transition");++scan_cases;
   start_packet();finish_packet();
  };
  if(argc==4){
   need(std::string(argv[3])=="bad_index","unknown negative control");seed_scan(0);
   d.rootp->admission_pair__DOT__original__DOT__active_index=1351;
   d.rootp->admission_pair__DOT__candidate__DOT__active_index=1351;tick();
   throw std::runtime_error("out-of-range scan assertion not detected");
  }
  full_scan(0);full_scan(1);for(unsigned i=0;i<4;++i){full_scan(2);}
  for(unsigned at:{0U,1U,674U,1349U,1350U})for(unsigned kind=0;kind<3;++kind){
   seed_scan(2);for(unsigned i=0;i<at;++i){tick();++scan_edges;}
   need(d.debug_state==13,"scan cancellation position");cancel(kind);++scan_cancel_cases;
   start_packet(true,true);finish_packet();
  }
  need(scan_cases==6&&scan_cancel_cases==15,"scan coverage");
  std::cout<<"{\\\"type\\\":\\\"scan\\\",\\\"status\\\":\\\"PASS\\\",\\\"cases\\\":"<<scan_cases<<",\\\"scan_edges\\\":"<<scan_edges<<",\\\"cancellations\\\":"<<scan_cancel_cases<<"}"<<std::endl;
'''
assert tb.count(anchor)==1
(OUT/'tb_pair.cpp').write_text(tb.replace(anchor,scan+anchor,1))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'schema':'v130-active-lookahead-v1','source':str(SRC.relative_to(R)),'source_sha256':sha(SRC),'candidate_sha256':sha(OUT/'cs88_admission_v91i2a.sv'),'edits':[{'old':old,'new':new},{'old':old2,'new':new2}], 'contract':'unchanged public cycles; valid-qualified raw data inherited from speculative-read baseline','status':'PREPARED_NOT_QUALIFIED'}
(OUT/'derivation.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print('PREPARED',manifest['candidate_sha256'])
if __name__=='__main__':pass
