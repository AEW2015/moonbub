#![allow(dead_code)]
#[path="cu66/framing.rs"]mod framing;
#[path="cu66/hud.rs"]mod hud;
#[path="cu66/local.rs"]mod local;
#[path="cu66/stb1.rs"]mod stb1;
#[path="cu66/network_driver.rs"]mod nd;
use std::{cell::RefCell,rc::Rc,process::{Command,Child,ChildStdin,ChildStdout,Stdio},io::{Read,Write},fs::File};
const ROOT:&str="C:/moon/dev/experiments/stb1-v55-parserstage-video12-real-rust-system-20261108";
struct Link{p:Child,input:ChildStdin,output:ChildStdout,seq:u32,now:u64,calls:u64}
impl Link{
 fn new()->Self{let mut p=Command::new("wsl.exe").args(["-d","MRS-HDL-Research","--","/mnt/c/moon/dev/experiments/stb1-v55-parserstage-video12-real-rust-system-20261108/build/Vdy71_platform_sim","8"]).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::from(File::create(format!("{ROOT}/rtl-stderr.log")).unwrap())).spawn().unwrap();let input=p.stdin.take().unwrap();let output=p.stdout.take().unwrap();Self{p,input,output,seq:0,now:0,calls:0}}
 fn rpc(&mut self,op:u32,a:u32,v:u32)->u32{self.seq+=1;self.calls+=1;for n in [0x43535231,self.seq,op,a,v]{self.input.write_all(&n.to_le_bytes()).unwrap()}self.input.flush().unwrap();let mut b=[0;24];self.output.read_exact(&mut b).expect("RPC response");let w:Vec<u32>=b.chunks_exact(4).map(|b|u32::from_le_bytes(b.try_into().unwrap())).collect();assert_eq!(&w[..3],&[0x43535231,self.seq,0]);self.now=w[4]as u64|((w[5]as u64)<<32);w[3]}
 fn advance(&mut self,us:u32){let mut n=us*100;while n>0{let a=n.min(1000000);self.rpc(3,a,0);n-=a;}}
}
impl Drop for Link{fn drop(&mut self){if self.p.try_wait().ok().flatten().is_none(){let _=self.p.kill();let _=self.p.wait();}}}
struct Bus(Rc<RefCell<Link>>);
impl local::Bus for Bus{
 fn read(&mut self,o:u32)->Result<u32,local::Error>{Ok(self.0.borrow_mut().rpc(1,o,0))}
 fn write(&mut self,o:u32,v:u32)->Result<(),local::Error>{self.0.borrow_mut().rpc(2,o,v);Ok(())}
 fn now(&self)->u64{self.0.borrow().now}
 fn yield_now(&mut self){self.0.borrow_mut().advance(100)}
 fn hbu_status_words(&mut self)->Result<[u32;4],local::Error>{let mut w=[0u32;5];for(i,v)in w.iter_mut().enumerate(){*v=self.read(0x608+i as u32*4)?;}Ok([w[0],w[2],w[3],w[4]])}
 fn staging_read_words(&mut self,o:u32,out:&mut[u32])->Result<usize,local::Error>{for(i,v)in out.iter_mut().enumerate(){*v=self.read(o+i as u32*4)?;}Ok(out.len())}
 fn staging_descriptor(&mut self,w:&[u32;5])->Result<(),local::Error>{for(i,v)in w.iter().enumerate(){self.write(0x720+i as u32*4,*v)?;}Ok(())}
 fn staging_payload_be(&mut self,o:u32,b:&[u8])->Result<usize,local::Error>{if o!=0xc00||b.is_empty()||b.len()>1024||b.len()%4!=0{return Err(local::Error::Bounds)}for(i,w)in b.chunks_exact(4).enumerate(){self.write(o+i as u32*4,u32::from_be_bytes(w.try_into().unwrap()))?;}Ok(b.len())}
}
struct Source{index:usize,link:Rc<RefCell<Link>>,stored:usize}
impl Source{fn packet(&self)->&'static[u8]{match self.index{0=>include_bytes!("packets/frame000.cu66"),1=>include_bytes!("packets/frame001.cu66"),2=>include_bytes!("packets/frame002.cu66"),3=>include_bytes!("packets/frame003.cu66"),4=>include_bytes!("packets/frame004.cu66"),5=>include_bytes!("packets/frame005.cu66"),6=>include_bytes!("packets/frame006.cu66"),7=>include_bytes!("packets/frame007.cu66"),8=>include_bytes!("packets/frame008.cu66"),9=>include_bytes!("packets/frame009.cu66"),10=>include_bytes!("packets/frame010.cu66"),11=>include_bytes!("packets/frame011.cu66"),_=>panic!("source exhausted")}}}
impl nd::Source for Source{
 fn header(&mut self)->Result<nd::Header,nd::Error>{let p=self.packet();let mut prefix=[0;76];prefix.copy_from_slice(&p[..76]);self.stored=0;Ok(nd::Header{prefix,length:p.len(),crc:framing::crc32(p)})}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,nd::Error>{let p=self.packet();let n=(p.len()-offset).min(1024);out[..n].copy_from_slice(&p[offset..offset+n]);Ok(n)}
 fn stored(&mut self,n:usize)->Result<(),nd::Error>{assert!(n>self.stored&&n<=self.packet().len());self.stored=n;Ok(())}
 fn presented(&mut self)->Result<(),nd::Error>{assert_eq!(self.stored,self.packet().len());let bank=self.link.borrow_mut().rpc(6,self.index as u32,0);println!("ACTUAL_FRAME_PRESENTED frame={} bank={}",self.index,bank);self.index+=1;Ok(())}
 fn active(&mut self,o:u32,f:u32,g:u64,p:u8,t:u64){println!("PHASE ordinal={o} frame={f} gen={g} phase={p} at={t}");if p==nd::phase::NATIVE{self.link.borrow_mut().advance(200000);println!("MODELED_PREPARE_DELAY_US=200000");}}
}
fn main(){let link=Rc::new(RefCell::new(Link::new()));let mut bus=Bus(link.clone());let mut source=Source{index:0,link:link.clone(),stored:0};let mut h=hud::Hud::new(98304).unwrap();let(report,_proof)=nd::run_cached_sequence(&mut bus,&mut h,&mut source,12).unwrap_or_else(|e|panic!("Actual Rust driver error {e:?}, native {:?}",h.diagnostics()));assert_eq!((report.accepted,report.presented,report.rejected,report.underruns),(12,12,0,0));assert_eq!((report.words_written,report.words_verified),(253440,253440));assert_eq!(report.hud_cpu_us,[0;3]);println!("ACTUAL_RUST_REPORT {report:?}");for i in 0..4{println!("MODELSTAT index={i} value={}",link.borrow_mut().rpc(4,i,0));}println!("STB1_VIDEO12_SYSTEM_PASS");link.borrow_mut().rpc(0,0,0);assert!(link.borrow_mut().p.wait().unwrap().success());}
