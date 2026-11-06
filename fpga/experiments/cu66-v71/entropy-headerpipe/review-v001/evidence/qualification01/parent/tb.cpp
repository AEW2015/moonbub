#include "Vcu71_ab38_decoder_arithpipe_v4.h"
#include "verilated.h"
#include "Vcu71_ab38_decoder_arithpipe_v4___024root.h"
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
 Vcu71_ab38_decoder_arithpipe_v4 d;
 std::mt19937 random;
 std::vector<uint8_t> packet;
 std::vector<int16_t> expected;
 uint64_t cycles=0;
 unsigned accepted=0;uint32_t tile_crc=0;
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
    for(unsigned c=0;c<64;c++){uint16_t word=(d.tile_coefficients[c/2]>>(16*(c%2)))&65535u;uint8_t bytes2[2]={uint8_t(word),uint8_t(word>>8)};tile_crc=crc32(tile_crc,bytes2,2);}
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
  demand(!pending&&d.cfg_ready,"previous transaction not drained");packet=bytes(f.packet_path);expected.clear();accepted=0;tile_crc=crc32(0L,Z_NULL,0);held=false;request_held=false;active_blocks=f.blocks;
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
 std::array<uint8_t,352> probs()const {std::array<uint8_t,352>x{};for(unsigned i=0;i<352;i++)x[i]=d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__probabilities[i];return x;}
 std::array<uint32_t,32> tile_words()const {std::array<uint32_t,32>x{};for(unsigned i=0;i<32;i++)x[i]=d.tile_coefficients[i];return x;}
 uint64_t run_relaxed(const Fixture&f){
  auto before=probs();auto old_tile=tile_words();uint64_t start=cycles;load(f);
  while(!d.done&&!d.error){demand(cycles-start<20000000,"negative watchdog phase="+std::to_string(d.debug_state));step();}
  demand(bool(d.done)!=bool(d.error),"completion/error exclusivity");demand(!pending,"negative left pending read");
  if(!d.error)demand(accepted==f.blocks,"incomplete accepted malformed/control");
  if(d.error_code>=2&&d.error_code<=4){demand(probs()==before,"probability write before header validation");demand(tile_words()==old_tile,"coefficient payload write before header validation");demand(accepted==0&&d.decoded_decisions==0&&d.renormalizations==0&&!d.tile_valid,"header rejection performed coefficient/arithmetic work");demand(d.memory_reads==packet.size(),"header reject changed CRC read coverage");}
  return cycles-start;
 }
#if defined(CANDIDATE)
 std::array<uint32_t,6> private_header()const {return {d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__header_pair01,d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__header_pair23,d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__header_total,d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__header_prefix1,d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__header_prefix2,d.rootp->cu71_ab38_decoder_arithpipe_v4__DOT__header_prefix3};}
 void new_state_resets(const Fixture&a,const Fixture&b){
  run(b);unsigned number=0;
  for(unsigned state:std::array<unsigned,2>{54,55}){
   const auto&setup=number?a:b;const auto&retry=number?b:a;load(setup);unsigned watchdog=0;
   while(d.debug_state!=state&&!d.done&&!d.error){step();demand(++watchdog<2000000,"new reset-state reach watchdog");}
   demand(d.debug_state==state,"new reset-state not reached");demand(!pending&&!d.rd_req_valid&&!d.tile_valid&&accepted==0&&d.decoded_decisions==0&&d.renormalizations==0,"new header state performed work before validation");
   auto before=probs();auto private_before=private_header();d.rst=1;d.abort_i=1;d.cfg_valid=1;
   for(unsigned i=0;i<2;i++){
    step(false);demand(d.debug_state==0&&!d.busy&&!d.done&&!d.error&&!d.aborted&&!d.tile_valid&&!d.rd_req_valid&&!pending,"direct rst did not dominate abort/config");
    demand(d.decoded_decisions==0&&d.renormalizations==0&&d.memory_reads==0&&d.output_stall_cycles==0,"reset counters mismatch");
    demand(probs()==before,"direct reset changed unreset probability RAM");demand(private_header()==private_before,"new private payload incorrectly reset");
   }
   d.rst=0;d.abort_i=0;d.cfg_valid=0;step(false);demand(d.cfg_ready&&!d.busy&&!d.done&&!d.tile_valid&&!pending,"reset quiescence");
   run(retry);std::cout<<"HEADER_DIRECT_RESET_PASS state="<<state<<" probability_retained=352 private_payload_retained=6 reset_dominates_abort_config=1 valid_golden_retry=1\n";number++;
  }
 }
#endif
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
  demand(argc>=3,"usage header_review fixtures.tsv seed");unsigned seed=std::stoul(argv[2]);Verilated::randSeed(seed);Verilated::randReset(2);auto fs=fixtures(argv[1]);demand(fs.size()>2,"fixtures/control count");
  Sim sim(seed);sim.step(false);unsigned count=0,retries=0;
  for(const auto&f:fs){uint64_t elapsed=sim.run_relaxed(f);std::cout<<"DIFF name="<<f.name<<" error="<<unsigned(sim.d.error_code)<<" done="<<unsigned(sim.d.done)<<" tiles="<<sim.accepted<<" tile_crc="<<sim.tile_crc<<" decisions="<<sim.d.decoded_decisions<<" renorm="<<sim.d.renormalizations<<" reads="<<sim.d.memory_reads<<" cycles="<<elapsed<<"\n";count++;
   if(count>2){sim.run(fs[1]);retries++;}
  }
#if defined(CANDIDATE)
  sim.new_state_resets(fs[0],fs[1]);
#endif
  std::cout<<"HEADER_REVIEW_PASS cases="<<count<<" valid_golden_retries="<<retries<<" randomized_probability_initialization=1 four_state_X_equivalence=0\n";return 0;
 }catch(const std::exception&e){std::cerr<<"HEADER_REVIEW_FAIL "<<e.what()<<"\n";return 1;}
}
