#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include "Vcu71_yuv_pixel_pipe.h"
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
 Vcu71_yuv_pixel_pipe d;std::mt19937 rng;unsigned seed;std::deque<Expected>q;
 uint64_t cycles=0,compared=0,run=0,max_run=0;uint32_t tag=1;unsigned reset_drops=0;
 Sim(unsigned s):rng(s),seed(s){d.clk=0;d.rst=1;d.in_valid=0;tick();tick();d.rst=0;}
 void tick(){
  d.clk=0;d.eval();d.clk=1;d.eval();cycles++;
  if(d.rst){need(!d.out_valid,"resetvalid");run=0;return;}
  if(d.out_valid){need(!q.empty(),"unownedpixel");auto e=q.front();q.pop_front();need(d.out_tag==e.tag,"pixelidentity");need(d.out_rgb==e.rgb,"nativeRGBmismatch tag="+std::to_string(e.tag)+" expected="+std::to_string(e.rgb)+" got="+std::to_string(d.out_rgb));need(cycles-e.cycle==5,"fixed5stagealignment");compared++;run++;max_run=std::max(max_run,run);}else run=0;
 }
 void reset_probe(){
  for(unsigned n=0;n<3;n++){d.in_valid=1;d.in_tag=tag++;d.in_y=91;d.in_cb_t0=d.in_cb_t1=d.in_cb_b0=d.in_cb_b1=128;d.in_cr_t0=d.in_cr_t1=d.in_cr_b0=d.in_cr_b1=128;d.in_x_odd=d.in_y_odd=d.in_hud_hit=0;q.push_back({d.in_tag,0,cycles});tick();}
  reset_drops+=q.size();q.clear();d.rst=1;d.in_valid=0;tick();tick();d.rst=0;need(!d.busy,"resetbusy");tag+=1000;
 }
 void frame(const cu66::Frame&f,const std::string&name){
  auto oracle=cu66::render(f.planes,f.hud);uint64_t before=compared;
  for(unsigned u=0;u<720;u++)for(unsigned v=0;v<480;v++){
   if(seed&&rng()%4==0){d.in_valid=0;tick();}
   const unsigned cx=u/2,cy=v/2,cx1=std::min(cx+1,359u),cy1=std::min(cy+1,239u);
   d.in_y=f.planes[0][v*720+u];d.in_cb_t0=f.planes[1][cy*360+cx];d.in_cb_t1=f.planes[1][cy*360+cx1];d.in_cb_b0=f.planes[1][cy1*360+cx];d.in_cb_b1=f.planes[1][cy1*360+cx1];
   d.in_cr_t0=f.planes[2][cy*360+cx];d.in_cr_t1=f.planes[2][cy*360+cx1];d.in_cr_b0=f.planes[2][cy1*360+cx];d.in_cr_b1=f.planes[2][cy1*360+cx1];
   d.in_x_odd=u&1;d.in_y_odd=v&1;d.in_hud_hit=0;d.in_hud_word=0;
   for(const auto&p:f.hud)if(u>=p.rect[0]&&u<p.rect[0]+p.rect[2]&&v>=p.rect[1]&&v<p.rect[1]+p.rect[3]){d.in_hud_hit=1;d.in_hud_word=p.words[(v-p.rect[1])*p.rect[2]+u-p.rect[0]];}
   d.in_valid=1;d.in_tag=tag++;q.push_back({d.in_tag,oracle[v*720+u],cycles});tick();
  }
  d.in_valid=0;for(unsigned n=0;n<6;n++)tick();need(q.empty()&&!d.busy,"pipelinedrain");need(compared-before==345600,"fullcanvascount");
  std::cout<<"PIXEL_FRAME_PASS name="<<name<<" compared=345600"<<std::endl;
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
int main(int argc,char**argv){try{need(argc>=3,"index seed");unsigned seed=std::stoul(argv[2]);Sim sim(seed);sim.reset_probe();std::filesystem::path index=argv[1];std::ifstream file(index);need(bool(file),"indexopen");unsigned previous=~0u,count=0,actual=0;cu66::Decoder decoder;std::string line;
 while(std::getline(file,line)){std::stringstream s(line);std::string chain,n,path;std::getline(s,chain,'\t');std::getline(s,n,'\t');std::getline(s,path,'\t');unsigned c=std::stoul(chain);if(c!=previous){previous=c;count=0;decoder=cu66::Decoder();}if(count++>=2)continue;auto f=decoder.receive(load(index.parent_path()/path));sim.frame(*f,"actual"+chain+"_"+n);actual++;}
 need(actual==8,"keyPcoverage");for(unsigned k=0;k<4;k++)sim.frame(pattern(k),"pattern"+std::to_string(k));sim.frame(pattern(0),"recovery");need(sim.reset_drops==3,"resetprobedropcount");if(seed==0)need(sim.max_run==345600,"onepixelperclock");std::cout<<"CU71_PIXEL_PIPE_PASS actual_frames=8 patterns=4 recovery=1 compared="<<sim.compared<<" max_consecutive_outputs="<<sim.max_run<<" reset_drops="<<sim.reset_drops<<" seed="<<seed<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}return 0;}
