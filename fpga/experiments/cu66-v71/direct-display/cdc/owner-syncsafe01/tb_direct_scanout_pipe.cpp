#include "/mnt/c/mb70/experiments/cu66-native-v69/decoder.hpp"
#include "Vcu71_direct_scanout_syncsafe.h"
#include "verilated.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"fixture open");return{std::istreambuf_iterator<char>(f),{}};}
struct Sim{
 Vcu71_direct_scanout_syncsafe d;std::mt19937 rng;unsigned seed;std::vector<uint16_t>mem=std::vector<uint16_t>(1<<24,0xdead);std::vector<uint16_t>gold[2];
 uint64_t time=0,nm=5000,np=17030,mc=0,pc=0,pixels[2]={0,0},reads=0;bool pending=false,abort_ack=false;unsigned addr=0,delay=0;bool checking=false;unsigned held_addr=0;bool held=false;
 Sim(unsigned s):rng(s),seed(s){d.mem_clk=0;d.pixel_clk=0;d.rst=1;d.pixel_reset_n=0;d.prepare_valid=0;d.prepared_ready=0;d.prepare_abort_valid=0;d.descriptor_valid=0;d.lcd_req_ready=0;d.lcd_rsp_valid=0;d.lcd_rsp_error=0;d.lcd_busy=0;d.lcd_aborted=0;for(int i=0;i<30;i++)step();d.rst=0;}
 void install(const cu66::Frame&f,unsigned bank){gold[bank]=cu66::render(f.planes,f.hud);unsigned base=0x80000+bank*0x400000;unsigned po[3]={0,172800,216000};for(unsigned p=0;p<3;p++){unsigned w=p?360:720,h=p?240:480;for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x+=2){unsigned a=base+po[p]+((y/8)*(w/8)+(x/8))*32+(y%8)*4+(x%8)/2;mem[a]=f.planes[p][y*w+x]|(uint16_t(f.planes[p][y*w+x+1])<<8);}}unsigned a=0x100000+bank*0x400000;for(auto&p:f.hud)for(auto v:p.words)mem[a++]=v;}
 void step(){auto at=std::min(nm,np);bool me=at==nm,pe=at==np,mp=me&&!d.mem_clk,pp=pe&&!d.pixel_clk;time=at;bool req=false,rsp=false,prep=false,desc=false;unsigned a=0;
 if(mp){d.lcd_req_ready=!pending&&(!seed||rng()%5!=0);d.lcd_busy=pending;d.lcd_aborted=abort_ack;d.lcd_rsp_valid=pending&&delay==0&&!d.lcd_abort_i;d.lcd_rsp_error=0;if(d.lcd_rsp_valid)for(unsigned k=0;k<4;k++)d.lcd_rsp_data[k]=uint32_t(mem[addr+k*2])|(uint32_t(mem[addr+k*2+1])<<16);d.eval();if(held)need(d.lcd_req_valid&&d.lcd_req_addr==held_addr,"request unstable");held=d.lcd_req_valid&&!d.lcd_req_ready;held_addr=d.lcd_req_addr;req=d.lcd_req_valid&&d.lcd_req_ready;rsp=d.lcd_rsp_valid&&d.lcd_rsp_ready;a=d.lcd_req_addr;prep=d.prepare_valid&&d.prepare_ready;desc=d.descriptor_valid&&d.descriptor_ready;}
 if(me){d.mem_clk=!d.mem_clk;nm+=5000;}if(pe){d.pixel_clk=!d.pixel_clk;np+=17030;}d.eval();
 if(mp){mc++;abort_ack=false;if(pending&&delay)delay--;if(rsp)pending=false;if(d.lcd_abort_i&&pending){pending=false;abort_ack=true;}if(req){need(!pending,"multiple LCD requests");need((a&7)==0,"BL8 alignment");pending=true;addr=a;delay=seed?rng()%12:0;reads++;}if(prep)d.prepare_valid=0;if(desc)d.descriptor_valid=0;if(d.error)std::cout<<"OWNER_ERROR fault="<<unsigned(d.first_fault)<<" frame="<<d.first_fault_frame_id<<" mc="<<mc<<std::endl;}
 if(pp){pc++;if(checking&&d.front_valid&&d.data_enable){unsigned x=d.physical_x,y=d.physical_y,s=d.front_cache_slot;need(x<480&&y<800,"coords");uint16_t v=y>=40&&y<760?gold[s][x*720+y-40]:0;unsigned r=(v>>11)&31,g=(v>>5)&63,b=v&31;need(d.red==((r<<3)|(r>>2))&&d.green==((g<<2)|(g>>4))&&d.blue==((b<<3)|(b>>2)),"native raster mismatch x="+std::to_string(x)+" y="+std::to_string(y)+" slot="+std::to_string(s)+" expected="+std::to_string(v)+" actualRGB="+std::to_string(d.red)+","+std::to_string(d.green)+","+std::to_string(d.blue)+" underruns="+std::to_string(d.underruns)+" firstfault="+std::to_string(d.first_fault));pixels[s]++;}}
 need(mc<15000000,"owner watchdog fault="+std::to_string(d.first_fault)+" gen="+std::to_string(d.front_generation)+" prepared="+std::to_string(d.prepared_valid)+" reads="+std::to_string(reads));}
 void prepare(unsigned slot,unsigned gen,unsigned fid){d.prepare_cache_slot=slot;d.prepare_generation=gen;d.prepare_frame_id=fid;d.prepare_canonical_bank=slot;d.prepare_hud_bank=slot;d.prepare_valid=1;while(d.prepare_valid)step();while(!d.prepared_valid)step();need(!d.prepared_error&&d.prepared_generation==gen&&d.prepared_frame_id==fid&&d.prepared_cache_slot==slot,"prepared identity/error reason="+std::to_string(d.prepared_reason));d.prepared_ready=1;auto consume_at=mc+1;while(mc<consume_at)step();d.prepared_ready=0;}
 void descriptor(unsigned slot,unsigned gen,unsigned fid){d.descriptor_cache_slot=slot;d.descriptor_generation=gen;d.descriptor_frame_id=fid;d.descriptor_valid=1;while(d.descriptor_valid)step();}
 void memtick(){auto target=mc+1;while(mc<target)step();}
 void cancel(unsigned slot,unsigned gen,unsigned fid,bool expect_error){d.prepare_abort_cache_slot=slot;d.prepare_abort_generation=gen;d.prepare_abort_frame_id=fid;d.prepare_abort_valid=1;bool fired=false;for(unsigned n=0;n<10000;n++){d.eval();if(d.prepare_abort_ready){memtick();d.prepare_abort_valid=0;fired=true;break;}memtick();}need(fired,"abort admission watchdog");for(unsigned n=0;n<10000&&!d.abort_done;n++)memtick();need(d.abort_done&&bool(d.abort_error)==expect_error,"identity bound abort result gen="+std::to_string(gen)+" expectederror="+std::to_string(expect_error)+" done="+std::to_string(d.abort_done)+" error="+std::to_string(d.abort_error)+" reads="+std::to_string(reads)+" fault="+std::to_string(d.first_fault));need(expect_error||(!pending&&!d.lcd_busy),"abort acknowledged before adapter drain");memtick();}
 void controls(){
  unsigned gen=1;
  // Rejected bank3 cannot initiate a read or consume the free context.
  auto before=reads;d.prepare_generation=gen++;d.prepare_frame_id=10;d.prepare_cache_slot=0;d.prepare_canonical_bank=3;d.prepare_hud_bank=0;d.prepare_valid=1;while(d.prepare_valid)step();while(!d.prepared_valid)step();need(d.prepared_error&&reads==before,"bank3 reject before DMA");d.prepared_ready=1;memtick();d.prepared_ready=0;
  for(unsigned target: {1u,2641u,3000u,3500u}){
   unsigned g=gen++,fid=10+g;before=reads;d.prepare_generation=g;d.prepare_frame_id=fid;d.prepare_cache_slot=0;d.prepare_canonical_bank=0;d.prepare_hud_bank=0;d.prepare_valid=1;while(d.prepare_valid)step();while(reads-before<target)step();
   cancel(0,g+100,fid,true);need(!d.prepared_valid,"wrong identity must not complete PREPARE");cancel(0,g,fid,false);need(!d.prepared_valid&&!d.front_valid,"canceled context exposed completion");for(unsigned n=0;n<30;n++)memtick();need(!d.prepared_valid,"late canceled completion");
  }
  unsigned g=gen++;prepare(0,g,100);cancel(0,g,100,false);need(!d.prepared_valid,"READY context cancellation");
  g=gen++;prepare(0,g,101);descriptor(0,g,101);need(d.pending_valid,"pending descriptor");cancel(0,g,101,true);need(d.pending_valid,"PENDING cannot roll back");d.pixel_reset_n=1;while(!d.front_valid)step();cancel(0,g,101,true);need(d.front_valid&&d.front_generation==g,"FRONT cannot roll back");
  before=reads;d.prepare_generation=gen++;d.prepare_frame_id=102;d.prepare_cache_slot=0;d.prepare_valid=1;while(d.prepare_valid)step();while(!d.prepared_valid)step();need(d.prepared_error,"PREPARE must reject live FRONT slot");d.prepared_ready=1;memtick();d.prepared_ready=0;
  // Coordinated memory/pixel reset flushes ownership and accepted transactions.
  d.rst=1;d.pixel_reset_n=0;pending=false;held=false;for(unsigned n=0;n<10;n++)memtick();d.rst=0;need(!d.front_valid&&!d.pending_valid&&!d.prepared_valid&&d.first_fault==0,"coordinated reset ownership");prepare(0,100,200);need(d.accepted_prepares==1&&!d.prepared_error,"new context after reset");
  std::cout<<"CU71_DIRECT_OWNER_CONTROL_PASS abort_phases=4 wrong_identity=4 ready_abort=1 pending_front_protected=1 bank3_live_front_reject=1 coordinated_reset=1"<<std::endl;
 }
 void run(){auto before=reads;prepare(0,1,100);need(reads-before==3600,"cold prepare BL8 count="+std::to_string(reads-before));descriptor(0,1,100);checking=true;d.pixel_reset_n=1;while(!d.front_valid)step();std::cout<<"FRONT0 mc="<<mc<<" reads="<<reads<<std::endl;while(pixels[0]<384000)step();need(d.underruns==0&&d.first_fault==0,"front0 diagnostic");std::cout<<"RASTER0_PASS mc="<<mc<<" reads="<<reads<<std::endl;prepare(1,2,101);descriptor(1,2,101);while(pixels[1]<384000)step();need(d.front_generation==2&&d.front_frame_id==101&&d.presented_count==2,"front history");need(d.underruns==0&&d.first_fault==0&&d.memory_errors==0&&d.unowned_dma_responses==0,"final diagnostics");std::cout<<"CU71_DIRECT_OWNER_PASS seed="<<seed<<" pixels0="<<pixels[0]<<" pixels1="<<pixels[1]<<" reads="<<reads<<" generated="<<d.generated_lines<<" misses="<<d.line_cache_misses<<std::endl;}
};
int main(int argc,char**argv){try{need(argc==3||argc==4,"index seed [control]");Sim s(std::stoul(argv[2]));std::filesystem::path index=argv[1];std::ifstream f(index);std::string line;cu66::Decoder dec;unsigned n=0;while(n<2&&std::getline(f,line)){std::stringstream q(line);std::string c,k,p;std::getline(q,c,'\t');std::getline(q,k,'\t');std::getline(q,p,'\t');auto frame=dec.receive(load(index.parent_path()/p));s.install(*frame,n++);}need(n==2,"key/P fixtures");if(argc==4)s.controls();else s.run();}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}return 0;}


