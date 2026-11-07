//! Explicit, one-page-per-command export. Never called by the packet workers.
use crate::streaming::{self, diagnostic_trace as trace};
use std::sync::atomic::{AtomicUsize, Ordering};
static SUMMARY_PAGE: AtomicUsize = AtomicUsize::new(0);
static COMPACT_PAGE: AtomicUsize = AtomicUsize::new(0);
static EVENT_PAGE: AtomicUsize = AtomicUsize::new(0);
const BASE_SUMMARY_PAGES: usize = 5 + trace::PHASE_COUNT + 4;
const SUMMARY_PAGES: usize = BASE_SUMMARY_PAGES + 8;
fn now() -> u64 { unsafe { esp_idf_svc::sys::esp_timer_get_time() as u64 } }
fn flags(p: trace::Position) -> u8 { u8::from(p.frame_valid) | (u8::from(p.offset_valid) << 1) }

#[inline(never)]
pub fn command(key: u8) {
    match key {
        b'M' | b'F' => {
            if !streaming::diagnostic_trace_idle() {
                log::info!("USB_TRACE rxdiag v=2 ctrl={} result=busy", key as char);
                return;
            }
            let ok = if key == b'M' { trace::arm(now()) } else { trace::freeze(now()) };
            if ok { SUMMARY_PAGE.store(0, Ordering::Relaxed); EVENT_PAGE.store(0, Ordering::Relaxed); COMPACT_PAGE.store(0, Ordering::Relaxed); }
            log::info!("USB_TRACE rxdiag v=2 ctrl={} ok={}", key as char, ok);
        }
        b'J' => summary_page(),
        b'K' => event_page(),
        b'V' => compact_page(),
        _ => {}
    }
}

#[inline(never)]
fn summary_page() {
    if !streaming::diagnostic_trace_idle() {
        log::info!("USB_TRACE rxdiag v=2 result=busy"); return;
    }
    let Some(s) = trace::summary() else {
        log::info!("USB_TRACE rxdiag v=2 result=busy"); return;
    };
    let page = SUMMARY_PAGE.load(Ordering::Relaxed) % SUMMARY_PAGES;
    match page {
        0 => log::info!("USB_TRACE rxdiag v=2 s=0 epoch={} pages={} records={} failures={} armed={} frozen={} bytes={}",
            s.epoch, SUMMARY_PAGES, s.len, s.failure_len, s.armed, s.frozen, trace::STORAGE_BYTES),
        1 => log::info!("USB_TRACE rxdiag v=2 s=1 epoch={} recorded={} overwritten={} lost_records={} lost_phase={}",
            s.epoch, s.recorded, s.overwritten, s.lost_records, s.lost_phase),
        2 => log::info!("USB_TRACE rxdiag v=2 s=2 epoch={} queue_overflows={} lost_failures={} failure_overflow={} counters_valid={} ambiguous_tails={}",
            s.epoch, s.queue_overflows, s.lost_failures, s.failure_overflow, s.counters_valid, s.ambiguous_tails),
        3 => log::info!("USB_TRACE rxdiag v=2 s=3 epoch={} first={} last={} post={} triggered={} trigger_lost={}",
            s.epoch, s.first_sequence.unwrap_or(0), s.last_sequence.unwrap_or(0), s.post_remaining, s.triggered, s.trigger_lost),
        4 => log::info!("USB_TRACE rxdiag v=2 s=4 epoch={} first_overflow_us={} time_valid={}",
            s.epoch,s.first_overflow_us.unwrap_or(0),s.first_overflow_us.is_some()),
        p if p < 5 + trace::PHASE_COUNT => log::info!("USB_TRACE rxdiag v=2 s={} epoch={} phase={} max_us={}",
            p, s.epoch, p-5, s.phase_max_us[p-5]),
        p if p < BASE_SUMMARY_PAGES => trigger_page(p, &s),
        p => {
            let Some(loss)=trace::loss_counts() else {return;};
            if loss.epoch!=s.epoch {return;}
            let kind=p-BASE_SUMMARY_PAGES;
            log::info!("USB_TRACE rxdiag v=2 s={} epoch={} kind={} lost={} loss_valid={}",
                p,s.epoch,kind,loss.counts[kind],loss.counters_valid);
        },
    }
    SUMMARY_PAGE.store((page + 1) % SUMMARY_PAGES, Ordering::Relaxed);
}

#[inline(never)]
fn trigger_page(page: usize, s: &trace::Summary) {
    let Some(t) = s.trigger else {
        log::info!("USB_TRACE rxdiag v=2 s={} epoch={} trigger_valid=false", page, s.epoch); return;
    };
    match page - (5 + trace::PHASE_COUNT) {
        0 => log::info!("USB_TRACE rxdiag v=2 s={} epoch={} trigger_valid=true seq={} us={} rx={}",
            page,s.epoch,t.sequence,t.time_us,t.received_us),
        1 => log::info!("USB_TRACE rxdiag v=2 s={} epoch={} in_id={} in_off={} in_v={} queued={} qv={}",
            page,s.epoch,t.context.incoming.frame,t.context.incoming.offset,flags(t.context.incoming),t.context.queued,t.context.queue_valid),
        2 => log::info!("USB_TRACE rxdiag v=2 s={} epoch={} consumer_id={} off={} valid={} active_id={} expected={} active_v={}",
            page,s.epoch,t.consumer_context.incoming.frame,t.consumer_context.incoming.offset,flags(t.consumer_context.incoming),
            t.consumer_context.active.frame,t.consumer_context.active.offset,flags(t.consumer_context.active)),
        _ => log::info!("USB_TRACE rxdiag v=2 s={} epoch={} phase={} since={} phase_valid={}",
            page,s.epoch,t.phase as u8,t.phase_since_us,t.phase_valid),
    }
}

#[inline(never)]
fn event_page() {
    if !streaming::diagnostic_trace_idle() {
        log::info!("USB_TRACE rxdiag v=2 result=busy"); return;
    }
    let Some(s) = trace::summary() else { log::info!("USB_TRACE rxdiag v=2 result=busy"); return; };
    if !s.frozen { log::info!("USB_TRACE rxdiag v=2 result=not_frozen"); return; }
    let total = s.len as usize * 5 + s.failure_len as usize * 4;
    if total == 0 { log::info!("USB_TRACE rxdiag v=2 epoch={} result=empty", s.epoch); return; }
    let cursor = EVENT_PAGE.load(Ordering::Relaxed) % total;
    let ok = if cursor < s.len as usize * 5 {
        let index = cursor / 5; let page = cursor % 5;
        if let Some(r) = trace::read(index) { record_page(index,page,&r); true } else { false }
    } else {
        let n = cursor - s.len as usize * 5; let index = n / 4; let page = n % 4;
        if let Some(f) = trace::read_failure(index) { failure_page(index,page,&f); true } else { false }
    };
    if ok { EVENT_PAGE.store((cursor+1)%total, Ordering::Relaxed); }
    else { log::info!("USB_TRACE rxdiag v=2 result=busy"); }
}

#[inline(never)]
fn record_page(index:usize,page:usize,r:&trace::Record) {
    match page {
        0 => log::info!("USB_TRACE rxdiag v=2 e={} p=0 epoch={} seq={} us={} kind={} phase={}",
            index,r.epoch,r.sequence,r.time_us,r.kind as u8,r.phase as u8),
        1 => log::info!("USB_TRACE rxdiag v=2 e={} p=1 epoch={} seq={} in_id={} in_off={} in_v={} queued={} qv={}",
            index,r.epoch,r.sequence,r.context.incoming.frame,r.context.incoming.offset,flags(r.context.incoming),r.context.queued,r.context.queue_valid),
        2 => log::info!("USB_TRACE rxdiag v=2 e={} p=2 epoch={} seq={} active_id={} expected={} active_v={} since={} pv={}",
            index,r.epoch,r.sequence,r.context.active.frame,r.context.active.offset,flags(r.context.active),r.phase_since_us,r.phase_valid),
        3 => log::info!("USB_TRACE rxdiag v=2 e={} p=3 epoch={} seq={} rx={} lock={} qspi={} detail={} clipped={}",
            index,r.epoch,r.sequence,r.received_us,r.lock_us,r.qspi_us,r.detail,r.duration_clipped),
        _ => log::info!("USB_TRACE rxdiag v=2 e={} p=4 epoch={} seq={} consumer={} valid={}",
            index,r.epoch,r.sequence,r.consumer_us,r.kind==trace::Kind::Complete),
    }
}

#[inline(never)]
fn failure_page(index:usize,page:usize,f:&trace::Failure) {
    if page == 0 {
        log::info!("USB_TRACE rxdiag v=2 f={} p=0 epoch={} seq={} us={} in_id={} in_off={} in_v={}",
            index,f.epoch,f.sequence,f.time_us,f.context.incoming.frame,f.context.incoming.offset,flags(f.context.incoming));
    } else if page == 1 {
        log::info!("USB_TRACE rxdiag v=2 f={} p=1 epoch={} seq={} active_id={} expected={} active_v={} queued={} qv={} detail={}",
            index,f.epoch,f.sequence,f.context.active.frame,f.context.active.offset,flags(f.context.active),f.context.queued,f.context.queue_valid,f.detail);
    } else if page == 2 {
        log::info!("USB_TRACE rxdiag v=2 f={} p=2 epoch={} seq={} consumer={} valid={} clipped={}",
            index,f.epoch,f.sequence,f.consumer_us.unwrap_or(0),f.consumer_us.is_some(),f.duration_clipped);
    } else {
        log::info!("USB_TRACE rxdiag v=2 f={} p=3 epoch={} seq={} rx={} tail_ambiguous={}",
            index,f.epoch,f.sequence,f.received_us,f.tail_ambiguous);
    }
}

/// Frozen-only one-record-per-command export; legacy J/K remain supported.
#[inline(never)]
fn compact_page() {
    if !streaming::diagnostic_trace_idle() {
        log::info!("USB_TRACE rxdiag v=2 result=busy"); return;
    }
    let Some(s) = trace::summary() else { return; };
    if !s.frozen { log::info!("USB_TRACE rxdiag v=2 result=not_frozen"); return; }
    let total = s.len as usize + s.failure_len as usize;
    if total == 0 { log::info!("USB_TRACE rxdiag v=2 epoch={} result=empty",s.epoch); return; }
    let cursor = COMPACT_PAGE.load(Ordering::Relaxed) % total;
    let line = if cursor < s.len as usize {
        trace::read(cursor).filter(|r|r.epoch==s.epoch)
            .map(|r|crate::trace_compact::record(cursor as u16,&r))
    } else {
        let index=cursor-s.len as usize;
        trace::read_failure(index).filter(|r|r.epoch==s.epoch)
            .map(|r|crate::trace_compact::failure(index as u16,&r))
    };
    if let Some(line)=line {
        log::info!(target:"diag","{}",line.as_str());
        COMPACT_PAGE.store((cursor+1)%total,Ordering::Relaxed);
    }
}
