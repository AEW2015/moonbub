//! Allocation-free post-trial export. No bus, transport or driver state changes.
use core::fmt::Arguments;
use super::network_driver::{Error, Report};

pub fn report(r:&Report,mut emit:impl FnMut(Arguments<'_>)){
 emit(format_args!("DY71_NET summary success=true frames={} accepted={} presented={} rejected={} underruns={} elapsed_us={}",r.frames,r.accepted,r.presented,r.rejected,r.underruns,r.elapsed_us));
 emit(format_args!("DY71_NET words written={} verified={}",r.words_written,r.words_verified));
 for i in 0..(r.frames as usize).min(super::network_driver::MAX_FRAMES){
  emit(format_args!("DY71_NET slot={} ingress packet={} admit={} pending={}",i,r.packet_complete_us[i],r.admission_us[i],r.hud_pending_us[i]));
  emit(format_args!("DY71_NET slot={} extract snapshot={} start={} done={} commands={}",i,r.hud_snapshot_us[i],r.hu_extract_start_us[i],r.hu_extract_done_us[i],r.hu_extract_commands[i]));
  emit(format_args!("DY71_NET slot={} native start={} done={} cpu_us={}",i,r.native_start_us[i],r.native_done_us[i],r.hud_cpu_us[i]));
  emit(format_args!("DY71_NET slot={} hud valid={} write_done={} readback_done={}",i,r.hud_valid_us[i],r.hud_write_done_us[i],r.hud_readback_done_us[i]));
  emit(format_args!("DY71_NET slot={} final drained={} software_ack={} presentation={}",i,r.hud_drained_us[i],r.software_commit_acked_us[i],r.presentation_observed_us[i]));
 }
 emit(format_args!("DY71_NET arena cap={} live={} peak={}",r.allocator[0],r.allocator[1],r.allocator[2]));
 emit(format_args!("DY71_NET arena largest={} allocations={} failures={}",r.allocator[3],r.allocator[4],r.allocator[5]));
}
pub fn failure(error:&Error,mut emit:impl FnMut(Arguments<'_>)){
 emit(format_args!("DY71_NET summary success=false error={:?} partial_stages_retained=false",error));
}
pub fn health(reads:u64,writes:u64,qspi:u64,free:usize,largest:usize,stack_low:usize,min_free:usize,mut emit:impl FnMut(Arguments<'_>)){
 emit(format_args!("DY71_NET io reads={} writes={} qspi_transactions={}",reads,writes,qspi));
 emit(format_args!("DY71_NET health free={} largest={} stack_low={} native_min_free={}",free,largest,stack_low,min_free));
}
