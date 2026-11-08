from pathlib import Path
import hashlib, json, os, subprocess

p = Path(__file__).resolve().parent
root = Path('C:/moon/publish/firmware/experiments')
variants = {'control': root/'v48-dy71-selftest-control-20261107', 'candidate': root/'v51-dy71-free-probe-20261108'}
def function(text, name):
    start = text.index(name)
    start = text.rfind('\n', 0, start) + 1
    begin = text.index('{', start)
    depth = 1
    end = begin + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

stub = '''
use std::sync::atomic::{AtomicUsize, Ordering};
static MIN_FREE:AtomicUsize=AtomicUsize::new(usize::MAX);
mod esp_idf_svc {pub mod sys {
 use super::super::*;
 pub const MALLOC_CAP_INTERNAL:u32=0x800; pub const MALLOC_CAP_8BIT:u32=4;
 pub static FREE_CALLS:AtomicUsize=AtomicUsize::new(0);
 pub static LARGEST_CALLS:AtomicUsize=AtomicUsize::new(0);
 pub static FREE:AtomicUsize=AtomicUsize::new(120000);
 pub static LARGEST:AtomicUsize=AtomicUsize::new(32000);
 pub unsafe fn heap_caps_get_free_size(c:u32)->usize {assert_eq!(c,0x804);FREE_CALLS.fetch_add(1,Ordering::Relaxed);FREE.load(Ordering::Relaxed)}
 pub unsafe fn heap_caps_get_largest_free_block(c:u32)->usize {assert_eq!(c,0x804);LARGEST_CALLS.fetch_add(1,Ordering::Relaxed);LARGEST.load(Ordering::Relaxed)}
}}
'''
tests = '''
#[test]fn reserve_samples_and_minimum_unchanged(){unsafe{
 esp_idf_svc::sys::FREE_CALLS.store(0,Ordering::Relaxed);
 esp_idf_svc::sys::LARGEST_CALLS.store(0,Ordering::Relaxed);
 MIN_FREE.store(usize::MAX,Ordering::Relaxed);
 for free in [120000usize,117552,8192,8191,0,35000] {
  esp_idf_svc::sys::FREE.store(free,Ordering::Relaxed);
  assert_eq!(free_probe(),free);
 }
 assert_eq!(MIN_FREE.load(Ordering::Relaxed),0);
 assert_eq!(esp_idf_svc::sys::FREE_CALLS.load(Ordering::Relaxed),6);
 assert_eq!(esp_idf_svc::sys::LARGEST_CALLS.load(Ordering::Relaxed),EXPECTED_NORMAL_LARGEST*6);
 assert_eq!(largest_probe(),32000);
 assert_eq!(esp_idf_svc::sys::LARGEST_CALLS.load(Ordering::Relaxed),EXPECTED_NORMAL_LARGEST*6+1);
}}
#[test]fn successful_allocation_callback_cadence(){unsafe{
 esp_idf_svc::sys::FREE_CALLS.store(0,Ordering::Relaxed);
 esp_idf_svc::sys::LARGEST_CALLS.store(0,Ordering::Relaxed);
 for _ in 0..2260 {let _=free_probe();let _=free_probe();}
 assert_eq!(esp_idf_svc::sys::FREE_CALLS.load(Ordering::Relaxed),4520);
 assert_eq!(esp_idf_svc::sys::LARGEST_CALLS.load(Ordering::Relaxed),EXPECTED_NORMAL_LARGEST*4520);
}}
'''
records=[]
for label, base in variants.items():
    src=base/'handheld/src/cu66/network_usb.rs'
    text=src.read_text()
    names=['free_probe(', 'largest_probe(', 'heap(']
    if label=='candidate': names += ['internal_free(', 'internal_largest(']
    # Use declaration names so calls do not accidentally select another function.
    fragments=[function(text,'fn '+name) for name in names]
    fragments=[('unsafe extern "C" '+f if f.startswith('fn free_probe') or f.startswith('fn largest_probe') else f) for f in fragments]
    # function() preserves the declaration prefix on each complete source line.
    generated=stub+'\n'.join(fragments)+'\nconst EXPECTED_NORMAL_LARGEST:usize='+('1'if label=='control'else'0')+';\n'+tests
    source=p/(label+'-callbacks.rs');source.write_text(generated)
    exe=p/(label+'-callbacks.exe')
    commands=[[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(source),'-o',str(exe)], [str(exe),'--test-threads=1']]
    for phase,cmd in zip(['compile','test'],commands):
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=90,env=dict(os.environ,TEMP='C:/moon/tmp',TMP='C:/moon/tmp'))
        (p/(label+'-'+phase+'.log')).write_text(r.stdout+r.stderr)
        records.append({'variant':label,'phase':phase,'command':cmd,'returncode':r.returncode,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'extracted_harness_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
        (p/'execution.json').write_text(json.dumps(records,indent=2)+'\n')
        print(label,phase,r.returncode,flush=True)
        if r.returncode: raise SystemExit(r.stdout+r.stderr)
print('CALLBACK_BEHAVIOR_PASS reserve/minimum cadence preserved; normal largest queries 4520 -> 0 in source-extracted host model; target timing unmeasured')
