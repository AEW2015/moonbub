#include "Vcu71_direct_prepare_adapter.h"
#include "verilated.h"
#include <cstdio>
#include <stdexcept>
static unsigned checks=0;
static void need(bool x,const char*why){++checks;if(!x)throw std::runtime_error(why);}
int main(){try{
 Vcu71_direct_prepare_adapter d;
 auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();d.clk=0;d.eval();};
 auto reset=[&](){d.rst=1;d.kill=0;d.start_valid=0;d.result_ready=0;d.descriptor_accepted=0;d.owner_prepared_valid=0;d.owner_abort_done=0;d.owner_abort_error=0;d.owner_abort_ready=0;d.owner_prepare_ready=0;tick();need(!d.worker_drained&&!d.start_ready,"reset admitted/drained");d.rst=0;tick();need(d.worker_drained&&!d.busy&&!d.fault,"reset recovery");};
 auto begin=[&](unsigned id){d.generation=1000+id;d.frame_id=id;d.canonical_bank=1;d.hud_bank=1;d.cache_slot=id&1;d.start_valid=1;d.owner_prepare_ready=0;d.eval();need(d.owner_prepare_valid&&!d.start_ready,"prepare backpressure");tick();need(d.worker_drained,"unaccepted prepare owned context");d.owner_prepare_ready=1;tick();d.start_valid=0;d.owner_prepare_ready=0;d.eval();need(d.busy&&!d.worker_drained,"accepted prepare not owned");};
 auto result=[&](bool error){d.owner_prepared_generation=d.generation;d.owner_prepared_frame_id=d.frame_id;d.owner_prepared_slot=d.cache_slot;d.owner_prepared_error=error;d.owner_prepared_reason=error?0x44:0;d.owner_prepared_valid=1;d.result_ready=0;d.eval();need(d.result_valid&&!d.owner_prepared_ready,"held result lost");tick();need(d.result_valid&&!d.worker_drained,"result consumed without ready");d.result_ready=1;tick();d.owner_prepared_valid=0;d.result_ready=0;d.eval();};
 auto cancel=[&](bool error){d.kill=1;d.owner_abort_ready=0;d.eval();need(!d.worker_drained&&d.owner_abort_valid,"kill released live provisional lease");need(d.owner_abort_generation==d.generation&&d.owner_abort_frame_id==d.frame_id&&d.owner_abort_slot==d.cache_slot,"abort identity");for(int i=0;i<5;i++){tick();need(!d.worker_drained&&d.owner_abort_valid,"abort offer lost");}d.owner_abort_ready=1;tick();d.owner_abort_ready=0;for(int i=0;i<9;i++){tick();need(!d.worker_drained&&!d.owner_abort_valid,"drain fabricated before actual abortdone");}d.owner_abort_error=error;d.owner_abort_done=1;tick();d.owner_abort_done=0;d.owner_abort_error=0;need(bool(d.worker_drained)==!error,"abort completion fence");d.kill=0;tick();};
 reset();begin(1);result(false);need(d.worker_drained&&!d.busy,"READY work not drained");cancel(false);need(!d.fault,"normal abort fault");
 begin(2);cancel(false);need(!d.fault,"ACTIVE cancellation fault");
 begin(3);result(false);d.descriptor_generation=d.generation;d.descriptor_frame_id=d.frame_id;d.descriptor_slot=d.cache_slot;d.descriptor_accepted=1;tick();d.descriptor_accepted=0;d.kill=1;d.eval();need(d.worker_drained&&!d.owner_abort_valid,"committed descriptor rolled back");for(int i=0;i<8;i++){tick();need(!d.owner_abort_valid,"lost softwareACK caused cancel");}d.kill=0;tick();
 begin(4);result(true);need(d.worker_drained&&!d.busy,"failed prepared result retained freed context");
 begin(5);d.owner_prepared_generation=d.generation-1;d.owner_prepared_frame_id=d.frame_id;d.owner_prepared_slot=d.cache_slot;d.owner_prepared_valid=1;d.result_ready=1;tick();need(!d.result_valid&&!d.owner_prepared_ready&&d.fault&&!d.worker_drained,"stale prepared identity accepted");d.owner_prepared_valid=0;d.result_ready=0;cancel(false);need(d.fault,"stale diagnostic cleared");
 reset();begin(6);cancel(true);need(d.fault&&d.busy&&!d.worker_drained,"failed cancellation released ownership");reset();
 begin(7);result(false);d.descriptor_generation=d.generation;d.descriptor_frame_id=d.frame_id+1;d.descriptor_slot=d.cache_slot;d.descriptor_accepted=1;tick();d.descriptor_accepted=0;need(d.fault&&!d.worker_drained,"wrong descriptor released lease");reset();
 begin(8);d.owner_prepared_generation=d.generation;d.owner_prepared_frame_id=d.frame_id;d.owner_prepared_slot=d.cache_slot;d.owner_prepared_error=0;d.owner_prepared_valid=1;d.result_ready=1;d.kill=1;d.eval();need(!d.result_valid&&!d.owner_prepared_ready,"coincident kill leaked prepare success");d.owner_prepared_valid=0;d.result_ready=0;cancel(false);
 std::printf("DY71_PREPARE_ADAPTER_PASS checks=%u actual_abortdone_required=1 committed_context_not_cancelled=1\n",checks);return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ADAPTER_FAIL %s\n",e.what());return 1;}}
