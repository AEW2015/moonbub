#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/core_admission.rs"]mod core_admission;
#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/key_diag_core.rs"]mod key_diag_core;
use core_admission::*;use key_diag_core::*;
fn main(){let mut a=CoreAdmission::new(1);let x=a.reserve_av().unwrap();let copied=x.clone();drop(copied);}
