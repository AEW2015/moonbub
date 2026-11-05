#ifdef ROWS_HASH
#include "Vcu66_rows_sha256.h"
using Model=Vcu66_rows_sha256;
#else
#include "Vcu66_tile_rows.h"
using Model=Vcu66_tile_rows;
#endif
#include "verilated.h"
#include <zlib.h>
#include <array>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
struct Fixture{std::string name,path,hash;};
static std::vector<Fixture> fixtures(const std::string&p){std::ifstream f(p);need(bool(f),"fixture manifest");std::vector<Fixture> out;std::string line;while(std::getline(f,line)){std::stringstream s(line);std::array<std::string,4> v;for(auto&x:v)need(bool(std::getline(s,x,'\t')),"four fields");need(v[2]=="518404","fixed message length");out.push_back({v[0],(std::filesystem::path(p).parent_path()/v[1]).string(),v[3]});}return out;}
static std::vector<uint8_t> load(const Fixture&f){std::ifstream in(f.path,std::ios::binary);need(bool(in),"message file");std::vector<uint8_t> z{std::istreambuf_iterator<char>(in),{}};std::vector<uint8_t> out(518404);uLongf n=out.size();need(uncompress(out.data(),&n,z.data(),z.size())==Z_OK&&n==out.size(),"message inflate");return out;}
struct Event{bool tile,byte,result;};
struct Sim{
 Model d;std::mt19937 rng;uint64_t cycles=0;bool held=false;uint8_t held_data=0;bool held_last=false;unsigned bytes=0,tiles=0;bool active_key=true;std::vector<uint8_t> message;
#ifdef ROWS_HASH
 bool result_held=false;std::array<uint32_t,8> old_digest{};
#endif
 explicit Sim(unsigned seed):rng(seed){d.clk=0;d.rst=1;d.abort_i=0;d.start_valid=0;d.tile_valid=0;d.frame_id=17;d.key=1;
#ifdef ROWS_HASH
 d.result_ready=0;
#else
 d.data_ready=0;
#endif
 step(false);step(false);d.rst=0;step(false);}
 Event step(bool check=true){need(cycles<200000000,"global watchdog");d.clk=0;d.eval();
  if(check&&!d.rst&&!d.abort_i&&!d.error){
   if(held)need(d.data_valid&&d.data==held_data&&bool(d.data_last)==held_last,"byte changed while stalled");
   if(d.data_valid&&d.data_ready){need(bytes<message.size(),"too many bytes");if(d.data!=message[bytes])throw std::runtime_error("byte="+std::to_string(bytes)+" expected="+std::to_string(message[bytes])+" got="+std::to_string(d.data));need(bool(d.data_last)==(bytes+1==message.size()),"exact byte last");}
#ifdef ROWS_HASH
   if(result_held){need(d.result_valid,"digest valid dropped");for(unsigned i=0;i<8;i++)need(d.digest[i]==old_digest[i],"digest changed under result stall");}
#endif
  }
  Event e{bool(d.tile_valid&&d.tile_ready),bool(d.data_valid&&d.data_ready),false};
#ifdef ROWS_HASH
  e.result=d.result_valid&&d.result_ready;result_held=check&&!d.rst&&!d.abort_i&&!d.error&&d.result_valid&&!d.result_ready;if(result_held)for(unsigned i=0;i<8;i++)old_digest[i]=d.digest[i];
#endif
  held=check&&!d.rst&&!d.abort_i&&!d.error&&d.data_valid&&!d.data_ready;if(held){held_data=d.data;held_last=d.data_last;}
  d.clk=1;d.eval();cycles++;
  if(check){bytes+=e.byte;tiles+=e.tile;}
#ifndef ROWS_HASH
  e.result=d.done;
#endif
  return e;
 }
 void begin(const Fixture&f){need(d.start_ready,"new frame not ready");message=load(f);bytes=tiles=0;held=false;
#ifdef ROWS_HASH
 result_held=false;d.result_ready=0;
#else
 d.data_ready=0;
#endif
 d.tile_valid=0;d.frame_id=17;active_key=(f.name.find("combat")==std::string::npos);d.key=active_key;d.start_valid=1;step();d.start_valid=0;}
 void offer(unsigned ordinal,unsigned mode){unsigned plane=ordinal<5400?0:ordinal<6750?1:2;unsigned index=ordinal-(plane==0?0:plane==1?5400:6750);unsigned width=plane==0?720:360,bw=width/8;unsigned x=(index%bw)*8,y=(index/bw)*8,offset=plane==0?4:plane==1?345604:432004;
  for(unsigned w=0;w<16;w++){uint32_t word=0;for(unsigned b=0;b<4;b++){unsigned p=w*4+b;word|=uint32_t(message[offset+(y+p/8)*width+x+p%8])<<(8*b);}d.tile_pixels[w]=word;}
  d.tile_frame_id=17;d.tile_key=active_key;d.tile_plane=plane;d.tile_index=index;d.tile_last=ordinal==8099;
  if(mode==1&&ordinal==0)d.tile_frame_id=18;
  if(mode==2&&ordinal==0)d.tile_key=!active_key;
  if(mode==3&&ordinal==0)d.tile_plane=1;
  if(mode==4&&ordinal==0)d.tile_index=1;
  if(mode==5&&ordinal==0)d.tile_last=1;
  if(mode==6&&ordinal==1)d.tile_index=0;
  if(mode==7&&ordinal==5400)d.tile_plane=0;
  if(mode==8&&ordinal==8099)d.tile_last=0;
 }
#ifdef ROWS_HASH
 std::string hex(){std::ostringstream s;for(int i=7;i>=0;i--)s<<std::hex<<std::setw(8)<<std::setfill('0')<<d.digest[i];return s.str();}
#endif
 void run(const Fixture&f,bool randomize,unsigned mode=0,bool busy_start=false){uint64_t started=cycles;begin(f);unsigned ordinal=0;bool offering=false,finished=false;uint64_t first_byte=0,first_y=0,last_byte=0,first_result=0;
  while(!finished&&!d.error){need(cycles-started<20000000,"frame watchdog");if(busy_start&&cycles-started<40){need(!d.start_ready,"busy metadata start accepted");d.start_valid=1;d.frame_id=123;d.key=!active_key;}else{d.start_valid=0;d.frame_id=17;d.key=active_key;}if(ordinal<8100&&!offering&&(!randomize||rng()%5!=0)){offer(ordinal,mode);offering=true;}d.tile_valid=offering;
#ifdef ROWS_HASH
   d.result_ready=!randomize||rng()%4!=0;d.clk=0;d.eval();if(d.result_valid){need(mode==0,"invalid frame produced digest");need(hex()==f.hash,"integrated SHA mismatch");if(!first_result)first_result=cycles-started;}
#else
   d.data_ready=!randomize||rng()%4!=0;
#endif
   auto e=step();if(e.tile){ordinal++;offering=false;}if(e.byte){if(bytes==1)first_byte=cycles-started;if(bytes==5)first_y=cycles-started;last_byte=cycles-started;}finished=e.result;
  }
  d.tile_valid=0;
  need(bool(d.error)==(mode!=0),mode?"bad metadata accepted":"unexpected frame error "+std::to_string(d.error_code));
  if(mode)need(!finished,"bad frame finished");else{
   need(bytes==518404&&tiles==8100&&d.accepted_tiles==8100&&d.emitted_bytes==518404&&d.strip_word_writes==64800&&d.strip_word_reads==64800,"exact frame counters");
#ifdef ROWS_HASH
   need(d.hash_bytes==518404&&d.hash_blocks==8101&&d.hash_rounds==518464,"integrated SHA work");
#endif
  }
  std::cout<<"CASE_PASS name="<<f.name<<" mode="<<mode<<" cycles="<<cycles-started<<" bytes="<<bytes<<" tiles="<<tiles<<" first_byte="<<first_byte<<" first_y="<<first_y<<" last_byte="<<last_byte<<" first_result="<<first_result<<" writes="<<d.strip_word_writes<<" reads="<<d.strip_word_reads<<" input_stalls="<<d.input_stall_cycles<<" output_stalls="<<d.output_stall_cycles<<" error="<<unsigned(d.error_code)<<"\n";
  step(false);step(false);
 }
 void controls(const Fixture&f){
  for(unsigned mode=1;mode<=8;mode++)run(f,true,mode);
  d.frame_id=0xffffffff;d.start_valid=1;step(false);d.start_valid=0;need(d.error&&!d.data_valid,"invalid config frame id accepted");step(false);step(false);run(f,true,0,true);
  // Capture ownership: bus changes immediately after accepted tile while8writes run.
  begin(f);offer(0,0);d.tile_valid=1;while(!step().tile){}d.tile_valid=0;for(unsigned w=0;w<16;w++)d.tile_pixels[w]=0xffffffff;
  for(unsigned i=0;i<10;i++)step();need(d.expected_index==1,"captured tile commit");
  d.abort_i=1;for(unsigned i=0;i<5;i++){step(false);need(!d.start_ready,"start ready under abort");}d.abort_i=0;step(false);need(d.start_ready,"abort did not release");run(f,true);
  // Reset clears strip ownership without a RAM clear.
  begin(f);offer(0,0);d.tile_valid=1;step();d.tile_valid=0;step();d.rst=1;step(false);d.rst=0;step(false);run(f,true);
  // Stalled output/cache lease abort, followed by valid retry.
  begin(f);unsigned ordinal=0;bool ready=false;while(!ready){if(ordinal<8100)offer(ordinal,0);d.tile_valid=ordinal<8100;
#ifdef ROWS_HASH
   d.result_ready=0;
#else
   d.data_ready=1;
#endif
   auto e=step();if(e.tile)ordinal++;ready=bytes>80;need(cycles<200000000,"abort setup");}
  d.tile_valid=0;
#ifdef ROWS_HASH
  unsigned waited=0;while(!(d.data_valid&&!d.data_ready)){step();need(++waited<100000,"SHA stall setup");}
#else
  d.data_ready=0;for(unsigned i=0;i<23;i++)step();
#endif
  d.abort_i=1;step(false);d.abort_i=0;step(false);run(f,true);
  std::cout<<"CONTROL_PASS wrong_frame wrong_key wrong_plane wrong_index early_last duplicate plane_boundary missing_last captured_bus_ownership invalid_config busy_start key_zero_and_one held_abort reset provisional_output_abort retry\n";
 }
};
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);try{need(argc>=4,"rows_sim fixtures.tsv seed randomize");unsigned seed=std::stoul(argv[2]);bool randomize=std::stoul(argv[3]);auto fs=fixtures(argv[1]);Sim s(seed);for(auto&f:fs)s.run(f,randomize);s.controls(fs.at(0));std::cout<<"TEST_PASS seed="<<seed<<" randomized="<<randomize<<" full_frames="<<fs.size()<<" full_bytes_exact=1";
#ifdef ROWS_HASH
 std::cout<<" integrated_SHA256=1";
#else
 std::cout<<" integrated_SHA256=0";
#endif
 std::cout<<" physical_display_or_FPS_proven=0\n";return 0;}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
