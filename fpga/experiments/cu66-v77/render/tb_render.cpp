#include "Vcu77_render_sim.h"
#include "verilated.h"
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include <array>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"fixture open");return {std::istreambuf_iterator<char>(f),{}};}
struct Sim{
 std::unique_ptr<VerilatedContext> c=[](){auto v=std::make_unique<VerilatedContext>();v->threads(1);return v;}();Vcu77_render_sim d{c.get()};
 std::mt19937 rng;bool random;uint64_t clocks=0,gen=0;unsigned bank=0,accepted=0,emitted=0,pf=0,cons=0,cmds=0,words=0,beat=0,delay=0,address=0;
 bool pending=false,present=false;std::vector<uint16_t>mem=std::vector<uint16_t>(1u<<24),gold;std::array<uint16_t,8>saved{};std::deque<unsigned>coords;unsigned mode=0;
 bool held=false;unsigned hu=0,hv=0,hr=0,he=0;bool mheld=false;unsigned ma=0;
 explicit Sim(unsigned seed):rng(seed),random(seed!=0){d.clk=0;d.rst=1;d.abort_i=0;d.desc_valid=0;d.finish_valid=0;d.prefetch_valid=0;d.prefetch_done_ready=1;d.consume_valid=0;d.pixel_req_valid=0;d.rgb_ready=0;d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_last=0;d.mem_rsp_error=0;d.mem_rsp_data=0;step();step();d.rst=0;step();}
 struct E{bool desc,prefetch,consume,request,response,query,pixel,finish;unsigned addr,u,v,rgb;bool error;};
 E step(){d.clk=0;d.eval();if(held&&!d.abort_i){need(d.rgb_valid&&d.rgb_u==hu&&d.rgb_v==hv&&d.rgb_data==hr&&d.rgb_error==he,"held RGB changed");}if(mheld&&!d.abort_i)need(d.mem_req_valid&&d.mem_req_addr==ma,"held memory request changed");
  E e{bool(d.desc_valid&&d.desc_ready),bool(d.prefetch_valid&&d.prefetch_ready),bool(d.consume_valid&&d.consume_ready),bool(d.mem_req_valid&&d.mem_req_ready),bool(d.mem_rsp_valid&&d.mem_rsp_ready),bool(d.pixel_req_valid&&d.pixel_req_ready),bool(d.rgb_valid&&d.rgb_ready),bool(d.finish_valid&&d.finish_ready),d.mem_req_addr,d.rgb_u,d.rgb_v,d.rgb_data,bool(d.rgb_error)};
  held=d.rgb_valid&&!d.rgb_ready&&!d.abort_i;hu=d.rgb_u;hv=d.rgb_v;hr=d.rgb_data;he=d.rgb_error;mheld=d.mem_req_valid&&!d.mem_req_ready&&!d.abort_i;ma=d.mem_req_addr;
  d.clk=1;d.eval();clocks++;need(clocks<400000000,"global watchdog");return e;
 }
 unsigned canonical()const{return bank==0?0x80000:bank==1?0x480000:0x880000;}unsigned hudbase()const{return bank==0?0x100000:bank==1?0x500000:0x900000;}
 void prepare(const cu66::Frame&f){
  for(unsigned p=0;p<3;p++){unsigned w=p?360:720,h=p?240:480,base=canonical()+(p==0?0:p==1?172800:216000);for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x+=2){unsigned tile=(y/8)*(w/8)+x/8,at=base+tile*32+(y%8)*4+(x%8)/2;mem[at]=f.planes[p][y*w+x]|(unsigned(f.planes[p][y*w+x+1])<<8);}}
  unsigned off=0;for(auto&p:f.hud)for(auto v:p.words)mem[hudbase()+off++]=v;need(off==21120,"HUD complete");gold=cu66::render(f.planes,f.hud);
 }
 void drive(){
  d.mem_req_ready=!pending&&(!random||rng()%4);if(pending&&delay)delay--;if(pending&&!delay&&!present&&(!random||rng()%3))present=true;
  d.mem_rsp_valid=pending&&present;d.mem_rsp_data=pending?saved[beat]:0;d.mem_rsp_last=pending&&beat==7;d.mem_rsp_error=mode==2&&pending&&beat==3;
  d.prefetch_valid=pf<90;d.prefetch_index=pf;d.prefetch_done_ready=1;
  unsigned strip=accepted/3840;d.pixel_req_valid=accepted<345600&&strip==cons&&strip<d.prefetched_count&&(!random||rng()%5);d.pixel_u=strip*8+(accepted%3840)/480;d.pixel_v=accepted%480;
  d.rgb_ready=!random||rng()%4;d.consume_valid=cons<90&&emitted>=(cons+1)*3840&&d.pixel_inflight==0;d.consume_index=cons;
 }
 void service(const E&e){
  if(e.response){need(pending&&present,"unowned memory response");words++;present=false;if(beat==7){pending=false;beat=0;}else{beat++;delay=random?rng()%3:0;}}
  if(e.request){need(!pending,"multiple memory bursts");need(e.addr%8==0&&((e.addr>=canonical()&&e.addr+7<canonical()+259200)||(e.addr>=hudbase()&&e.addr+7<hudbase()+21120)),"physical address guard");pending=true;present=false;address=e.addr;beat=0;delay=random?1+rng()%8:0;for(unsigned i=0;i<8;i++)saved[i]=mem.at(e.addr+i);cmds++;}
  if(e.prefetch)pf++;if(e.consume)cons++;
  if(e.query){coords.push_back(accepted);accepted++;}
  if(e.pixel){need(!coords.empty(),"unowned RGB output");unsigned at=coords.front();coords.pop_front();unsigned u=(at/3840)*8+(at%3840)/480,v=at%480;need(!e.error&&e.u==u&&e.v==v,"RGB error/order");need(e.rgb==gold[v*720+u],"native RGB mismatch u="+std::to_string(u)+" v="+std::to_string(v)+" got="+std::to_string(e.rgb)+" want="+std::to_string(gold[v*720+u]));emitted++;}
 }
 void run(const cu66::Frame&f,const std::string&name,unsigned fault=0){
  need(d.desc_ready&&!pending&&d.pixel_inflight==0,"descriptor lease readiness");gen++;bank=(gen-1)%3;prepare(f);accepted=emitted=pf=cons=cmds=words=0;coords.clear();held=mheld=false;mode=fault;d.desc_generation=gen;d.desc_frame_id=f.id;d.desc_bank=bank;d.desc_valid=1;need(step().desc,"descriptor accept");d.desc_valid=0;auto start=clocks;bool aborted=false,stop=false;
  while(!stop){need(clocks-start<10000000,"frame watchdog");drive();if(fault==1&&accepted>20&&d.pixel_inflight>0){d.rgb_ready=0;d.abort_i=1;aborted=true;}
   if(aborted||d.error){d.prefetch_valid=0;d.pixel_req_valid=0;d.consume_valid=0;d.rgb_ready=1;if(d.error)d.abort_i=1;}
   auto e=step();if(d.abort_i){coords.clear();held=false;}service(e);d.abort_i=0;
   if(!fault&&cons==90){need(emitted==345600&&accepted==345600&&coords.empty()&&!pending&&d.pixel_inflight==0,"completeframe drain");d.prefetch_valid=0;d.pixel_req_valid=0;d.consume_valid=0;d.finish_valid=1;need(step().finish,"finish handshake");d.finish_valid=0;stop=true;}
   if(fault&&!d.active&&!pending){need(d.pixel_inflight==0,"aborted pixel pipeline drain");stop=true;}
  }
  if(!fault)need(cmds==35040&&words==280320&&d.read_commands==35040&&d.read_words==280320&&d.pixel_queries==345600&&d.cache_misses==0&&!d.error,"full counts");
  else if(fault==1)need(aborted,"abort probe not reached");else need(d.error,"memory fault not rejected");
  for(unsigned i=0;i<5;i++){d.mem_req_ready=0;d.mem_rsp_valid=0;d.prefetch_valid=0;d.pixel_req_valid=0;d.consume_valid=0;d.rgb_ready=1;step();}need(d.desc_ready&&!pending&&!d.rgb_valid,"restart after drain");
  std::cout<<"RENDER_CASE_PASS name="<<name<<" mode="<<fault<<" cycles="<<clocks-start<<" commands="<<cmds<<" words="<<words<<" pixels="<<emitted<<" accepted="<<accepted<<" generation="<<gen<<" bank="<<bank<<"\n";
 }
};
static cu66::Frame pattern(unsigned kind){cu66::Frame f;f.id=100+kind;for(unsigned p=0;p<3;p++){unsigned w=p?360:720,h=p?240:480;f.planes[p].resize(w*h);for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++){unsigned v=(x*37+y*61+kind*53+p*127)&255;if(kind==1)v=((x^y)&1)?0:255;if(kind==2)v=p==0?0:p==1?255:0;if(kind==3)v=p==0?255:p==1?0:255;f.planes[p][y*w+x]=v;}}for(unsigned r=0;r<4;r++){cu66::Patch p;for(unsigned i=0;i<4;i++)p.rect[i]=cu66::RECTS[r][i];for(unsigned i=0;i<unsigned(p.rect[2])*p.rect[3];i++)p.words.push_back((i*313+r*0x173b+kind*79)&65535);f.hud.push_back(p);}return f;}
int main(int argc,char**argv){try{need(argc>=3,"index seed");unsigned seed=std::stoul(argv[2]);Sim s(seed);std::filesystem::path index=argv[1];std::ifstream file(index);need(bool(file),"index open");unsigned previous=~0u,count=0,actual=0;cu66::Decoder decoder;std::string line;while(std::getline(file,line)){std::stringstream row(line);std::string chain,n,path;std::getline(row,chain,'\t');std::getline(row,n,'\t');std::getline(row,path,'\t');unsigned c=std::stoul(chain);if(c!=previous){if(actual>=8)break;decoder=cu66::Decoder();previous=c;count=0;}if(count++>=2)continue;auto f=decoder.receive(load(index.parent_path()/path));s.run(*f,"actual"+chain+"_"+n);actual++;}need(actual==8,"actual key/P coverage");for(unsigned k=0;k<4;k++)s.run(pattern(k),"pattern"+std::to_string(k));if(seed){s.run(pattern(0),"abort",1);s.run(pattern(0),"memerror",2);}s.run(pattern(0),"recovery");std::cout<<"RENDER_PASS actual_frames=8 patterns=4 recovery=1 full_frames=13 RGB_words=4492800 fault_probes="<<(seed?2:0)<<" seed="<<seed<<"\n";}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
