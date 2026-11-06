#include "Vcu71_ab38_decoder_arithpipe.h"
#include "verilated.h"
#include "Vcu71_ab38_decoder_arithpipe___024root.h"
#include <zlib.h>
#include <array>
#include <cstdint>
#include <fstream>
#include <filesystem>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>

static void demand(bool v,const std::string&why){if(!v)throw std::runtime_error(why);}
static std::vector<uint8_t> bytes(const std::string&p){std::ifstream f(p,std::ios::binary);demand(bool(f),"fixture open: "+p);return {std::istreambuf_iterator<char>(f),{}};}
struct Fixture{std::string name,packet_path,expected_path;unsigned blocks,bw,dispatch;bool invalid;};
static std::vector<Fixture> fixtures(const std::string&path){
 std::ifstream f(path);demand(bool(f),"manifest open");std::vector<Fixture> out;std::string line;
 while(std::getline(f,line)){if(line.empty())continue;std::stringstream s(line);std::array<std::string,7> v;for(auto&x:v)demand(bool(std::getline(s,x,'\t')),"seven TSV fields");v[1]=(std::filesystem::path(path).parent_path()/v[1]).string();if(v[2]!="-")v[2]=(std::filesystem::path(path).parent_path()/v[2]).string();out.push_back({v[0],v[1],v[2],unsigned(std::stoul(v[3])),unsigned(std::stoul(v[4])),unsigned(std::stoul(v[5])),v[6]=="1"});}return out;
}
struct Sim {
 Vcu71_ab38_decoder_arithpipe d;
 std::mt19937 random;
 std::vector<uint8_t> packet;
 std::vector<int16_t> expected;
 uint64_t cycles=0;
 unsigned accepted=0;
 bool pending=false,held=false,request_held=false;
 unsigned held_request_address=0,active_blocks=0;
 unsigned delay=0;uint8_t response=0;
 std::array<uint32_t,32> held_tile{};unsigned held_index=0;bool held_last=false;
 uint64_t state_seen=0;
 explicit Sim(unsigned seed):random(seed){d.clk=0;d.rst=1;d.abort_i=0;d.cfg_valid=0;d.rd_req_ready=0;d.rd_rsp_valid=0;d.rd_rsp_data=0;d.tile_ready=0;step(false);step(false);d.rst=0;}
 void step(bool checks=true,int force_ready=-1){
  d.clk=0;d.rd_req_ready=(random()%5)!=0;d.rd_rsp_valid=pending&&delay==0;d.rd_rsp_data=response;
  d.tile_ready=force_ready<0?((random()%4)!=0):force_ready;d.eval();
  bool req=d.rd_req_valid&&d.rd_req_ready,rsp=d.rd_rsp_valid&&d.rd_rsp_ready;
  bool take=d.tile_valid&&d.tile_ready;uint16_t address=d.rd_req_addr;
  if(checks&&!d.rst&&!d.abort_i){
   if(request_held)demand(d.rd_req_valid&&d.rd_req_addr==held_request_address,"read request changed under backpressure");
   if(held){demand(d.tile_valid,"valid dropped while stalled");demand(d.tile_index==held_index&&bool(d.tile_last)==held_last,"metadata changed while stalled");for(unsigned i=0;i<32;i++)demand(d.tile_coefficients[i]==held_tile[i],"coefficients changed while stalled");}
   if(take){
    demand(d.tile_index==accepted,"tile order/index");
    demand(bool(d.tile_last)==(accepted+1==active_blocks),"tile last marker");
    if(!expected.empty())for(unsigned i=0;i<64;i++){
     int16_t got=int16_t((d.tile_coefficients[i/2]>>(16*(i%2)))&65535u);
     int16_t want=expected.at(accepted*64+i);
     if(got!=want)throw std::runtime_error("tile="+std::to_string(accepted)+" coefficient="+std::to_string(i)+" expected="+std::to_string(want)+" got="+std::to_string(got));
    }
    accepted++;
   }
  }
  request_held=checks&&!d.rst&&!d.abort_i&&d.rd_req_valid&&!d.rd_req_ready;
  if(request_held)held_request_address=d.rd_req_addr;
  held=checks&&!d.rst&&!d.abort_i&&d.tile_valid&&!d.tile_ready;
  if(held){held_index=d.tile_index;held_last=d.tile_last;for(unsigned i=0;i<32;i++)held_tile[i]=d.tile_coefficients[i];}
  if(d.debug_state<64)state_seen|=uint64_t(1)<<d.debug_state;
  d.clk=1;d.eval();cycles++;
  if(d.rst){pending=false;held=false;request_held=false;return;}
  if(rsp)pending=false;
  else if(pending&&delay)delay--;
  if(req){demand(!pending,"more than one outstanding read");demand(address<packet.size(),"read beyond supplied packet");pending=true;response=packet.at(address);delay=random()%8;}
 }
 void load(const Fixture&f){
  demand(!pending&&d.cfg_ready,"previous transaction not drained");packet=bytes(f.packet_path);expected.clear();accepted=0;held=false;request_held=false;active_blocks=f.blocks;
  if(f.expected_path!="-"){
   auto packed=bytes(f.expected_path);std::vector<uint8_t> plain(f.blocks*128);uLongf size=plain.size();demand(uncompress(plain.data(),&size,packed.data(),packed.size())==Z_OK&&size==plain.size(),"coefficient decompression/length");
   expected.resize(f.blocks*64);for(unsigned i=0;i<expected.size();i++)expected[i]=int16_t(unsigned(plain[2*i])|(unsigned(plain[2*i+1])<<8));
  }
  d.cfg_dispatch=f.dispatch;d.cfg_packet_bytes=packet.size();d.cfg_blocks=f.blocks;d.cfg_blocks_w=f.bw;d.cfg_valid=1;step();d.cfg_valid=0;
 }
 uint64_t run(const Fixture&f){
  uint64_t start=cycles;load(f);
  while(!d.done&&!d.error){demand(cycles-start<20000000,"watchdog phase="+std::to_string(d.debug_state));step();}
  demand(bool(d.error)==f.invalid,f.invalid?"malformed packet accepted":"unexpected error code "+std::to_string(d.error_code));
  if(f.invalid)demand(!d.done,"invalid packet finished");else demand(d.done&&accepted==f.blocks,"missing complete tiles");
  demand(!pending,"completion left pending read");
  return cycles-start;
 }
 void arithmetic_micro_abort_checks(const Fixture&good){
  for(unsigned target:std::array<unsigned,4>{43,44,45,46}){
   load(good);unsigned count=0;
   while(d.debug_state!=target){step();demand(++count<2000000,"arithmetic microstate not reached");demand(!d.done&&!d.error,"fixture finished before microstate");}
   std::array<uint8_t,352> before{};
   for(unsigned i=0;i<352;i++)before[i]=d.rootp->cu71_ab38_decoder_arithpipe__DOT__probabilities[i];
   unsigned decisions=d.decoded_decisions;d.abort_i=1;step(false);
   for(unsigned i=0;i<352;i++)demand(before[i]==d.rootp->cu71_ab38_decoder_arithpipe__DOT__probabilities[i],"probability write on arithmetic abort");
   demand(d.decoded_decisions==decisions,"aborted arithmetic decision committed");
   for(unsigned n=0;n<3;n++){step(false);demand(!d.cfg_ready,"held abort admitted config");}
   d.abort_i=0;step(false);held=false;request_held=false;
   demand(d.cfg_ready&&!d.busy&&!d.done&&!d.tile_valid&&!pending,"arithmetic abort did not quiesce");
   run(good);
  }
  std::cout<<"ARITHMETIC_MICRO_ABORT_PASS appended_states=4 probability_writes_on_abort=0 valid_retry=4\n";
 }
 void abort_checks(const Fixture&good){
  load(good);unsigned n=0;while(!pending){step();demand(++n<1000,"abort pending setup");}
  d.abort_i=1;step(false);d.abort_i=0;held=false;
  n=0;while(!d.cfg_ready){step(false);demand(++n<1000,"abort drain watchdog");}
  demand(!d.done&&!pending,"abort published or failed to drain");run(good);
  // Abort exactly when the outstanding response is accepted.
  load(good);n=0;while(!(pending&&delay==0&&d.rd_rsp_ready)){step(false);demand(++n<2000,"coincident response setup");}
  d.abort_i=1;step(false);for(unsigned i=0;i<4;i++){demand(!d.cfg_ready,"config ready during held abort");step(false);}d.abort_i=0;step(false);
  demand(d.cfg_ready&&!pending&&!d.done,"coincident response abort failed");run(good);
  // Keep abort asserted across a delayed response's drain.
  load(good);n=0;while(!pending){step(false);demand(++n<2000,"held abort setup");}delay=5;d.abort_i=1;
  for(unsigned i=0;i<12;i++)step(false);d.abort_i=0;step(false);
  demand(d.cfg_ready&&!pending&&!d.done,"held abort drain failed");run(good);
  // A config offered while busy cannot replace the latched transaction.
  load(good);d.cfg_valid=1;d.cfg_dispatch=4;d.cfg_blocks=1;
  for(unsigned i=0;i<40;i++){demand(!d.cfg_ready,"busy config accepted");step();}
  d.cfg_valid=0;d.cfg_blocks=good.blocks;d.cfg_dispatch=good.dispatch;
  while(!d.done&&!d.error){step();demand(++n<2000000,"busy config watchdog");}
  demand(!d.error&&accepted==good.blocks,"busy config changed transaction");
  load(good);n=0;while(!d.tile_valid){step(true,0);demand(++n<2000000,"stalled-output setup watchdog");}
  for(unsigned i=0;i<23;i++)step(true,0);
  d.abort_i=1;step(false,0);d.abort_i=0;held=false;step(false);
  demand(d.cfg_ready&&!d.tile_valid&&!d.done,"abort leaked output");run(good);
  load(good);for(unsigned i=0;i<70;i++)step(false);d.rst=1;step(false);step(false);d.rst=0;step(false);
  demand(d.cfg_ready&&!d.tile_valid&&!d.done,"reset leaked output");run(good);
 }
};
int main(int argc,char**argv){
 Verilated::commandArgs(argc,argv);
 try{
  demand(argc>=3,"usage: entropy_sim fixtures.tsv seed [limit] [--abort-tests]");unsigned seed=std::stoul(argv[2]);auto fs=fixtures(argv[1]);unsigned limit=argc>=4?std::stoul(argv[3]):fs.size();limit=std::min(limit,unsigned(fs.size()));
  Sim sim(seed);sim.step(false);uint64_t total=0,minimum=UINT64_MAX,maximum=0,decisions=0,renorm=0,reads=0,stalls=0;unsigned good=0,bad=0;
  for(unsigned i=0;i<limit;i++){
   uint64_t elapsed=sim.run(fs[i]);total+=elapsed;minimum=std::min(minimum,elapsed);maximum=std::max(maximum,elapsed);good+=!fs[i].invalid;bad+=fs[i].invalid;
   decisions+=sim.d.decoded_decisions;renorm+=sim.d.renormalizations;reads+=sim.d.memory_reads;stalls+=sim.d.output_stall_cycles;
   std::cout<<"CASE_PASS name="<<fs[i].name<<" seed="<<seed<<" cycles="<<elapsed<<" tiles="<<sim.accepted<<" error="<<unsigned(sim.d.error_code)<<" decisions="<<sim.d.decoded_decisions<<" renorm="<<sim.d.renormalizations<<" reads="<<sim.d.memory_reads<<" stalls="<<sim.d.output_stall_cycles<<"\n";
  }
  if(argc>=5&&std::string(argv[4])=="--abort-tests"){auto p=std::find_if(fs.begin(),fs.end(),[](const Fixture&f){return !f.invalid;});demand(p!=fs.end(),"abort fixture");sim.abort_checks(*p);sim.arithmetic_micro_abort_checks(*p);std::cout<<"ABORT_RESET_PASS seed="<<seed<<" pending-read coincident-response held-abort busy-config stalled-output reset then valid retry\n";}
  std::cout<<"TEST_PASS backend=Verilator seed="<<seed<<" cases="<<limit<<" valid="<<good<<" rejected="<<bad<<" cycles="<<total<<" minimum="<<minimum<<" maximum="<<maximum<<" decisions="<<decisions<<" renorm="<<renorm<<" external_reads="<<reads<<" output_stalls="<<stalls<<" state_seen="<<sim.state_seen<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
