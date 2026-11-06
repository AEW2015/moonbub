#include "Vcu77_direct_cache.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static constexpr unsigned RX[4]={22,22,168,168},RY[4]={54,82,360,390},RW[4]={160,160,320,240};
static uint8_t sample(unsigned p,unsigned x,unsigned y,unsigned salt){return uint8_t((p+1)*37+x*11+y*19+(x^y)*3+salt*23);}
static uint16_t hud(unsigned p,unsigned x,unsigned y,unsigned salt){return uint16_t((p+1)*4099+x*97+y*13+salt*31);}
struct Q {unsigned u,v;bool error;};
struct Sim {
 std::unique_ptr<VerilatedContext> c=[](){auto p=std::make_unique<VerilatedContext>();p->threads(1);return p;}();Vcu77_direct_cache d{c.get()};
 uint64_t cycles=0,seed=0;unsigned bank=0,salt=0;bool pending=false,force_stall=false;unsigned address=0,beat=0,delay=0;
 int bad_last=-1,bad_error=-1;std::deque<Q> q;unsigned queries=0,responses=0,holds=0,canceled=0;
 unsigned commands=0,words=0,prefetch_current=0;std::array<std::vector<unsigned>,90> requests;
 bool req_held=false;unsigned held_addr=0;
 Sim(unsigned s):seed(s){d.clk=0;d.rst=1;d.abort_i=0;d.desc_valid=0;d.finish_valid=0;d.prefetch_valid=0;d.prefetch_done_ready=1;d.consume_valid=0;d.pixel_req_valid=0;d.pixel_rsp_ready=1;d.mem_req_ready=0;d.mem_rsp_valid=0;d.eval();for(int i=0;i<5;i++)tick();d.rst=0;tick();}
 uint16_t mem(unsigned a){unsigned base=0x80000+bank*0x400000;
  for(unsigned p=0;p<3;p++){unsigned off=p==0?0:p==1?172800:216000,n=p==0?172800:43200,w=p==0?720:360;if(a>=base+off&&a<base+off+n){unsigned rel=a-base-off,tile=rel/32,k=rel%32,ty=tile/(w/8),tx=tile%(w/8),x=tx*8+(k%4)*2,y=ty*8+k/4;return uint16_t(sample(p,x,y,salt)|(unsigned(sample(p,x+1,y,salt))<<8));}}
  unsigned hb=0x100000+bank*0x400000;need(a>=hb,"unmapped memory request before HUD");unsigned rel=a-hb;
  for(unsigned p=0;p<4;p++){unsigned n=RW[p]*24;if(rel<n)return hud(p,rel%RW[p],rel/RW[p],salt);rel-=n;}throw std::runtime_error("unmapped memory request");
 }
 void check(){need(!q.empty(),"unexpected pixel response");auto e=q.front();need(d.pixel_rsp_u==e.u&&d.pixel_rsp_v==e.v&&bool(d.pixel_rsp_error)==e.error,"pixel identity/error");
  if(e.error){need(d.pixel_y==0&&d.cb00==0&&d.cb10==0&&d.cb01==0&&d.cb11==0&&d.cr00==0&&d.cr10==0&&d.cr01==0&&d.cr11==0&&d.pixel_hud==0&&!d.pixel_hud_hit,"invalid pixel leaked data");return;}
  unsigned x=e.u/2,y=e.v/2,x1=std::min(x+1,359u),y1=std::min(y+1,239u);need(d.pixel_y==sample(0,e.u,e.v,salt),"Y sample");
  std::array<unsigned,8> a={d.cb00,d.cb10,d.cb01,d.cb11,d.cr00,d.cr10,d.cr01,d.cr11};
  for(unsigned p=1;p<=2;p++){std::array<unsigned,4>w={sample(p,x,y,salt),sample(p,x1,y,salt),sample(p,x,y1,salt),sample(p,x1,y1,salt)};for(unsigned i=0;i<4;i++)need(a[(p-1)*4+i]==w[i],"chroma neighborhood u="+std::to_string(e.u)+" v="+std::to_string(e.v)+" p="+std::to_string(p)+" tap="+std::to_string(i));}
  bool hit=false;for(unsigned p=0;p<4;p++)if(e.u>=RX[p]&&e.u<RX[p]+RW[p]&&e.v>=RY[p]&&e.v<RY[p]+24){hit=true;need(d.pixel_hud==hud(p,e.u-RX[p],e.v-RY[p],salt),"HUD sample");}need(bool(d.pixel_hud_hit)==hit,"HUD hitbox");
 }
 struct E {bool desc,prefetch,consume,req,rsp,pixel,output;};
 E tick(){need(cycles<12000000,"test watchdog");
  d.mem_req_ready=!pending&&!force_stall&&(seed==0||(cycles%7)!=3);d.mem_rsp_valid=pending&&delay==0;
  d.mem_rsp_data=pending?mem(address+beat):0;d.mem_rsp_last=pending&&(int(beat)==bad_last?beat!=7:beat==7);d.mem_rsp_error=pending&&int(beat)==bad_error;d.eval();
  if(d.pixel_rsp_valid)check();
  if(req_held){need(d.mem_req_valid&&d.mem_req_addr==held_addr,"stalled memory request changed");}
  req_held=d.mem_req_valid&&!d.mem_req_ready&&!d.abort_i;held_addr=d.mem_req_addr;
  E e{bool(d.desc_valid&&d.desc_ready),bool(d.prefetch_valid&&d.prefetch_ready),bool(d.consume_valid&&d.consume_ready),bool(d.mem_req_valid&&d.mem_req_ready),bool(d.mem_rsp_valid&&d.mem_rsp_ready),bool(d.pixel_req_valid&&d.pixel_req_ready),bool(d.pixel_rsp_valid&&d.pixel_rsp_ready)};
  unsigned a=d.mem_req_addr;Q accepted{d.pixel_u,d.pixel_v,false};if(e.pixel)accepted.error=d.pixel_u>=720||d.pixel_v>=480||d.pixel_u/8<d.consumed_count||d.pixel_u/8>=d.prefetched_count;
  d.clk=1;d.eval();c->timeInc(5);d.clk=0;d.eval();c->timeInc(5);cycles++;
  if(e.output){q.pop_front();responses++;}else if(!q.empty()&&d.pixel_rsp_valid&&!d.pixel_rsp_ready)holds++;
  if(e.pixel){q.push_back(accepted);queries++;}
  if(e.rsp){words++;if(beat==7){pending=false;beat=0;}else{beat++;delay=seed?unsigned((cycles+seed)%3):0;}}
  else if(pending&&delay)delay--;
  if(e.req){need(!pending,"multiple memory operations");pending=true;address=a;beat=0;delay=seed?unsigned((cycles+seed)%5):0;commands++;need(prefetch_current<90,"prefetch capture bound");requests[prefetch_current].push_back(a);}
  return e;
 }
 void descriptor(uint64_t gen,unsigned fid,unsigned b,unsigned s){d.desc_generation=gen;d.desc_frame_id=fid;d.desc_bank=b;bank=b<3?b:0;salt=s;d.desc_valid=1;for(unsigned n=0;;n++){need(n<100,"descriptor timeout");if(tick().desc)break;}d.desc_valid=0;}
 void prefetch(unsigned index){d.prefetch_index=index;d.prefetch_valid=1;for(unsigned n=0;;n++){need(n<30000,"prefetch admission timeout");if(tick().prefetch)break;}d.prefetch_valid=0;prefetch_current=index;}
 void ready(unsigned count){for(unsigned n=0;d.prefetched_count<count;n++){need(n<50000,"strip ready timeout index="+std::to_string(count)+" cmds="+std::to_string(commands)+" words="+std::to_string(words));tick();}while(d.prefetch_done_valid)tick();}
 void consume(unsigned index){d.consume_index=index;d.consume_valid=1;for(unsigned n=0;;n++){need(n<100,"consume timeout");if(tick().consume)break;}d.consume_valid=0;}
 void query(unsigned u,unsigned v){d.pixel_u=u;d.pixel_v=v;d.pixel_req_valid=1;for(unsigned n=0;;n++){need(n<100,"pixel request timeout");if(tick().pixel)break;}d.pixel_req_valid=0;}
 void flush(){d.pixel_req_valid=0;d.pixel_rsp_ready=1;for(unsigned n=0;!q.empty();n++){need(n<100,"pixel drain timeout");tick();}}
 void abort_now(){d.pixel_req_valid=0;d.abort_i=1;req_held=false;canceled+=q.size();q.clear();d.eval();tick();d.abort_i=0;
  for(unsigned n=0;d.active||pending;n++){need(n<1000,"abort drain timeout");tick();}tick();need(!d.prefetch_done_valid&&!d.pixel_rsp_valid&&d.desc_ready,"abort left old publication/lease");}
 void blocked_prefetch(unsigned i){auto before=commands;d.prefetch_valid=1;d.prefetch_index=i;for(unsigned n=0;n<9;n++){need(!tick().prefetch,"invalid prefetch accepted");}d.prefetch_valid=0;need(commands==before,"invalid prefetch issued memory");}
 void blocked_consume(unsigned i){d.consume_valid=1;d.consume_index=i;for(unsigned n=0;n<9;n++)need(!tick().consume,"invalid consume accepted");d.consume_valid=0;}
};
int main(int argc,char**argv){try{need(argc==3,"seed trace.mem");unsigned seed=unsigned(std::stoul(argv[1]));std::ifstream f(argv[2]);need(bool(f),"trace open");std::array<std::vector<unsigned>,90> expected;std::string line;while(std::getline(f,line)){auto n=std::stoul(line,nullptr,16);expected[n>>24].push_back(n&0xffffff);}
 Sim s(seed);unsigned full=0,faults=0,rejects=0;for(auto meta:std::array<std::array<unsigned,3>,3>{{{0,0,0},{1,0xffffffffu,0},{1,0,3}}}){s.descriptor(meta[0],meta[1],meta[2],0);need(!s.d.active&&s.d.error&&s.commands==0,"bad descriptor escaped");rejects++;}
 for(unsigned epoch=0;epoch<2;epoch++){
  s.commands=s.words=0;for(auto&v:s.requests)v.clear();s.descriptor(5+epoch,10+epoch,epoch?2:0,epoch?9:0);need(s.d.active&&!s.d.error,"descriptor start");
  s.blocked_prefetch(1);rejects++;s.blocked_consume(0);rejects++;s.query(0,0);s.flush();s.prefetch(0);s.ready(1);s.prefetch(1);s.ready(2);
  for(unsigned strip=0;strip<90;strip++){
   if(strip==0){s.blocked_consume(1);rejects++;s.blocked_prefetch(1);rejects++;s.d.finish_valid=1;need(!s.d.finish_ready,"early finish");s.tick();s.d.finish_valid=0;rejects++;}
   if(strip+2<90)s.prefetch(strip+2);
   for(unsigned u=strip*8;u<strip*8+8;u++)for(unsigned v=0;v<480;v++){
    s.d.pixel_rsp_ready=1;s.query(u,v);if(seed&&((u*480+v)%127==37)){s.d.pixel_rsp_ready=0;for(unsigned n=0;n<3;n++)s.tick();s.d.pixel_rsp_ready=1;}
   }
   s.flush();if(strip+2<90)s.ready(strip+3);if(strip==0){s.blocked_prefetch(3);rejects++;}s.consume(strip);
  }
  s.query(0,0);s.flush();s.query(720,480);s.flush();need(s.d.read_commands==35040&&s.d.read_words==280320&&s.commands==35040&&s.words==280320,"frame traffic counts");
  for(unsigned strip=0;strip<90;strip++){auto a=s.requests[strip],b=expected[strip];for(auto&x:a)x-=s.bank*0x400000;std::sort(a.begin(),a.end());std::sort(b.begin(),b.end());need(a==b,"perstrip physical address set "+std::to_string(strip));}
  need(s.d.finish_ready,"complete finish not ready");s.d.finish_valid=1;s.tick();s.d.finish_valid=0;need(!s.d.active,"finish not released");full++;std::cout<<"CACHE_FRAME_PASS epoch="<<epoch<<" commands="<<s.commands<<" words="<<s.words<<" pixels=345600 cycles="<<s.cycles<<std::endl;
 }
 for(unsigned kind=0;kind<3;kind++)for(unsigned pos=0;pos<8;pos++){
  s.commands=s.words=0;s.bad_last=kind==1?int(pos):-1;s.bad_error=kind==2?int(pos):-1;s.descriptor(100+faults,100+faults,0,3);s.prefetch(0);
  for(unsigned n=0;!s.pending||s.words<pos;n++){need(n<300,"fault setup");s.tick();}
  if(kind==0)s.abort_now();else{for(unsigned n=0;s.d.active||s.pending;n++){need(n<500,"fault drain");s.tick();}need(s.d.error&&s.d.error_code==2&&!s.d.prefetch_done_valid,"memory error published");}
  need(s.commands==1&&s.words==8,"accepted memory error/abort did not drain8");s.bad_last=s.bad_error=-1;faults++;
 }
 s.descriptor(900,900,0,8);s.prefetch(0);s.ready(1);s.query(0,0);s.d.pixel_rsp_ready=0;s.prefetch(1);while(!s.pending||s.beat<2)s.tick();
 s.force_stall=true;auto oldgen=s.d.active_generation;s.d.desc_valid=1;s.d.desc_generation=901;s.d.desc_frame_id=901;s.d.desc_bank=2;
 for(unsigned n=0;n<9;n++){need(!s.tick().desc,"replacement epoch accepted while response held");need(s.d.active_generation==oldgen,"active epoch mutated");}
 s.d.desc_valid=0;rejects++;s.abort_now();s.force_stall=false;s.d.pixel_rsp_ready=1;need(s.d.read_commands==481&&s.d.read_words==3848,"held epoch abort did not drain exactly accepted burst");faults++;
 s.descriptor(999,999,0,4);s.force_stall=true;s.prefetch(0);for(unsigned n=0;n<10;n++)s.tick();s.abort_now();s.force_stall=false;need(s.d.read_commands==0,"preissue abort issued memory");faults++;
 std::cout<<"CACHE_PASS seed="<<seed<<" rasters="<<full<<" active_pixels="<<full*345600<<" fault_probes="<<faults<<" invalid_requests="<<rejects<<" accepted_pixel_queries="<<s.queries<<" pixel_responses="<<s.responses<<" canceled_pixel_responses="<<s.canceled<<" held_pixel_cycles="<<s.holds<<" cycles="<<s.cycles<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
