//! Allocation-free bounded payload formatting; transport envelopes/pacing live in report_snapshot.
use core::fmt::Arguments;
use super::network_driver::{Error,Report,MAX_FRAMES};

pub fn report(r:&Report,mut emit:impl FnMut(Arguments<'_>)){
 emit(format_args!("summary ok=1 frames={} completed={} cache={}",r.frames,r.completed_records,r.cache_mode));
 emit(format_args!("counters accepted={} presented={} rejected={} underruns={}",r.accepted,r.presented,r.rejected,r.underruns));
 emit(format_args!("totals words_written={} words_verified={} elapsed_us={}",r.words_written,r.words_verified,r.elapsed_us));
 let retained=r.completed_records.min(MAX_FRAMES as u32);let first=r.completed_records-retained;
 emit(format_args!("ring capacity={} retained={} first={} omitted={}",MAX_FRAMES,retained,first,first));
 for ordinal in first..r.completed_records{
  let i=ordinal as usize%MAX_FRAMES;
  if r.record_index[i]!=ordinal{emit(format_args!("ring_error ordinal={} slot={} observed={}",ordinal,i,r.record_index[i]));continue}
  emit(format_args!("frame slot={} ordinal={} id={} generation={}",i,ordinal,r.frame_id[i],r.generation[i]));
  emit(format_args!("ingress ordinal={} packet={} admit={} pending={}",ordinal,r.packet_complete_us[i],r.admission_us[i],r.hud_pending_us[i]));
  emit(format_args!("request ordinal={} snapshot={}",ordinal,r.hud_snapshot_us[i]));
  if r.cache_mode{emit(format_args!("hu_ingress_span ordinal={} start={} done={} scalar_commands={}",ordinal,r.hu_extract_start_us[i],r.hu_extract_done_us[i],r.hu_extract_commands[i]));}
  else{emit(format_args!("hu_scalar_fetch ordinal={} start={} done={} commands={}",ordinal,r.hu_extract_start_us[i],r.hu_extract_done_us[i],r.hu_extract_commands[i]));}
  emit(format_args!("native ordinal={} start={} done={} cpu_us={}",ordinal,r.native_start_us[i],r.native_done_us[i],r.hud_cpu_us[i]));
  emit(format_args!("hud ordinal={} valid={} write_done={} readback_done={}",ordinal,r.hud_valid_us[i],r.hud_write_done_us[i],r.hud_readback_done_us[i]));
  emit(format_args!("final ordinal={} drained={} software_ack={} presentation={}",ordinal,r.hud_drained_us[i],r.software_commit_acked_us[i],r.presentation_observed_us[i]));
 }
 emit(format_args!("arena cap={} live={} peak={}",r.allocator[0],r.allocator[1],r.allocator[2]));
 emit(format_args!("arena largest={} allocations={} failures={}",r.allocator[3],r.allocator[4],r.allocator[5]));
}
pub fn failure(error:&Error,mut emit:impl FnMut(Arguments<'_>)){
 emit(format_args!("summary ok=0 error={:?} partial_stage_arrays_retained=false",error));
}
pub fn health(reads:u64,writes:u64,qspi:u64,free:usize,largest:usize,stack_low:usize,min_free:usize,mut emit:impl FnMut(Arguments<'_>)){
 emit(format_args!("io reads={} writes={} qspi_transactions={}",reads,writes,qspi));
 emit(format_args!("health free={} largest={} stack_low={} native_min_free={}",free,largest,stack_low,min_free));
}
