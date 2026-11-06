#include "Vcu71_sha_pair.h"
#include "verilated.h"
#include <zlib.h>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static void require(bool v,const std::string&s){if(!v)throw std::runtime_error(s);}
struct Fixture{std::string name,path,hex;unsigned size;};
static std::vector<Fixture> load(const std::string&p){std::ifstream f(p);require(bool(f),"fixture TSV");std::vector<Fixture> out;std::string line;while(std::getline(f,line)){std::stringstream s(line);std::array<std::string,4> v;for(auto&x:v)require(bool(std::getline(s,x,'\t')),"four fields");out.push_back({v[0],(std::filesystem::path(p).parent_path()/v[1]).string(),v[3],unsigned(std::stoul(v[2]))});}return out;}
static std::vector<uint8_t> message(const Fixture&f){std::ifstream in(f.path,std::ios::binary);require(bool(in),"open message");std::vector<uint8_t> packed{std::istreambuf_iterator<char>(in),{}};std::vector<uint8_t> data(f.size?f.size:1);uLongf n=data.size();require(uncompress(data.data(),&n,packed.data(),packed.size())==Z_OK&&n==f.size,"zlib message length");data.resize(f.size);return data;}
struct Event{bool input,result;};
struct Sim{
 Vcu71_sha_pair d;std::mt19937 rng;uint64_t cycle=0;bool held=false;std::array<uint32_t,8> held_digest{};
 explicit Sim(unsigned seed):rng(seed){d.clk=0;d.rst=1;d.abort_i=0;d.start_valid=0;d.data_valid=0;d.data=0;d.data_last=0;d.result_ready=0;step();step();d.rst=0;std::cout<<"STARTUP_WORDS reference="<<d.initial_word_reference<<" candidate="<<d.initial_word_candidate<<"\n";require(d.initial_word_reference!=0&&d.initial_word_candidate!=0&&d.initial_word_reference!=d.initial_word_candidate,"randomized private-word startup not established");}
 std::string hex(){std::ostringstream s;for(int i=7;i>=0;i--)s<<std::hex<<std::setw(8)<<std::setfill('0')<<d.digest[i];return s.str();}
 Event step(){require(cycle<100000000,"global control watchdog");d.clk=0;d.eval();if(cycle>0)require(!d.mismatch_any,"public cycle mismatch LOW fields="+std::to_string(d.mismatch_fields));if(held&&!d.abort_i&&!d.rst){require(d.result_valid,"result valid dropped under backpressure");for(unsigned i=0;i<8;i++)require(d.digest[i]==held_digest[i],"digest changed under backpressure");}
  Event e{bool(d.data_valid&&d.data_ready),bool(d.result_valid&&d.result_ready)};held=d.result_valid&&!d.result_ready&&!d.abort_i&&!d.rst;if(held)for(unsigned i=0;i<8;i++)held_digest[i]=d.digest[i];d.clk=1;d.eval();require(!d.mismatch_any,"public cycle mismatch HIGH fields="+std::to_string(d.mismatch_fields));cycle++;return e;}
 void start(unsigned bytes){require(d.start_ready,"start readiness");d.data_valid=0;d.result_ready=0;d.total_bytes=bytes;d.start_valid=1;step();d.start_valid=0;}
 void run(const Fixture&f,bool randomize){auto data=message(f);uint64_t begin=cycle;start(data.size());unsigned pos=0;bool offer=false;uint64_t first=0,last=0,result_first=0,source_bubbles=0;bool seen=false;
  while(true){
   require(cycle-begin<20000000,"watchdog fill="+std::to_string(d.debug_fill_state)+" core="+std::to_string(d.debug_core_state));
   if(pos<data.size()&&!offer&&(!randomize||rng()%4!=0))offer=true;
   d.data_valid=offer;d.data=pos<data.size()?data[pos]:0;d.data_last=pos+1==data.size();d.result_ready=!randomize||rng()%4!=0;
   d.clk=0;d.eval();if(d.data_ready&&!d.data_valid)source_bubbles++;
   if(d.result_valid){require(hex()==f.hex,"digest mismatch name="+f.name+" expected="+f.hex+" got="+hex());if(!seen){seen=true;result_first=cycle-begin;}}
   auto e=step();require(!d.error,"unexpected SHA framing error");if(e.input){if(pos==0)first=cycle-begin;pos++;last=cycle-begin;offer=false;}
   if(e.result){require(pos==data.size(),"result before exact input");break;}
  }
  unsigned blocks=(uint64_t(data.size())+9+63)/64;
  require(d.accepted_bytes==data.size()&&d.compressed_blocks==blocks&&d.round_cycles==blocks*64&&d.padding_bytes==blocks*64-data.size(),"SHA work/count mismatch");
  std::cout<<"CASE_PASS name="<<f.name<<" bytes="<<data.size()<<" cycles="<<cycle-begin<<" first_byte="<<first<<" last_byte="<<last<<" result_first="<<result_first<<" result_accept="<<cycle-begin<<" blocks="<<d.compressed_blocks<<" rounds="<<d.round_cycles<<" padding="<<d.padding_bytes<<" input_stalls="<<d.input_stall_cycles<<" output_stalls="<<d.output_stall_cycles<<" source_bubbles="<<source_bubbles<<"\n";
 }
 void controls(const Fixture&abc){
  // Early, missing and overlong last markers fail without a published result.
  for(unsigned mode=0;mode<3;mode++){
   start(4);for(unsigned pos=0;pos<5&&!d.error;){d.data_valid=1;d.data=uint8_t(pos);d.data_last=mode==0?pos==0:mode==1?false:pos==4;if(step().input)pos++;require(!d.result_valid,"bad framing published");}
   require(d.error&&d.error_code==1&&!d.busy,"bad last was not rejected");d.data_valid=0;run(abc,true);
  }
  start(4);for(unsigned pos=0;pos<3;){d.data_valid=1;d.data=uint8_t(pos);d.data_last=0;if(step().input)pos++;}d.data_valid=0;
  for(unsigned i=0;i<100;i++){step();require(!d.result_valid&&!d.error,"silence incorrectly finalized");}d.abort_i=1;for(unsigned i=0;i<5;i++){step();require(!d.start_ready&&!d.result_valid,"abort readiness/result");}d.abort_i=0;step();run(abc,true);
  start(80);unsigned pos=0;while(d.debug_core_state!=1){d.data_valid=1;d.data=uint8_t(pos);d.data_last=pos==79;if(step().input)pos++;require(pos<=80,"round abort setup");}
  d.abort_i=1;step();d.abort_i=0;d.data_valid=0;step();require(!d.result_valid,"abort rounds leaked");run(abc,true);
  start(80);for(unsigned i=0;i<10;i++){d.data_valid=1;d.data=uint8_t(i);d.data_last=0;step();}d.rst=1;step();d.rst=0;d.data_valid=0;step();require(!d.result_valid,"reset leaked digest");run(abc,true);
  // Hold a valid result, verify all256bits, abort then retry.
  auto data=message(abc);start(data.size());pos=0;d.result_ready=0;
  while(!d.result_valid){d.data_valid=pos<data.size();d.data=pos<data.size()?data[pos]:0;d.data_last=pos+1==data.size();if(step().input)pos++;}
  d.data_valid=0;for(unsigned i=0;i<23;i++){step();require(hex()==abc.hex,"held digest");}d.abort_i=1;step();d.abort_i=0;step();run(abc,true);
  // Accepted start parameters remain fixed while a second start is offered.
  start(data.size());pos=0;d.total_bytes=999;d.start_valid=1;
  while(!d.result_valid){require(!d.start_ready,"start accepted while active");d.data_valid=pos<data.size();d.data=pos<data.size()?data[pos]:0;d.data_last=pos+1==data.size();if(step().input)pos++;}
  require(hex()==abc.hex,"busy start changed transaction");d.start_valid=0;d.data_valid=1;d.data=0xaa;d.data_last=1;
  for(unsigned i=0;i<10;i++){require(!d.data_ready,"extra unaccepted byte consumed");step();}d.data_valid=0;d.result_ready=1;step();run(abc,true);
  // Cancel/reset every compression round, including early lookahead writes,
  // ring wrap boundaries and the final round; valid retry replaces stale data.
  for(unsigned reset_kind=0;reset_kind<2;reset_kind++)for(unsigned offset=0;offset<64;offset++){
   start(64);unsigned pos=0;
   while(d.debug_core_state!=1){d.data_valid=pos<64;d.data=uint8_t(pos*13+offset);d.data_last=pos==63;if(step().input)pos++;}
   d.data_valid=0;for(unsigned n=0;n<offset;n++)step();
   if(reset_kind)d.rst=1;else d.abort_i=1;step();d.rst=0;d.abort_i=0;step();
   require(!d.result_valid&&!d.busy&&d.start_ready,"all-round cancellation failed");run(abc,true);
  }
  std::cout<<"ALL_ROUND_CANCEL_PASS aborts=64 resets=64 public_cycle_compare=1\n";
  std::cout<<"CONTROL_PASS early_last missing_last overlong_last partial_pause_abort held_abort round_abort reset result_stability busy_start extra_unaccepted_byte valid_retry\n";
 }
};
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);try{require(argc>=4,"usage: hash_sim fixtures.tsv seed randomize");unsigned seed=std::stoul(argv[2]);bool randomize=std::stoul(argv[3]);auto fs=load(argv[1]);Sim sim(seed);sim.step();for(const auto&f:fs)sim.run(f,randomize);auto abc=fs.at(1);sim.controls(abc);std::cout<<"TEST_PASS backend=Verilator seed="<<seed<<" randomized="<<randomize<<" fixtures="<<fs.size()<<" full_sha256_checked=1 physical_timing_proven=0\n";return 0;}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
