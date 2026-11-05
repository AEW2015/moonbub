//! Fixed-capacity payloads; SDK framing and actual task stack remain physical gates.
use crate::key_diag_core::DiagnosticCore;
pub fn resource(
    stack_low_bytes: u32,
    declared_bytes: u32,
    free_internal: usize,
    largest_internal: usize,
) -> Result<crate::diag_pages::Line, fmt::Error> {
    let mut line = crate::diag_pages::Line::new();
    write!(line,"USB_D24 v=2 p=key_resource worker=KeyDiag stack_low_bytes={} declared_bytes={} free_internal={} largest_internal={} sampled=true",stack_low_bytes,declared_bytes,free_internal,largest_internal)?;
    Ok(line)
}
use core::fmt::{self, Write};
pub fn page(c: &DiagnosticCore, index: u8) -> Result<crate::diag_pages::Line, fmt::Error> {
    let mut line = crate::diag_pages::Line::new();
    if index == 0 {
        write!(
            line,
            "USB_D24 v=2 p=key state={:?} reason={:?} actions={}",
            c.stage(),
            c.reason(),
            c.actions_in_phase()
        )?;
    } else if let Some(r) = c.record() {
        return record_page(r, index);
    } else {
        write!(line, "USB_D24 v=2 p=key_record state=unavailable")?;
    }
    Ok(line)
}
pub fn record_page(
    r: &crate::key_diag_core::Record,
    index: u8,
) -> Result<crate::diag_pages::Line, fmt::Error> {
    let mut line = crate::diag_pages::Line::new();
    match index{
  1=>write!(line,"USB_D24 v=2 p=key_record owner={:016x} seq={} status={:08x} kind={:?}",r.owner,r.sequence,r.status,r.kind)?,
  2=>write!(line,"USB_D24 v=2 p=key_counts owner={:016x} seq={} cycles={} samples={} bytes={} epoch={} frame={} fault={:08x}",r.owner,r.sequence,r.payload.cycles,r.payload.samples,r.payload.bytes,r.payload.epoch,r.payload.frame,r.payload.fault)?,
  _=>write!(line,"USB_D24 v=2 p=key_tag owner={:016x} seq={} words={:08x},{:08x},{:08x},{:08x}",r.owner,r.sequence,r.payload.tag[0],r.payload.tag[1],r.payload.tag[2],r.payload.tag[3])?
 }
    Ok(line)
}
