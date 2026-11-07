"""Derive frozen all-memory-clients bench; overlap immutable display and decoder."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
s=(ROOT/'fpga/experiments/cu66-v91l-scratch-live/tb_scratch_live.cpp').read_text()
def replace(before,after):
 global s
 assert before in s,before[:100]
 s=s.replace(before,after)
replace('Vscratch_live','Voverlap_live')
replace('      full_rgb();record=false;tick();','      decode_summaries();record=false;tick();')
replace('rgb_observe();reference_lines_observe();scratch_observe();','rgb_observe();reference_lines_observe();scratch_observe();')
replace('d.rgb_out_ready=random(5)!=0;', 'd.rgb_out_ready=random(5)!=0;if(guard_mode&&rgb_owner&&rgb_owner->fid==0&&rgb_pixels==345599&&(!guard_release_cycle||cycle<guard_release_cycle)){d.rgb_out_ready=0;++guard_hold_cycles;}')
replace('live_after_edge();advance(Verilated::time()+5000);d.clk=0;d.eval();', 'live_after_edge();advance(Verilated::time()+5000);d.clk=0;d.eval();rgb_after_edge();')
replace('      if(d.v_frame_presented&&physical_events)', '      if(d.v_frame_committed&&be32(vf->packet,8)==1){delta_commit=cycle;if(guard_mode){need(rgb_owner&&rgb_owner->fid==0&&d.display_active&&d.v_front_valid&&d.v_front_fid==0&&d.v_pending_valid&&d.v_pending_fid==1&&!d.display_effective_drained,"native guard commit escaped old display lease");guard_release_cycle=cycle+17;native_roles("publication_wait_actual_display",Verilated::time(),cycle);}}\n      if(d.v_frame_presented&&physical_events)')
replace('need((!d.v_reference_bank_valid||q.bank!=d.v_reference_bank)', 'need(!d.display_active||q.bank!=d.display_bank,"candidate write aliases real display lease");\n        need((!d.v_reference_bank_valid||q.bank!=d.v_reference_bank)')
# Every display observation uses a captured descriptor; decoding can change active/vf/epoch.
a=s.index('    void rgb_observe(){');b=s.index('    uint64_t scratch_read_requests=',a)
s=s[:a]+(AREA/'overlap_extension.inc').read_text()+'\n'+s[b:]
# Preserve raw external drain hint while exposing the actual lease-derived core gate.
replace('<<unsigned(d.present_drained)<<",\\\"cycle\\\":', '<<unsigned(d.display_effective_drained)<<",\\\"external_drained_hint\\\":"<<unsigned(d.present_drained)<<",\\\"display_active\\\":"<<unsigned(d.display_active)<<",\\\"display_bank\\\":"<<unsigned(d.display_bank)<<",\\\"display_epoch\\\":"<<d.display_epoch<<",\\\"display_fid\\\":"<<d.display_fid<<",\\\"display_generation\\\":"<<d.display_generation<<",\\\"cycle\\\":')
s=s[:s.index('int main(')]+r'''int main(int argc,char **argv){try{
 need(argc==14,"usage: cases transforms canonical validation seed events actual hashes bus rgb-golden physical-events output-directory guard");Verilated::commandArgs(argc,argv);
 auto cases=load(argv[1]);load_tiles(argv[2]);load_validation(argv[4]);unsigned seed=unsigned(std::stoul(argv[5]));Bench b(seed,argv[6],argv[3],argv[7]);b.guard_mode=std::stoul(argv[13])!=0;b.hash_events.open(argv[8]);need(bool(b.hash_events),"hash events output");b.bus_events.open(argv[9],std::ios::binary);need(bool(b.bus_events),"bus events output");b.configure_rgb(argv[10],argv[11],argv[12]);
 auto find=[&](const std::string &id)->const Case&{for(const auto &c:cases)if(c.id==id)return c;throw std::runtime_error("case missing "+id);};
 b.cold_live();b.nominal(find("actual_001"),0);
 for(unsigned n=0;n<100&&!b.d.v_front_valid;++n)b.tick();
 need(b.d.v_front_valid&&b.d.v_front_fid==0&&!b.d.v_pending_valid&&!b.d.display_active,"key must actually present before overlapping display");
 b.start_rgb();b.nominal(find("actual_006"),0);b.delta_begin=b.begin_cycle;
 need(b.delta_commit&&b.overlap_cycles>0&&b.contended_offer_cycles>0&&b.rgb_candidate_overlap_requests>0&&b.rgb_reference_overlap_requests>0&&b.rgb_scratch_overlap_requests>0,"native clients never actually contended during RGB");
 if(b.guard_mode){need(b.rgb_owner&&b.d.display_active&&b.d.v_front_fid==0&&b.d.v_pending_valid&&b.d.v_pending_fid==1,"guard display did not survive decode return");for(unsigned n=0;n<12;++n){b.tick();need(b.d.v_front_fid==0&&b.d.v_pending_valid&&!b.d.display_effective_drained,"old display lease failed to block presentation");}}
 b.wait_rgb();need(b.key_rgb_close>b.delta_begin,"no measured native decode/display overlap");
 for(unsigned n=0;n<100&&b.d.v_front_fid!=1;++n)b.tick();
 need(b.d.v_front_valid&&b.d.v_front_fid==1&&!b.d.v_pending_valid,"delta did not present after actual old display drain");
 b.start_rgb();b.wait_rgb();for(unsigned n=0;n<6;++n)b.tick();
 need(!b.candidate_pending&&!b.pending&&!b.reference_pending&&!b.d.fabric_wr_pending&&!b.d.fabric_rd_pending&&!b.d.rgb_busy&&!b.d.fabric_ref_busy&&!b.d.fabric_ref_pending&&!b.d.fabric_scratch_busy&&!b.d.fabric_scratch_pending&&b.d.fabric_mux_owner==0&&b.d.fabric_memory_owner==0&&!b.d.display_active,"terminal overlapped shared owners");
 b.service_summary();
 std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":2,\"profiles\":1,\"guard_mode\":"<<(b.guard_mode?"true":"false")<<",\"service\":\"actual_decode_display_overlap_same_timed_memory\",\"physical_preload\":false,\"scratch_rtl\":true,\"reference_rtl\":true,\"full_rtl_hud_decoder\":false,\"hardware_30fps_proven\":false}\n";return 0;
}catch(const std::exception &e){std::cerr<<"OVERLAP_LIVE_TEST_FAIL "<<e.what()<<'\n';return 1;}}
'''
(AREA/'tb_overlap_live.cpp').write_text('// Native decode/display overlap with real immutable consumer lease.\n'+s)
print('OVERLAP_LIVE_BENCH_GENERATED')
