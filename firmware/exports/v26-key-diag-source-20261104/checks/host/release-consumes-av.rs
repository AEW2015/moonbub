#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/core_admission.rs"]mod core_admission;
#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/key_diag_core.rs"]mod key_diag_core;
use core_admission::*;use key_diag_core::*;
fn main(){let mut a=CoreAdmission::new(1);let v=a.reserve_video().unwrap();a.activate_video(&v).unwrap();let p=a.reserve_av().unwrap();a.begin_av_drain(&p).unwrap();a.release_av(p,AvDrain{session_cleared:true,feeder_idle:true,io_drained:true,power_restored:true}).unwrap();let _=p.id();}
