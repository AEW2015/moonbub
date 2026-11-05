#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/core_admission.rs"]mod core_admission;
#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/key_diag_core.rs"]mod key_diag_core;
use core_admission::*;use key_diag_core::*;
fn main(){let mut a=CoreAdmission::new(1);let p=a.reserve_diagnostic().unwrap();let mut c=DiagnosticCore::new(p,0,0,Budgets::default());let op=c.next_operation(0).unwrap();c.complete(op,Outcome::Read(0),0,0);let(_,x,_)=c.into_exit().unwrap();let moved=x;let reused=x;drop((moved,reused));}
