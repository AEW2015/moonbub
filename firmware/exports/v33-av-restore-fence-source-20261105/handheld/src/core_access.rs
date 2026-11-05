//! SDK lock boundary: reserve under CONTROL, perform callbacks without CONTROL,
//! finish after Device/CURRENT/session guards have left scope.
use crate::core_admission::{AvDrain, ProgramPermit};
use crate::core_coordinator::{Maintenance, MaintenancePermit, CONTROL};
pub fn reserve_program(receiver: bool, restore: bool) -> anyhow::Result<ProgramPermit> {
    let result = {
        let mut c = CONTROL.lock().unwrap();
        c.program(receiver, restore)
    };
    result.map_err(|e| anyhow::anyhow!("FPGA Busy: {e:?}"))
}
pub fn finish_program(p: ProgramPermit, ok: bool) -> anyhow::Result<()> {
    let result = {
        let mut c = CONTROL.lock().unwrap();
        c.program_finished(p, ok)
    };
    result.map_err(|e| anyhow::anyhow!("FPGA programming unconfirmed; restart required: {e:?}"))
}
pub fn program<T>(
    receiver: bool,
    restore: bool,
    f: impl FnOnce(&mut ProgramPermit) -> Result<T, String>,
) -> Result<T, String> {
    let mut p = reserve_program(receiver, restore).map_err(|e| e.to_string())?;
    let result = f(&mut p);
    let finish = finish_program(p, result.is_ok()).map_err(|e| e.to_string());
    match (result, finish) {
        (Ok(v), Ok(())) => Ok(v),
        (Err(e), _) => Err(e),
        (_, Err(e)) => Err(e),
    }
}
pub fn observe_peer() -> anyhow::Result<bool> {
    let (magic, build) = {
        let mut d = crate::device::Device::lock();
        (d.fpga.read_u32(0xe0000000)?, d.fpga.read_u32(0xe0000184)?)
    };
    let mut c = CONTROL.lock().unwrap();
    c.note_peer(magic, build);
    Ok(c.diagnostic_peer())
}
pub fn refuse_diagnostic_peer() -> anyhow::Result<()> {
    anyhow::ensure!(
        !observe_peer()?,
        "MBK1 compute-only image: video/local/AV refused"
    );
    Ok(())
}
pub fn av_admit() -> bool {
    CONTROL.lock().unwrap().av_admit().is_ok()
}
pub fn av_drained(confirmed: bool) {
    let _ = CONTROL.lock().unwrap().av_drained(AvDrain {
        session_cleared: confirmed,
        feeder_idle: confirmed,
        io_drained: confirmed,
        power_restored: confirmed,
    });
}
/// Inert token Drop in pure core becomes an explicit release here. This wrapper
/// must be dropped after all Device/CURRENT/session guards (lexical outer scope).
pub struct MaintenanceGuard {
    permit: Option<MaintenancePermit>,
    confirmed: bool,
}
impl MaintenanceGuard {
    pub fn acquire(m: Maintenance) -> anyhow::Result<Self> {
        let result = {
            let mut c = CONTROL.lock().unwrap();
            c.maintenance(m)
        };
        let p = result.map_err(|e| anyhow::anyhow!("FPGA Busy: {e:?}"))?;
        Ok(Self {
            permit: Some(p),
            confirmed: true,
        })
    }
}
impl MaintenanceGuard {
    pub fn side_effects_begin(&mut self) {
        self.confirmed = false;
    }
    pub fn quiescent(&mut self) {
        self.confirmed = true;
    }
}
impl Drop for MaintenanceGuard {
    fn drop(&mut self) {
        if let Some(p) = self.permit.take() {
            let _ = CONTROL
                .lock()
                .unwrap()
                .maintenance_finished(p, self.confirmed);
        }
    }
}
