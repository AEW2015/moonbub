#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include "Vcu71_cache_pixel_test.h"
#include "verilated.h"
#include <deque>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
static void need(bool v,const std::string&s){if(!v)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"fixtureopen");return{std::istreambuf_iterator<char>(f),{}};}
struct Expected{uint32_t tag;uint16_t rgb;uint64_t cycle;};
struct Sim{
 Vcu71_cache_pixel_test d;std::mt19937 rng;unsigned seed;std::deque<Expected>q;
 uint64_t cycles=0,compared=0,run=0,max_run=0,writes=0;uint32_t tag=1;unsigned cases=0,rejected_writes=0;
 Sim(unsigned s):rng(s),seed(s){d.clk=0;d.rst=1;d.rd_valid=0;d.wr_valid=0;d.wr_allow=1;d.front_valid=0;d.render_live=0;tick();tick();d.rst=0;}
 void tick(){
  d.clk=0;d.eval();d.clk=1;d.eval();cycles++;
  if(d.rst){need(!d.out_valid,"resetvalid");run=0;return;}
  if(d.out_valid){need(!q.empty(),"unownedpixel");auto e=q.front();q.pop_front();need(d.out_tag==e.tag,"pixelidentity");need(d.out_rgb==e.rgb,"cachednativeRGBmismatch tag="+std::to_string(e.tag)+" expected="+std::to_string(e.rgb)+" got="+std::to_string(d.out_rgb));need(cycles-e.cycle==6,"cacheplus5stagealignment");compared++;run++;max_run=std::max(max_run,run);}else run=0;
 }
 void write(unsigned context,unsigned kind,unsigned bank,unsigned row,uint64_t data,unsigned hud_index=0,unsigned hud_word=0,bool bad=false){
  d.rd_valid=0;d.wr_valid=1;d.wr_context=context;d.wr_kind=kind;d.wr_bank=bank;d.wr_row=row;d.wr_data=data;d.wr_hud_index=hud_index;d.wr_hud_word=hud_word;tick();need(bool(d.wr_error)==bad,"writepermissionbounds");if(bad)rejected_writes++;else writes++;d.wr_valid=0;
 }
 void page(const cu66::Frame&f,unsigned context,unsigned plane,unsigned group){
  unsigned width=plane?360:720,height=plane?240:480;
  need(group<width/8,"pagegroupbounds");
  for(unsigned row=0;row<height;row++){uint64_t data=0;for(unsigned k=0;k<8;k++)data|=uint64_t(f.planes[plane][row*width+group*8+k])<<(8*k);write(context,plane,group&1,row,data);}
 }
 void bad_read(unsigned context,unsigned u,unsigned v,unsigned hud_index,bool hit){
  d.wr_valid=0;d.rd_valid=1;d.rd_context=context;d.rd_u=u;d.rd_v=v;d.rd_hud_hit=hit;d.rd_hud_index=hud_index;d.rd_tag=tag++;tick();need(d.read_error,"badreadnotrejected");d.rd_valid=0;for(unsigned n=0;n<7;n++)tick();need(q.empty()&&!d.busy,"badreaddrainguard");
 }
 void reset_probe(){
  d.wr_valid=0;d.rd_valid=1;d.rd_context=d.front_context;d.rd_u=719;d.rd_v=0;d.rd_hud_hit=0;d.rd_hud_index=0;
  for(unsigned n=0;n<2;n++){d.rd_tag=tag++;q.push_back({d.rd_tag,0,cycles});tick();}
  need(q.size()==2,"resetqueuedpixels");q.clear();d.rst=1;d.rd_valid=0;d.front_valid=0;d.render_live=0;tick();tick();d.rst=0;tag+=10000;need(!d.busy,"resetflushedpipeline");
 }
 void frame(const cu66::Frame&f,const std::string&name){
  auto oracle=cu66::render(f.planes,f.hud);uint64_t before=compared;unsigned context=cases++&1;
  d.render_live=0;unsigned hi=0;
  for(const auto&p:f.hud)for(auto word:p.words)write(context,3,0,0,0,hi++,word);
  need(hi==21120,"fullHUDcache");
  d.front_valid=1;d.front_context=context;d.render_context=context;
  for(unsigned u=0;u<720;u++){
   d.render_live=0;
   if(u%8==0)page(f,context,0,u/8);
   if(u%16==0){unsigned g=u/16;if(u==0){page(f,context,1,0);page(f,context,2,0);}if(g+1<45){page(f,context,1,g+1);page(f,context,2,g+1);}}
   d.render_live=1;d.render_u=u;
   if(u==0){
    write(context,0,0,0,~uint64_t(0),0,0,true);
    write(context,1,0,0,~uint64_t(0),0,0,true);
    write(context,3,0,0,0,0,0x7bad,true);
    write(context,0,1,480,~uint64_t(0),0,0,true);
    write(context,1,1,240,~uint64_t(0),0,0,true);
    d.wr_allow=0;write(context,0,1,0,~uint64_t(0),0,0,true);d.wr_allow=1;
   }
   for(unsigned v=0;v<480;v++){
    if(seed&&rng()%4==0){d.rd_valid=0;tick();}
    d.rd_valid=1;d.rd_context=context;d.rd_u=u;d.rd_v=v;d.rd_tag=tag++;d.rd_hud_hit=0;d.rd_hud_index=0;
    unsigned base=0;for(const auto&p:f.hud){if(u>=p.rect[0]&&u<p.rect[0]+p.rect[2]&&v>=p.rect[1]&&v<p.rect[1]+p.rect[3]){d.rd_hud_hit=1;d.rd_hud_index=base+(v-p.rect[1])*p.rect[2]+u-p.rect[0];}base+=p.words.size();}
    q.push_back({d.rd_tag,oracle[v*720+u],cycles});tick();need(!d.read_error,"validreadrejected");
   }
   d.rd_valid=0;for(unsigned n=0;n<7;n++)tick();need(q.empty()&&!d.busy,"linepipelinedrain");
  }
  d.render_live=0;need(compared-before==345600,"fullcachedcanvascount");
  bad_read(context,720,0,0,false);bad_read(context,0,480,0,false);bad_read(context,0,0,21120,true);
  std::cout<<"CACHE_FRAME_PASS name="<<name<<" context="<<context<<" compared=345600"<<std::endl;
 }
};
static cu66::Frame pattern(unsigned kind) {
  cu66::Frame f;
  f.id = 100 + kind;
  for (unsigned a = 0; a < 3; a++) {
    unsigned w = a ? 360 : 720, h = a ? 240 : 480;
    f.planes[a].resize(w * h);
    for (unsigned y = 0; y < h; y++)
      for (unsigned x = 0; x < w; x++) {
        unsigned v = (x * 37 + y * 61 + kind * 53 + a * 127) & 255;
        if (kind == 1)
          v = ((x ^ y) & 1) ? 0 : 255;
        if (kind == 2)
          v = (a == 0 ? 0 : a == 1 ? 255 : 0);
        if (kind == 3)
          v = (a == 0 ? 255 : a == 1 ? 0 : 255);
        f.planes[a][y * w + x] = uint8_t(v);
      }
  }
  for (unsigned r = 0; r < 4; r++) {
    cu66::Patch p;
    for (unsigned i = 0; i < 4; i++)
      p.rect[i] = cu66::RECTS[r][i];
    for (unsigned i = 0; i < unsigned(p.rect[2]) * p.rect[3]; i++)
      p.words.push_back(uint16_t((i * 313 + r * 0x173b + kind * 79) & 65535));
    f.hud.push_back(p);
  }
  return f;
}
int main(int argc,char**argv){try{need(argc>=3,"index seed");unsigned seed=std::stoul(argv[2]);Sim sim(seed);std::filesystem::path index=argv[1];std::ifstream file(index);need(bool(file),"indexopen");unsigned previous=~0u,count=0,actual=0;cu66::Decoder decoder;std::string line;
 while(std::getline(file,line)){std::stringstream s(line);std::string chain,n,path;std::getline(s,chain,'\t');std::getline(s,n,'\t');std::getline(s,path,'\t');unsigned c=std::stoul(chain);if(c!=previous){previous=c;count=0;decoder=cu66::Decoder();}if(count++>=2)continue;auto f=decoder.receive(load(index.parent_path()/path));sim.frame(*f,"actual"+chain+"_"+n);actual++;}
 need(actual==8,"keyPcoverage");for(unsigned k=0;k<4;k++)sim.frame(pattern(k),"pattern"+std::to_string(k));sim.frame(pattern(0),"recovery");sim.reset_probe();sim.frame(pattern(1),"after_reset");if(seed==0)need(sim.max_run==480,"onepixelperclockline");std::cout<<"CU71_CACHE_PIXEL_PASS actual_frames=8 patterns=4 recovery=1 reset_recovery=1 compared="<<sim.compared<<" max_consecutive_outputs="<<sim.max_run<<" rejected_writes="<<sim.rejected_writes<<" seed="<<seed<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}return 0;}
