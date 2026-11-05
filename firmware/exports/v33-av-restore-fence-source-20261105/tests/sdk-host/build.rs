use std::{env,fs,path::PathBuf};
fn main(){
 let root=PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap());
 let source=root.join("../../handheld/src/streaming/audio.rs");
 let s=fs::read_to_string(&source).unwrap();
 let radio=&s[s.find("struct Radio {").unwrap()..s.find("fn endpoint(").unwrap()];
 let guard=&s[s.find("pub struct Guard {").unwrap()..s.find("impl Guard {").unwrap()];
 let drop=&s[s.find("impl Drop for Guard {").unwrap()..s.find("fn send_input(").unwrap()];
 assert_eq!(radio.matches("RECOVERY_FAILED.store(true, Ordering::Release)").count(),1);
 assert!(radio.contains("PS_RESTORE_ERRORS.fetch_add(1, Ordering::Relaxed);"));
 assert!(drop.contains("crate::core_access::av_drained(joined&&!RECOVERY_FAILED.load(Ordering::Acquire))"));
 // The two in-worker STOP/lease paths still share this exact helper. No
 // fabricated release/worker algorithm is substituted in the generated test.
 assert_eq!(s.matches("if !restore_ps(&mut power_save)").count(),3);
 let mut out=String::from("use std::sync::{Arc,atomic::{AtomicBool,AtomicU32,Ordering}};\nuse crate::streaming::av_power_save;\nstatic RECOVERY_FAILED:AtomicBool=AtomicBool::new(false);\n");
 for name in ["PS_INITIAL","PS_ACTUAL","PS_ENTRY_ERRORS","PS_RESTORE_ERRORS"]{out+=&format!("static {}:AtomicU32=AtomicU32::new(0);\n",name);}
 out+=radio;out+=guard;out+=drop;
 out+=&format!("include!({:?});\n",root.join("src/av_restore_cases.rs"));
 fs::write(PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("av_restore_actual.rs"),out).unwrap();
 println!("cargo:rerun-if-changed={}",source.display());
 println!("cargo:rerun-if-changed=src/av_restore_cases.rs");
}
