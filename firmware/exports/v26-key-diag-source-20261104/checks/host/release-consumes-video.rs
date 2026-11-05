#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/core_admission.rs"]mod core_admission;
#[path="C:/Users/lavat/codex/moonbub/firmware/exports/v26-key-diag-source-20261104/handheld/src/key_diag_core.rs"]mod key_diag_core;
use core_admission::*;use key_diag_core::*;
fn main(){let mut a=CoreAdmission::new(1);let p=a.reserve_video().unwrap();a.begin_video_drain(&p).unwrap();a.release_video(p,VideoDrain{worker_joined:true,receivers_closed:true,local_cleanup_complete:true}).unwrap();let _=p.id();}
