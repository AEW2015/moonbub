#include "Vcu77_display_sim.h"
#include "verilated.h"
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <sstream>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"packetopen");return {std::istreambuf_iterator<char>(f),{}};}
static unsigned base(unsigned b){return b==0?0x80000:0x880000;}
static unsigned hb(unsigned b){return b==0?0x100000:0x900000;}
struct Events {bool auxreq=false,auxrsp=false,descreq=false,preq=false,pdone=false,cons=false,finish=false,dp=false,wr=false,wd=false,rr=false,rd=false;};
struct Sim{
 std::unique_ptr<VerilatedContext> c=[](){auto v=std::make_unique<VerilatedContext>();v->threads(1);return v;}();Vcu77_display_sim d{c.get()};
 uint64_t cycles=0,next_pixel=17029,measurement=0;unsigned epoch=0,bank=0,pre=0,consume=0,bgmode=0;
 bool measurement_on=false,prefetch_pending=false,consume_pending=false,panel_complete=false;unsigned pending_strip=0;
 std::shared_ptr<const cu66::Frame> gold;uint64_t pixels=0,good=0,bad=0,complete=0;unsigned linepix=0,lines=0;bool raster_good=true;
 uint64_t releasedW=0,releasedR=0,doneW=0,doneR=0;unsigned bgstate=0,bgplane=0,bgindex=0;bool bgwrite=false,turn=false;
 std::vector<std::pair<unsigned,unsigned>> refs;
 explicit Sim(unsigned mode):bgmode(mode){
  for(unsigned p=0;p<3;p++){unsigned n=p?1350:5400;for(unsigned i=0;i<n;i++){bool hidden=p==0?cu66::SAFE0[i]:p==1?cu66::SAFE1[i]:cu66::SAFE2[i];if(!hidden)refs.emplace_back(p,i);}}
  need(refs.size()==7806,"referencecount");
  d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.display_rst=1;d.abort_i=0;d.desc_valid=0;d.finish_valid=0;d.prefetch_valid=0;d.prefetch_done_ready=1;d.consume_valid=0;d.display_desc_valid=0;
  d.aux_req_valid=0;d.aux_rsp_ready=1;d.read_valid=0;d.read_rsp_ready=1;d.write_valid=0;d.write_done_ready=1;
  d.eval();for(unsigned i=0;i<12;i++)tick();d.rst=0;for(unsigned i=0;i<100;i++)tick();
 }
 void check_pixel(){
  if(!measurement_on||!d.front_valid||!d.data_enable)return;
  unsigned x=d.physical_x,y=d.physical_y;need(x<480&&y<800,"nativebounds");
  if(x==0&&y==0){linepix=0;lines=0;raster_good=true;}
  uint16_t want=(40<=y&&y<760)?gold->display[x*720+y-40]:0;
  uint16_t got=uint16_t((d.red>>3)<<11|(d.green>>2)<<5|(d.blue>>3));
  need(d.front_generation==epoch&&d.front_frame_id==gold->id,"nativeepochidentity");
  need(x==linepix&&y==lines,"nativepixelorder");linepix++;pixels++;if(want==got)good++;else{bad++;raster_good=false;}
  if(x==479){linepix=0;lines++;
   if(y>=40&&y<760&&((y-40)%8)==7){need(!consume_pending,"consumepending");consume_pending=true;pending_strip=(y-40)/8;}
   if(y==799){panel_complete=true;if(raster_good)complete++;}
  }
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t n=std::min(target,next_pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());need(n>=c->time(),"eventtime");c->timeInc(n-c->time());bool rise=false;if(n==next_pixel){d.pixel_clk=!d.pixel_clk;rise=d.pixel_clk;next_pixel+=17029;}d.eval();if(rise)check_pixel();}}
 void bg_drive(){
  d.write_valid=0;d.read_valid=0;
  if(!bgmode)return;
  if(measurement_on){uint64_t elapsed=cycles-measurement;releasedW=elapsed*243000/100000000;releasedR=elapsed*234180/100000000;}
  if(bgstate==0&&(doneW<releasedW||doneR<releasedR)){
   bgwrite=doneW<releasedW&&(doneR>=releasedR||!turn);
   if(bgwrite){unsigned t=unsigned(doneW%8100);bgplane=t<5400?0:t<6750?1:2;bgindex=bgplane==0?t:bgplane==1?t-5400:t-6750;}
   else {auto v=refs[doneR%refs.size()];bgplane=v.first;bgindex=v.second;}
   bgstate=1;
  }
  if(bgstate==1){
   if(bgwrite){d.write_valid=1;d.write_generation=100+epoch;d.write_bank=1;d.write_plane=bgplane;d.write_index=bgindex;for(unsigned i=0;i<16;i++)d.write_pixels[i]=0x12345678u^(unsigned(doneW)*37u+i*337u);}
   else {d.read_valid=1;d.read_generation=200+epoch;d.read_bank=bank;d.read_plane=bgplane;d.read_index=bgindex;}
  }
 }
 void drive(){
  bg_drive();
  d.prefetch_valid=measurement_on&&!prefetch_pending&&pre<90&&pre<unsigned(d.consumed_count)+3;d.prefetch_index=pre;
  d.consume_valid=consume_pending;d.consume_index=pending_strip;
 }
 Events tick(){need(cycles<15000000,"displaywatchdog");drive();d.eval();uint64_t t=c->time();advance(t+2750);d.read_clk=1;d.eval();advance(t+5000);d.eval();Events e;
  e.auxreq=d.aux_req_valid&&d.aux_req_ready;e.auxrsp=d.aux_rsp_valid&&d.aux_rsp_ready;e.descreq=d.desc_valid&&d.desc_ready;e.preq=d.prefetch_valid&&d.prefetch_ready;e.pdone=d.prefetch_done_valid&&d.prefetch_done_ready;e.cons=d.consume_valid&&d.consume_ready;e.finish=d.finish_valid&&d.finish_ready;e.dp=d.display_desc_valid&&d.display_desc_ready;e.wr=d.write_valid&&d.write_ready;e.wd=d.write_done_valid&&d.write_done_ready;e.rr=d.read_valid&&d.read_ready;e.rd=d.read_rsp_valid&&d.read_rsp_ready;
  if(e.pdone)need(d.prefetch_done_index==pre,"prefetchidentity");
  if(e.auxrsp)need(!d.aux_rsp_error,"setupwriteerror");
  if(e.wd)need(!d.write_done_error,"backgroundwriteerror");
  if(e.rd){need(!d.read_rsp_error,"backgroundreaderror");unsigned w=bgplane?360:720;
   for(unsigned i=0;i<32;i++){unsigned x=(bgindex%(w/8))*8+(i%4)*2,y=(bgindex/(w/8))*8+i/4;uint16_t expected=uint16_t(gold->planes[bgplane][y*w+x])|(uint16_t(gold->planes[bgplane][y*w+x+1])<<8);uint16_t actual=uint16_t(d.read_rsp_pixels[i/2]>>(16*(i%2)));need(actual==expected,"backgroundreferenceactualdata");}}
  d.clk=1;d.eval();advance(t+7750);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();cycles++;
  if(e.preq)prefetch_pending=true;if(e.pdone){need(prefetch_pending,"prefetchwithoutpending");prefetch_pending=false;pre++;}
  if(e.cons){need(pending_strip==consume,"consumeidentity");consume_pending=false;consume++;}
  if(e.wr||e.rr)bgstate=2;
  if(e.wd){need(bgstate==2&&bgwrite,"backgroundwriteownership");doneW++;bgstate=0;turn=true;}
  if(e.rd){need(bgstate==2&&!bgwrite,"backgroundreadownership");doneR++;bgstate=0;turn=false;}
  return e;
 }
 void seed(unsigned addr,const std::array<uint16_t,8>&v){
  d.aux_req_addr=addr;for(unsigned i=0;i<4;i++)d.aux_req_burst_data[i]=uint32_t(v[2*i])|(uint32_t(v[2*i+1])<<16);d.aux_req_valid=1;for(unsigned n=0;!tick().auxreq;n++)need(n<10000,"setupreqwait");d.aux_req_valid=0;for(unsigned n=0;!tick().auxrsp;n++)need(n<10000,"setuprspwait");
 }
 void setup(){
  std::array<uint16_t,8> words{};
  for(unsigned p=0;p<3;p++){unsigned w=p?360:720,h=p?240:480,off=p==0?0:p==1?172800:216000;
   for(unsigned ti=0;ti<(w/8)*(h/8);ti++)for(unsigned k=0;k<32;k+=8){
    for(unsigned i=0;i<8;i++){unsigned j=k+i,x=(ti%(w/8))*8+(j%4)*2,y=(ti/(w/8))*8+j/4;words[i]=uint16_t(gold->planes[p][y*w+x])|(uint16_t(gold->planes[p][y*w+x+1])<<8);}seed(base(bank)+off+ti*32+k,words);
   }
  }
  std::vector<uint16_t>hud;for(auto&p:gold->hud)hud.insert(hud.end(),p.words.begin(),p.words.end());need(hud.size()==21120,"nativeHUDsize");
  for(unsigned at=0;at<hud.size();at+=8){for(unsigned i=0;i<8;i++)words[i]=hud[at+i];seed(hb(bank)+at,words);}
 }
 void run(std::shared_ptr<const cu66::Frame>g,unsigned which){
  gold=g;bank=which?2:0;epoch=which+1;d.pixel_reset_n=0;d.display_rst=1;measurement_on=false;for(unsigned i=0;i<10;i++)tick();
  unsigned wr0=d.model_writes,wc0=d.model_write_commands,wb0=d.model_write_beats;setup();need(d.model_writes-wr0==280320&&d.model_write_commands-wc0==35040&&d.model_write_beats-wb0==280320,"physicalsetupcounts");
  pre=consume=0;prefetch_pending=consume_pending=panel_complete=false;pixels=good=bad=complete=0;linepix=lines=0;releasedW=releasedR=doneW=doneR=0;bgstate=0;turn=false;
  d.display_rst=0;d.desc_generation=epoch;d.desc_frame_id=gold->id;d.desc_bank=bank;d.desc_valid=1;while(!tick().descreq){}d.desc_valid=0;
  unsigned mr0=d.model_reads,mw0=d.model_writes,mwc0=d.model_write_commands,mwb0=d.model_write_beats;measurement=cycles;measurement_on=true;d.pixel_reset_n=1;d.display_desc_generation=epoch;d.display_desc_frame_id=gold->id;d.display_desc_valid=1;while(!tick().dp){}d.display_desc_valid=0;
  uint64_t first=cycles;while(!panel_complete){tick();need(cycles-first<4000000,"nativepaneltimeout");need(!d.cache_error&&!d.adapter_error,"cache/adaptererror code="+std::to_string(d.cache_error_code)+" pre="+std::to_string(pre)+" consume="+std::to_string(consume));}
  need(pixels==384000,"nativefullrasterpixelcount");need(pre==90&&consume==90&&!consume_pending,"allstripscompleted");need(d.read_commands==35040&&d.read_words==280320&&d.pixel_queries==345600,"actualcacheworkcounts");
  d.finish_valid=1;while(!tick().finish){}d.finish_valid=0;measurement_on=false;uint64_t foreground_end=cycles;d.pixel_reset_n=0;d.display_rst=1;
  // Stop new paced releases, then drain only jobs actually released. If requests
  // remain, preserve legal acknowledgments and reference checks until completion.
  for(unsigned n=0;bgstate||doneW<releasedW||doneR<releasedR;n++){need(n<100000,"backgroundreleaseddrain");tick();}
  need(bgstate==0&&doneW==releasedW&&doneR==releasedR,"backgroundidle");
  need(d.model_reads-mr0==35040+4*doneR&&d.model_writes-mw0==32*doneW&&d.model_write_commands-mwc0==4*doneW&&d.model_write_beats-mwb0==32*doneW,"measuredactualmodelcounts");
  std::cout<<"DISPLAY_CASE_PASS source="<<gold->id<<" epoch="<<epoch<<" bank="<<bank<<" background="<<bgmode<<" pixels="<<pixels<<" good="<<good<<" mismatches="<<bad<<" exact_rasters="<<complete<<" underruns="<<d.underruns<<" memory_errors="<<d.memory_errors<<" cache_reads="<<d.read_commands<<" cache_words="<<d.read_words<<" queries="<<d.pixel_queries<<" released_w="<<releasedW<<" released_r="<<releasedR<<" complete_w="<<doneW<<" complete_r="<<doneR<<" measure_cycles="<<foreground_end-measurement<<" drain_cycles="<<cycles-foreground_end<<" actual_reads="<<d.model_reads-mr0<<" actual_writes="<<d.model_writes-mw0<<std::endl;
  need(bad==0&&complete==1&&d.underruns==0&&d.memory_errors==0,"nativepixel/deadlinefailure");
 }
};
int main(int argc,char**argv){try{need(argc==3,"index mode");std::filesystem::path index=argv[1];Sim s(unsigned(std::stoul(argv[2])));cu66::Decoder dec;std::ifstream f(index);std::string l;unsigned n=0;while(n<2&&std::getline(f,l)){std::stringstream row(l);std::string chain,ordinal,path;std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');need(chain=="0","chronologicalcohort");auto g=dec.receive(load(index.parent_path()/path));s.run(g,n);n++;}need(n==2,"twoepochs");std::cout<<"DIRECT_DISPLAY_PASS frames=2 physical30fps_proven=0 validated_under10ms_proven=0"<<std::endl;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
