"""Keep frozen compare monitors; replace its candidate ACK actor with RTL service."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
s=(ROOT/'fpga/experiments/cu66-v91l-rows/tb_compare.cpp').read_text()
def replace(a,b):
 global s
 assert a in s,a[:90]
 s=s.replace(a,b)
replace('Vcs88_rows_v91l','Vshared_live')
# Candidate ready/response are now exclusively driven by actual physical RTL.
a=s.index('      d.candidate_req_ready=',s.index('void live_before_eval'))
b=s.index('      d.software_hud_valid=',a)
s=s[:a]+s[b:]
replace('d.candidate_rsp_valid=0;d.candidate_req_ready=0;','')
replace('candidate_pending=CandidatePending{q,cycle+payload_beats+overhead};','candidate_pending=CandidatePending{q,cycle};')
replace('const unsigned payload_beats=(q.bytes+1)/2,overhead=profile?2+random(6):1;','const unsigned payload_beats=(q.bytes+1)/2,overhead=0;')
# Mirror receipt is observation only; fail if actual physical response disagrees.
replace('auto q=candidate_pending->q;\n        const unsigned written=', 'auto q=candidate_pending->q;need(d.candidate_rsp_epoch==q.epoch&&d.candidate_rsp_token==q.token&&d.candidate_rsp_bank==q.bank&&d.candidate_rsp_addr==q.addr&&!d.candidate_rsp_error,"actual physical candidate ACK identity");\n        const unsigned written=')
replace('d.clk=0;live_before_eval();','d.clk=0;live_before_eval();d.rgb_out_ready=random(5)!=0;')
replace('d.eval();live_observe();const bool cancel=', 'd.eval();live_observe();rgb_observe();const bool cancel=')
replace('d.clk=1;d.eval();++cycle;live_after_edge();','advance(Verilated::time()+5000);d.clk=1;d.eval();++cycle;live_after_edge();advance(Verilated::time()+5000);d.clk=0;d.eval();')
replace('        d.clk=0;d.reset=1;', '        d.rgb_reset=0;d.rgb_cancel=0;d.rgb_start=0;d.rgb_start_epoch=0;d.rgb_start_generation=0;d.rgb_start_bank=0;d.rgb_out_ready=0;d.fabric_peek_addr=0;\n        d.clk=0;d.reset=1;')
replace('d.power_on_reset=0;d.reset=0;tick();','d.power_on_reset=0;d.reset=0;tick();for(unsigned n=0;n<1000&&!d.fabric_controller_ready;n++)tick();need(d.fabric_controller_ready,"physical controller cold initialization");')
replace('      record=false;tick();','      full_rgb();record=false;tick();')
replace('commit_cycle=cycle;','commit_cycle=cycle;native_roles("native_commit",Verilated::time(),cycle);')
replace('d.start=1;begin_cycle=cycle;tick();d.start=0;','d.start=1;begin_cycle=cycle;tick();d.start=0;native_roles("native_start",Verilated::time()-5000,begin_cycle);')
replace('      }\n    }\n    void drain_live()', '      }\n      if(d.v_frame_presented&&physical_events)native_roles("native_presented",Verilated::time(),cycle);\n    }\n    void drain_live()')
replace('    static uint32_t be32(', (AREA/'bench_extension.inc').read_text()+'\n    static uint32_t be32(')
s=s[:s.index('int main(')]+r'''int main(int argc,char **argv){try{
 need(argc==13,"usage: cases transforms canonical validation seed events actual hashes bus rgb-golden physical-events output-directory");Verilated::commandArgs(argc,argv);
 auto cases=load(argv[1]);load_tiles(argv[2]);load_validation(argv[4]);unsigned seed=unsigned(std::stoul(argv[5]));Bench b(seed,argv[6],argv[3],argv[7]);b.hash_events.open(argv[8]);need(bool(b.hash_events),"hash events output");b.bus_events.open(argv[9],std::ios::binary);need(bool(b.bus_events),"bus events output");b.configure_rgb(argv[10],argv[11],argv[12]);
 auto find=[&](const std::string &id)->const Case&{for(const auto &c:cases)if(c.id==id)return c;throw std::runtime_error("case missing "+id);};
 // Fault injections retain their original logical actor in the separate frozen control campaign.
 // This experiment uses only real matching ACKs from the unchanged physical controller.
 b.cold_live();b.nominal(find("actual_001"),0);
 b.hold_presentation=true;b.nominal(find("actual_006"),0);
 need(b.d.v_front_fid==0&&b.d.v_pending_valid&&b.d.v_pending_fid==1,"pending live presentation fence");
 for(unsigned n=0;n<17;++n){b.tick();need(b.d.v_front_fid==0&&b.d.v_pending_valid,"front changed without vblank");}
 b.native_roles("publication_wait_vblank",Verilated::time()-5000,b.cycle);
 b.hold_presentation=false;b.hold_scanout=true;for(unsigned n=0;n<17;++n){b.tick();need(b.d.v_front_fid==0&&b.d.v_pending_valid,"front changed with scanout owner");}
 b.native_roles("publication_wait_scanout",Verilated::time()-5000,b.cycle);
 b.hold_scanout=false;b.tick();need(b.d.v_frame_presented&&b.d.v_front_fid==1&&!b.d.v_pending_valid,"actual pending frame did not present");
 need(!b.candidate_pending&&!b.pending&&!b.reference_pending&&!b.d.fabric_wr_pending&&!b.d.fabric_rd_pending&&!b.d.rgb_busy,"terminal shared owners");
 std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":2,\"profiles\":1,\"service\":\"actual_live_writes_validated_then_rgb_same_timed_physical_memory\",\"physical_preload\":false,\"scratch_reference_rtl\":false,\"full_rtl_hud_decoder\":false,\"hardware_30fps_proven\":false}\n";return 0;
}catch(const std::exception &e){std::cerr<<"SHARED_LIVE_TEST_FAIL "<<e.what()<<'\n';return 1;}}
'''
(AREA/'tb_shared_live.cpp').write_text('// Derived from frozen row comparison; physical ACK actor removed.\n'+s)
print('SHARED_LIVE_BENCH_GENERATED')
