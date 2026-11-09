#include "Vscratch_probe___024root.h"
#include "tb_prepare.cpp"
// The inherited class keeps its exact three-edge adapter. This alias below is
// only for declared private storage fixtures, clocked against the real old RTL.
#undef Vscratch_probe
static void slot_conservation(const Vscratch_probe&d){need(d.verify_tile_events==d.verify_tile_commits+unsigned(d.verify_tile_slot_valid),"one-slot event/commit/pending conservation");}
static std::array<uint32_t,64> visible(const Vscratch_probe&d){std::array<uint32_t,64>a{};for(unsigned i=0;i<64;++i)a[i]=d.verify_tile_visible[i];return a;}
static void expect_private(const Vscratch_probe&d,const std::array<uint32_t,64>&a){for(unsigned i=0;i<64;++i)need(d.verify_tile_visible[i]==a[i]&&d.verify_tile_private[i]==a[i],"warm kill/drain erased already-visible tile write");}
#define OLD(n) d.rootp->scratch_probe__DOT__original__DOT__##n
#define NEW(n) d.rootp->scratch_probe__DOT__candidate__DOT__##n
#define BOTH(n,v) do{OLD(n)=(v);NEW(n)=(v);}while(0)
static void edge(Vscratch_probe&d){d.clk=d.reference_clk=0;d.eval();need(!d.mismatch,"private storage fixture preedge raw/public mismatch");std::cout<<"{\"type\":\"private_storage_edge\",\"state\":"<<unsigned(d.debug_state)<<",\"read_band\":"<<unsigned(d.verify_read_band)<<",\"cache_valid\":"<<unsigned(d.debug_cache_valid)<<",\"event\":"<<unsigned(d.verify_tile_event_valid)<<",\"pending\":"<<unsigned(d.verify_tile_slot_valid)<<"}\n"<<std::flush;d.clk=d.reference_clk=1;d.eval();need(!d.mismatch,"private storage fixture postedge raw/public mismatch");d.clk=d.reference_clk=0;d.eval();need(!d.mismatch,"private storage fixture held raw/public mismatch");slot_conservation(d);}
static void setup(Vscratch_probe&d,unsigned state,unsigned bank,unsigned index,int value){
 d.reset=0;d.abort_valid=0;d.mem_rsp_valid=0;d.mem_rsp_error=0;d.mem_rsp_epoch=9;d.dense_ready=0;
 BOTH(state,state);BOTH(busy_owned,state!=0&&state!=23&&state!=24);BOTH(raw_mode,0);BOTH(tile_overlap_mode,0);BOTH(prep_bank,bank);BOTH(emit_bank,1-bank);BOTH(bank_ready,0);BOTH(tile_preparing,0);BOTH(prefetch_mode,0);BOTH(prefetched_valid,0);BOTH(sealed,0);BOTH(done,0);BOTH(error,0);BOTH(blocks,1);BOTH(output_block,0);BOTH(prepare_block,0);BOTH(serial_clear,1);BOTH(clear_index,index);BOTH(outstanding,0);BOTH(prefetch_offer,0);BOTH(write_slot_valid,0);BOTH(overlap_mode,0);BOTH(request_epoch,9);BOTH(read_address,32);BOTH(read_segment,0);BOTH(read_band,1);BOTH(head_valid,0);BOTH(counts[0],1);BOTH(used_bytes,96);BOTH(assembly_bytes,0);
 // Construct a complete coherent cache/head poststate, including the original
 // all-offset predecoded-position invariant. Do not disable those assertions.
 for(unsigned band=0;band<4;++band){
  for(unsigned word=0;word<4;++word){OLD(cache_data)[band][word]=0;NEW(cache_data)[band][word]=0;}
  OLD(cache_address)[band]=band?48+16*(band-1):32;NEW(cache_address)[band]=OLD(cache_address)[band];
  OLD(starts)[band]=OLD(cache_address)[band];NEW(starts)[band]=OLD(starts)[band];
  if(band){OLD(counts)[band]=NEW(counts)[band]=0;OLD(cursors)[band-1]=NEW(cursors)[band-1]=0;OLD(heads)[band-1]=NEW(heads)[band-1]=0;OLD(head_positions)[band-1]=NEW(head_positions)[band-1]=0;}
 }
 OLD(cache_data)[0][0]=unsigned(value)&65535;NEW(cache_data)[0][0]=unsigned(value)&65535;
 unsigned valid=1;
 if(state==17){
  const unsigned rank=ranks[index];need(rank!=0&&value!=0&&value>=-2048&&value<=2048,"prepared AC record is outside a legal band/domain");const unsigned band=rank<6?1:rank<21?2:3,record=(index<<13)|(unsigned(value)&8191);
  BOTH(read_band,band);BOTH(read_segment,band);BOTH(read_address,48+16*(band-1));BOTH(head_valid,1U<<(band-1));OLD(counts)[band]=NEW(counts)[band]=1;OLD(cursors)[band-1]=NEW(cursors)[band-1]=1;OLD(heads)[band-1]=NEW(heads)[band-1]=record;OLD(head_positions)[band-1]=NEW(head_positions)[band-1]=position(record);OLD(cache_data)[band][0]=NEW(cache_data)[band][0]=record;valid|=1U<<band;
 }
 BOTH(cache_valid,valid);
 for(unsigned band=0;band<4;++band)for(unsigned offset=0;offset<16;++offset){
  uint32_t word=0;for(unsigned byte=0;byte<4&&offset+byte<16;++byte){const unsigned at=offset+byte;word|=((OLD(cache_data)[band][at/4]>>((at%4)*8))&255U)<<(byte*8);}
  OLD(cache_positions)[band][offset]=NEW(cache_positions)[band][offset]=position(word);
 }
 NEW(read_tag_match)=1;
}
static void raw_fixtures(unsigned&events,unsigned&guards,unsigned&held){
 Vscratch_probe d;d.clk=d.reference_clk=0;d.pair_enable=1;d.reset=1;d.begin_valid=d.coef_valid=d.band_end_valid=d.seal_valid=d.abort_valid=d.mem_req_ready=d.mem_rsp_valid=d.mem_rsp_error=d.dense_ready=0;d.abort_epoch=0;d.begin_blocks=1;d.begin_raw=d.begin_serial_clear=d.begin_overlap=d.begin_prefetch=d.begin_tile_overlap=0;d.begin_count1=d.begin_count2=d.begin_count3=d.begin_epoch=0;d.coef_band=d.coef_block=d.coef_index=d.coef_value=d.coef_epoch=d.band_end_band=d.band_end_epoch=d.seal_epoch=d.mem_rsp_epoch=0;for(unsigned k=0;k<4;++k)d.mem_rsp_data[k]=0;edge(d);d.reset=0;
 std::array<uint16_t,128> expected{};
 auto check=[&](){for(unsigned i=0;i<128;++i)need(get(d.verify_tile_visible,i*16,16)==expected[i],"independent all-word private-storage golden");};
 auto write=[&](unsigned state,unsigned bank,unsigned index,int value){setup(d,state,bank,index,value);d.eval();need(d.verify_tile_event_valid,"declared real event branch missing");expected[bank*64+(state==16?0:index)]=uint16_t(state==14?0:value);edge(d);check();++events;};
 // Consecutive real CLEAR/DC/AC branches target repeated and different words.
 // These are explicitly prepared private contexts, not packet-reachability claims.
 write(14,0,0,0);write(16,0,0,37);write(14,0,0,0);write(17,0,7,-2048);write(17,1,63,2048);write(14,1,63,0);write(16,1,0,-1);write(16,1,0,23);
 need(d.verify_tile_back_to_back>=7,"back-to-back zero/data/replacement fixture missing");
 // A completed logical bank remains unchanged while its pending value retires.
 auto saved=visible(d);setup(d,25,0,0,0);BOTH(tile_overlap_mode,1);BOTH(bank_ready,2);BOTH(bank_block[1],0);BOTH(bank_epoch[1],0);edge(d);check();expect_private(d,saved);++held;edge(d);check();++held;
 // Matching tagged error reaches AC_CHECK when neither prefetch nor write owner
 // takes an earlier error branch. Preserve that late raw write exactly.
 setup(d,17,0,5,303);BOTH(outstanding,1);d.mem_rsp_valid=d.mem_rsp_error=1;d.eval();need(d.verify_tile_event_valid,"matching unowned-error case incorrectly gated by response_failure");expected[5]=303;edge(d);check();++events;
 // Every earlier branch suppresses a new event while retiring the old tuple.
 for(unsigned kind=0;kind<5;++kind){setup(d,17,1,4,404);d.mem_rsp_valid=1;d.mem_rsp_error=1;BOTH(outstanding,1);
  if(kind==0){BOTH(outstanding,0);} // unsolicited
  if(kind==1)d.mem_rsp_epoch=8; // mismatched tagged reply
  if(kind==2){BOTH(prefetch_offer,1);} // prefetch-owned error
  if(kind==3){BOTH(overlap_mode,1);BOTH(write_slot_valid,1);} // write-owned error
  if(kind==4){BOTH(state,25);} // existing DRAIN state
  d.eval();need(!d.verify_tile_event_valid,"outer-priority guard leaked a tile event");edge(d);check();++guards;
 }
 setup(d,25,0,0,0);auto before=visible(d);edge(d);expect_private(d,before);check();
 need(d.verify_tile_events==events&&d.verify_tile_commits==events&&!d.verify_tile_slot_valid&&d.verify_tile_zero_events>0&&d.verify_tile_data_events>0,"private fixture final finite slot ledger");
}
int main(int argc,char**argv){try{
 need(inherited_prepare_main(argc,argv)==0,"entire immutable V115 paired scratch suite");const unsigned seed=unsigned(std::stoul(argv[1]));std::ofstream trace(std::string(argv[2])+"-slot.jsonl");need(bool(trace),"slot trace open");unsigned kills=0,retries=0,raw_events=0,guards=0,held=0;
 for(unsigned tile_mode=0;tile_mode<2;++tile_mode)for(unsigned reset=0;reset<2;++reset)for(unsigned zero=0;zero<2;++zero){
  auto p=packet(3,false,seed+kills+77);ProbeBench b(seed+kills+5000,trace);b.ingest(p,7U|(tile_mode<<3));
  for(unsigned n=0;!(b.d.verify_tile_slot_valid&&bool(b.d.verify_tile_slot_value==0)==bool(zero));++n){need(n<20000,"natural pending zero/data tile write setup watchdog");b.tick();}
  need(b.d.verify_tile_events==b.d.verify_tile_commits+1,"natural write not in one local pending slot");const auto saved=visible(b.d);b.abort_and_drain(reset!=0);need(!b.d.verify_tile_slot_valid,"kill did not retire old pending tuple");expect_private(b.d,saved);slot_conservation(b.d);++kills;
  b.ingest(p,7U|(tile_mode<<3));b.finish();need(b.d.verify_tile_events==b.d.verify_tile_commits&&!b.d.verify_tile_slot_valid,"full retry retained tile write debt");slot_conservation(b.d);++retries;
 }
 raw_fixtures(raw_events,guards,held);need(kills==8&&retries==8&&raw_events==9&&guards==5&&held==2,"additive tile-slot coverage incomplete");
 std::cout<<"{\"type\":\"refined_scratch_slot_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"original_full_transactions\":72,\"original_corrupt_response_cases\":128,\"original_read_owner_cases\":4,\"original_boundary_transactions\":48,\"original_pending_cancel_cases\":12,\"original_complete_retry_transactions\":24,\"natural_pending_kills\":"<<kills<<",\"same_object_full_retries\":"<<retries<<",\"private_storage_event_fixtures\":"<<raw_events<<",\"outer_priority_guard_fixtures\":"<<guards<<",\"ready_bank_hold_edges\":"<<held<<",\"visible_raw_words_compared_per_checked_edge\":128,\"new_public_cycles\":0,\"old_assertions_removed\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<"REFINED_SCRATCH_FAIL "<<e.what()<<'\n';return 1;}}
