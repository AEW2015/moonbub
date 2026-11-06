#include "Vcu78_direct_scanout.h"
#include "verilated.h"
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"packetopen");return {std::istreambuf_iterator<char>(f),{}};}
struct Ev{bool desc=false,present=false;};
struct Sim{
 std::unique_ptr<VerilatedContext>c=[](){auto v=std::make_unique<VerilatedContext>();v->threads(1);return v;}();Vcu78_direct_scanout d{c.get()};
 std::array<std::shared_ptr<const cu66::Frame>,3>frames;
 std::map<unsigned,std::array<uint16_t,8>>mem;
 uint64_t cycles=0,next_pixel=17029,pixels=0,good=0;unsigned seed=0,sequence=0,errors=0,presents=0,held=0,request_holds=0,descriptor_waits=0,previous_front_bank=3;bool request_stalled=false;unsigned held_request_address=0;
 bool memory_pending=false;unsigned address=0,beat=0,delay=0;bool response_valid=false;
 unsigned linepix=0,lines=0;uint64_t raster_gen=0;bool raster_good=false;
 std::array<unsigned,4>complete{};std::array<unsigned,4>first_boundary{};
 explicit Sim(const std::filesystem::path&index,unsigned s):seed(s){
  std::ifstream f(index);std::string l;cu66::Decoder dec;
  for(unsigned b=0;b<3;b++){need(bool(std::getline(f,l)),"threefixtures");std::stringstream row(l);std::string chain,ordinal,path;std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');need(chain=="0","chronologicalcohort");frames[b]=dec.receive(load(index.parent_path()/path));
   unsigned base=0x80000+b*0x400000,hbase=0x100000+b*0x400000;
   for(unsigned p=0;p<3;p++){unsigned w=p?360:720,h=p?240:480,off=p==0?0:p==1?172800:216000;
    for(unsigned ti=0;ti<(w/8)*(h/8);ti++)for(unsigned k=0;k<32;k+=8){std::array<uint16_t,8>a{};for(unsigned i=0;i<8;i++){unsigned j=k+i,x=(ti%(w/8))*8+(j%4)*2,y=(ti/(w/8))*8+j/4;a[i]=uint16_t(frames[b]->planes[p][y*w+x])|(uint16_t(frames[b]->planes[p][y*w+x+1])<<8);}mem[base+off+ti*32+k]=a;}}
   std::vector<uint16_t>hud;for(auto&p:frames[b]->hud)hud.insert(hud.end(),p.words.begin(),p.words.end());need(hud.size()==21120,"HUDsize");for(unsigned at=0;at<hud.size();at+=8){std::array<uint16_t,8>a{};std::copy_n(hud.begin()+at,8,a.begin());mem[hbase+at]=a;}
  }
  d.mem_clk=0;d.pixel_clk=0;d.mem_rst=1;d.pixel_reset_n=0;d.descriptor_valid=0;d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_data=0;d.mem_rsp_last=0;d.mem_rsp_error=0;d.eval();for(unsigned i=0;i<10;i++)tick();d.mem_rst=0;d.pixel_reset_n=1;
 }
 void pixel(){if(!d.front_valid||!d.data_enable)return;unsigned x=d.physical_x,y=d.physical_y;need(x<480&&y<800,"physicalbounds");uint64_t gen=d.front_generation;need(gen>=1&&gen<=3&&d.front_frame_id==frames[gen-1]->id&&d.front_bank==gen-1,"visibleidentity");
  if(x==0&&y==0){linepix=lines=0;raster_gen=gen;raster_good=true;}
  need(x==linepix&&y==lines&&raster_gen==gen,"mixedgeneration/rasterorder");
  uint16_t want=(40<=y&&y<760)?frames[gen-1]->display[x*720+y-40]:0;uint16_t got=uint16_t((d.red>>3)<<11|(d.green>>2)<<5|(d.blue>>3));
  need(got==want,"nativepixel mismatch gen="+std::to_string(gen)+" x="+std::to_string(x)+" y="+std::to_string(y)+" expected="+std::to_string(want)+" got="+std::to_string(got));good++;pixels++;linepix++;
  if(x==479){linepix=0;lines++;if(y==799&&raster_good){complete[gen]++;std::cout<<"SCAN_RASTER_PASS generation="<<gen<<" fid="<<frames[gen-1]->id<<" repeats="<<complete[gen]<<" cycles="<<cycles<<std::endl;}}
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t n=std::min(target,next_pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());need(n>=c->time(),"eventtime");c->timeInc(n-c->time());bool rising=false;if(n==next_pixel){d.pixel_clk=!d.pixel_clk;rising=d.pixel_clk;next_pixel+=17029;}d.eval();if(rising)pixel();}}
 void drive(){
  d.mem_req_ready=!memory_pending&&(seed==0||cycles%5!=0);
  if(memory_pending&&!response_valid){if(delay)delay--;else response_valid=true;}
  d.mem_rsp_valid=response_valid;d.mem_rsp_data=memory_pending?mem.at(address)[beat]:0;d.mem_rsp_last=beat==7;d.mem_rsp_error=0;
 }
 Ev tick(){need(cycles<20000000,"scanoutwatchdog");drive();d.eval();uint64_t t=c->time();advance(t+5000);d.eval();Ev e;e.desc=d.descriptor_valid&&d.descriptor_ready;bool rq=d.mem_req_valid&&d.mem_req_ready,rs=d.mem_rsp_valid&&d.mem_rsp_ready;
  unsigned rqaddr=d.mem_req_addr;
  if(request_stalled)need(d.mem_req_valid&&rqaddr==held_request_address,"heldmemoryrequestchanged");
  request_stalled=d.mem_req_valid&&!d.mem_req_ready;if(request_stalled){held_request_address=rqaddr;request_holds++;}
  if(d.mem_rsp_valid&&!d.mem_rsp_ready)held++;
  if(d.presented){need(d.scanout_drained,"presentedwithoutoldreadDrain");need(!d.data_enable,"visiblechangedinactivepixels");if(previous_front_bank<3&&memory_pending)need((address>>22)!=previous_front_bank,"oldacceptedreadsurvivedswitch");previous_front_bank=d.front_bank;presents++;first_boundary[d.front_generation]=unsigned(cycles);}
  if(d.error)errors++;
  d.mem_clk=1;d.eval();advance(t+10000);d.mem_clk=0;d.eval();cycles++;
  if(rs){response_valid=false;beat++;if(beat==8){memory_pending=false;beat=0;}else delay=seed?unsigned((sequence+beat)%3):0;}
  if(rq){need(!memory_pending,"multiplememorybursts");need(rqaddr%8==0&&mem.count(rqaddr),"unmappedread");memory_pending=true;address=rqaddr;beat=0;delay=seed?sequence%7:0;sequence++;}
  return e;
 }
 void descriptor(unsigned gen,unsigned fid,unsigned bank){d.descriptor_generation=gen;d.descriptor_frame_id=fid;d.descriptor_bank=bank;d.descriptor_valid=1;for(unsigned n=0;!tick().desc;n++){need(n<3000000,"descriptorwait");descriptor_waits++;}d.descriptor_valid=0;}
 void until(unsigned gen,unsigned count){while(complete[gen]<count){tick();need(d.memory_errors==0&&d.underruns==0,"scanouterror/underrun mem="+std::to_string(d.memory_errors)+" under="+std::to_string(d.underruns));}}
 void run(){
  descriptor(1,frames[0]->id,0);until(1,1);
  // After old lines are converted, a committed descriptor arrives while the
  // repeat epoch is already prepared. It must remain pending without relabeling.
  while(!(d.data_enable&&d.physical_x==0&&d.physical_y==780))tick();
  unsigned prior=complete[1];descriptor(2,frames[1]->id,1);need(d.pending_valid,"latependingnotretained");unsigned held_before=descriptor_waits;descriptor(1,frames[0]->id,0);tick();need(descriptor_waits>held_before,"pendingdescriptorwasnotbackpressured");unsigned start=cycles;while(d.front_generation==1){tick();need(cycles-start<4000000,"latependingnotpresented");}
  need(complete[1]>prior,"latepreparedrepeatnotretained");until(2,1);
  descriptor(3,frames[2]->id,2);until(3,1);
  unsigned before=presents,err=errors;
  descriptor(2,frames[1]->id,1);tick();descriptor(4,0xffffffffu,0);tick();descriptor(4,3,3);tick();descriptor(4,3,2);tick();
  need(errors==err+4,"invaliddescriptorerrors");need(d.front_generation==3&&!d.pending_valid&&presents==before,"invaliddescriptorpublished");until(3,2);
  need(presents==3&&d.presented_count==3&&d.memory_errors==0&&d.underruns==0,"presentationorerrorcounts");need(complete[1]>=2&&complete[2]>=1&&complete[3]>=2,"repeatsources");
  std::cout<<"SCANOUT_PASS seed="<<seed<<" distinct_sources="<<presents<<" source0_rasters="<<complete[1]<<" source1_rasters="<<complete[2]<<" source2_rasters="<<complete[3]<<" native_pixels="<<pixels<<" exact_pixels="<<good<<" invalid_descriptors=5 late_pending=1 descriptor_wait_cycles="<<descriptor_waits<<" request_hold_cycles="<<request_holds<<" memory_bursts="<<sequence<<" read_words="<<d.cache_read_words<<" cache_queries="<<d.cache_pixel_queries<<" raster_cache_epochs="<<d.raster_count<<" underruns="<<d.underruns<<" memory_errors="<<d.memory_errors<<" cycles="<<cycles<<std::endl;
 }
};
int main(int argc,char**argv){try{need(argc==3,"index seed");Sim s(argv[1],unsigned(std::stoul(argv[2])));s.run();}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
