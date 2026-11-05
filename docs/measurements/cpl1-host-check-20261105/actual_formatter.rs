#[path="C:\\Users\\lavat\\codex\\moonbub\\firmware\\exports\\v32-cpl1-observe-source-20261105\\handheld\\src\\streaming\\telemetry.rs"] pub mod telemetry;
mod streaming {pub use crate::telemetry;}
#[path="C:\\Users\\lavat\\codex\\moonbub\\firmware\\exports\\v32-cpl1-observe-source-20261105\\handheld\\src\\diag_pages.rs"] mod diag_pages;
#[path="C:\\Users\\lavat\\codex\\moonbub\\firmware\\exports\\v32-cpl1-observe-source-20261105\\handheld\\src\\cpl1.rs"] mod cpl1;
fn main(){let mut words=[4660u32,7u32,65536u32,1959u32,4294967295u32,2u32,2596069104u32,305419896u32,1u32,0u32,1u32,17412u32,518400u32,21120u32,259200u32,259200u32,334349550u32,3165992509u32,643020u32,3075150561u32,1719690817u32,351625385u32,3084869734u32,270969528u32,196608u32,3u32,0u32,10u32,1u32,1u32,0u32,0u32,9u32,1280779749u32,345600u32,3u32,0u32,240u32,0u32,0u32];
if std::env::args().any(|x|x=="bad-crc"){words[33]=0x12345678;}
let s=cpl1::Snapshot{words};for i in 0..10{println!("{}",cpl1::page(&s,i).unwrap().as_str());}}