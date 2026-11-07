#include "Vtile_rowpair_reader.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);}
static uint32_t physical(uint32_t logical){
 uint32_t base=logical<345600?0:logical<432000?345600:432000;
 uint32_t width=logical<345600?720:360;
 uint32_t local=logical-base,y=local/width,x=local%width;
 return base+((y/8)*(width/8)+x/8)*64+(y%8)*8+x%8;
}
static std::string hexbytes(const std::array<uint8_t,16>& bytes){
 std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto b:bytes)out<<std::setw(2)<<static_cast<unsigned>(b);return out.str();
}
static std::array<uint8_t,16> wide_bytes(const VlWide<4>& words){
 std::array<uint8_t,16> data{};for(size_t i=0;i<16;i++)data[i]=static_cast<uint8_t>(words[i/4]>>((i%4)*8));return data;
}
static void set_wide(VlWide<4>& words,const std::array<uint8_t,16>& data){
 for(size_t j=0;j<4;j++){uint32_t v=0;for(size_t k=0;k<4;k++)v|=static_cast<uint32_t>(data[j*4+k])<<(k*8);words[j]=v;}
}
struct Image{std::string name;std::vector<uint8_t> canonical,tiles;};
static std::vector<Image> load_images(const std::string& path){
 std::ifstream in(path);require(in.good(),"missing canonical fixture");std::vector<Image> images;std::string line;
 while(std::getline(in,line)){
  std::istringstream row(line);std::string name,profile,hex;std::getline(row,name,'\t');std::getline(row,profile,'\t');std::getline(row,hex);
  if(profile!="0"||(name!="actual_001"&&name!="actual_006"))continue;
  require(hex.size()==1036800,"canonical fixture extent");Image image{name,{},std::vector<uint8_t>(518400)};
  for(size_t i=0;i<hex.size();i+=2)image.canonical.push_back(static_cast<uint8_t>(std::stoul(hex.substr(i,2),nullptr,16)));
  for(uint32_t i=0;i<518400;i++)image.tiles[physical(i)]=image.canonical[i];
  images.push_back(std::move(image));
 }
 require(images.size()==2&&images[0].name=="actual_001"&&images[1].name=="actual_006","two canonical images/order");return images;
}
static std::vector<uint32_t> load_schedule(const std::string& path){
 std::ifstream in(path);require(in.good(),"missing derived prefill schedule");std::vector<uint32_t> addresses;std::string line;std::vector<bool> seen(32400,false);
 while(std::getline(in,line)){if(line.empty())continue;const auto address=static_cast<uint32_t>(std::stoul(line,nullptr,16));require(address<518400&&address%16==0&&!seen[address/16],"schedule duplicate/range/alignment");seen[address/16]=true;addresses.push_back(address);}
 require(addresses.size()==32400&&std::all_of(seen.begin(),seen.end(),[](bool x){return x;}),"full schedule extent");return addresses;
}
struct Step{bool req=false,phys_req=false,phys_rsp=false,rsp=false;};
struct Bus{uint32_t address,bank,epoch,generation;uint64_t due;bool error,poison;size_t image;};
class Test{
public:
 Vtile_rowpair_reader d;uint64_t cycle=0;uint32_t seed,rng,token=0;bool retain,block_memory=false,error_next=false,poison_next=false;
 std::optional<Bus> bus;std::ofstream log;std::vector<Image> images;size_t image=0;unsigned checks=0;
 Test(uint32_t s,bool retention,const std::string& fixture,const std::string& events):seed(s),rng(s),retain(retention),log(events),images(load_images(fixture)){
  require(log.good(),"event output unavailable");d.clk=0;d.power_on_reset=1;d.reset=0;d.cancel=0;d.start=0;d.finish=0;d.req_valid=0;d.rsp_ready=0;
  d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_addr=0;d.mem_rsp_bank=0;d.mem_rsp_epoch=0;d.mem_rsp_generation=0;d.mem_rsp_error=0;for(size_t i=0;i<4;i++)d.mem_rsp_data[i]=0;
  tick();tick();d.power_on_reset=0;tick();
  log<<"{\"type\":\"config\",\"seed\":"<<seed<<",\"retain\":"<<retain<<",\"data_storage_bytes\":"<<(retain?1472:32)<<",\"service\":\"one_BL8_8payload_plus1to5wait_cycles_seeded_ready_stalls\"}\n";
 }
 uint32_t random(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
 std::string identity()const{
  std::ostringstream out;out<<"\"address\":"<<d.rsp_addr<<",\"bank\":"<<static_cast<unsigned>(d.rsp_bank)<<",\"epoch\":"<<d.rsp_epoch<<",\"generation\":"<<d.rsp_generation<<",\"token\":"<<d.rsp_token;return out.str();
 }
 Step tick(){
  require(cycle<20000000,"finite test watchdog");d.clk=0;d.eval();d.mem_req_ready=!block_memory&&((random()&3U)!=0);
  d.mem_rsp_valid=0;bool poison=false;
  if(bus&&cycle>=bus->due){
   d.mem_rsp_valid=1;d.mem_rsp_addr=bus->address;d.mem_rsp_bank=bus->bank;d.mem_rsp_epoch=bus->epoch;
   d.mem_rsp_generation=bus->generation^(bus->poison?1U:0U);d.mem_rsp_error=bus->error;
   std::array<uint8_t,16> bytes{};for(size_t i=0;i<16;i++)bytes[i]=images[bus->image].tiles[bus->address+i];set_wide(d.mem_rsp_data,bytes);poison=bus->poison;
  }
  d.eval();Step result;
  if(d.start&&d.start_ready)log<<"{\"type\":\"start\",\"cycle\":"<<cycle<<",\"bank\":"<<static_cast<unsigned>(d.start_bank)<<",\"epoch\":"<<d.start_epoch<<",\"generation\":"<<d.start_generation<<",\"image\":\""<<images[image].name<<"\"}\n";
  if(d.finish&&d.state==0&&!d.physical_pending)log<<"{\"type\":\"finish\",\"cycle\":"<<cycle<<"}\n";
  if(d.reset||d.cancel)log<<"{\"type\":\"kill\",\"cycle\":"<<cycle<<",\"reset\":"<<static_cast<unsigned>(d.reset)<<",\"cancel\":"<<static_cast<unsigned>(d.cancel)<<",\"state\":"<<static_cast<unsigned>(d.state)<<",\"pending\":"<<static_cast<unsigned>(d.physical_pending)<<"}\n";
  if(d.req_valid&&d.req_ready){
   result.req=true;log<<"{\"type\":\"req\",\"cycle\":"<<cycle<<",\"address\":"<<d.req_addr<<",\"bank\":"<<static_cast<unsigned>(d.req_bank)<<",\"epoch\":"<<d.req_epoch<<",\"generation\":"<<d.req_generation<<",\"token\":"<<d.req_token<<"}\n";
  }
  if(d.mem_rsp_valid&&poison){
   require(!d.mem_rsp_ready,"wrong generation released accepted burst");log<<"{\"type\":\"wrong_tag_rsp\",\"cycle\":"<<cycle<<",\"address\":"<<d.mem_rsp_addr<<",\"generation\":"<<d.mem_rsp_generation<<",\"ready\":"<<static_cast<unsigned>(d.mem_rsp_ready)<<"}\n";
   bus->poison=false;bus->due=cycle+1;
  }
  if(d.mem_rsp_valid&&d.mem_rsp_ready){
   result.phys_rsp=true;require(bus.has_value(),"physical response without accepted service owner");
   log<<"{\"type\":\"phys_rsp\",\"cycle\":"<<cycle<<",\"address\":"<<d.mem_rsp_addr<<",\"bank\":"<<static_cast<unsigned>(d.mem_rsp_bank)<<",\"epoch\":"<<d.mem_rsp_epoch<<",\"generation\":"<<d.mem_rsp_generation<<",\"error\":"<<static_cast<unsigned>(d.mem_rsp_error)<<",\"data\":\""<<hexbytes(wide_bytes(d.mem_rsp_data))<<"\"}\n";bus.reset();
  }
  if(d.mem_req_valid&&d.mem_req_ready){
   result.phys_req=true;require(!bus,"physical service credit overflow");require(d.mem_req_addr<518400&&d.mem_req_addr%16==0,"physical burst alignment/range");
   bus=Bus{d.mem_req_addr,d.mem_req_bank,d.mem_req_epoch,d.mem_req_generation,cycle+8+1+(random()%5),error_next,poison_next,image};error_next=false;poison_next=false;
   log<<"{\"type\":\"phys_req\",\"cycle\":"<<cycle<<",\"address\":"<<d.mem_req_addr<<",\"bank\":"<<static_cast<unsigned>(d.mem_req_bank)<<",\"epoch\":"<<d.mem_req_epoch<<",\"generation\":"<<d.mem_req_generation<<",\"due\":"<<bus->due<<",\"image\":\""<<images[image].name<<"\"}\n";
  }
  if(d.rsp_valid){
   log<<"{\"type\":\"rsp_offer\",\"cycle\":"<<cycle<<","<<identity()<<",\"error\":"<<static_cast<unsigned>(d.rsp_error)<<",\"ready\":"<<static_cast<unsigned>(d.rsp_ready)<<",\"data\":\""<<hexbytes(wide_bytes(d.rsp_data))<<"\"}\n";
   require(!bus&&!d.physical_pending,"logical response before physical drain");
   if(d.rsp_ready){result.rsp=true;log<<"{\"type\":\"rsp_accept\",\"cycle\":"<<cycle<<","<<identity()<<",\"error\":"<<static_cast<unsigned>(d.rsp_error)<<",\"data\":\""<<hexbytes(wide_bytes(d.rsp_data))<<"\"}\n";}
  }
  d.clk=1;d.eval();cycle++;d.clk=0;d.eval();return result;
 }
 void pass(const std::string& name){checks++;log<<"{\"type\":\"check\",\"name\":\""<<name<<"\",\"status\":\"PASS\",\"cycle\":"<<cycle<<"}\n";}
 void start(size_t which,uint32_t bank,uint32_t epoch,uint32_t generation){
  require(d.start_ready,"start attempted while not drained");image=which;d.start_bank=bank;d.start_epoch=epoch;d.start_generation=generation;d.start=1;tick();d.start=0;
 }
 void stop(){require(d.state==0&&!bus,"finish with pending work");d.finish=1;tick();d.finish=0;require(d.start_ready,"finish failed to release session");}
 void offer(uint32_t address,int bank=-1,uint32_t epoch=0,uint32_t generation=0){
  d.req_addr=address;d.req_bank=bank<0?d.start_bank:static_cast<unsigned>(bank);d.req_epoch=epoch==0?d.start_epoch:epoch;
  d.req_generation=generation==0?d.start_generation:generation;d.req_token=++token;d.req_valid=1;
  for(unsigned n=0;n<1000;n++){if(tick().req){d.req_valid=0;return;}}throw std::runtime_error("logical offer timeout");
 }
 void wait_response(){for(unsigned n=0;n<1000;n++){if(d.rsp_valid)return;tick();}throw std::runtime_error("logical response timeout");}
 std::array<uint8_t,16> response(uint32_t address,unsigned error=0,unsigned hold=0){
  wait_response();const auto data=wide_bytes(d.rsp_data);const auto id=identity();require(d.rsp_error==error,"response error mismatch");
  require(d.rsp_addr==address&&d.rsp_token==token,"response address/token mismatch");
  for(unsigned i=0;i<hold;i++){tick();require(d.rsp_valid&&identity()==id&&wide_bytes(d.rsp_data)==data&&d.rsp_error==error,"held response changed");}
  d.rsp_ready=1;require(tick().rsp,"response not consumed");d.rsp_ready=0;return data;
 }
 void exact(uint32_t address){offer(address);const auto got=response(address,0,random()%3);for(size_t j=0;j<16;j++)require(got[j]==images[image].canonical[address+j],"logical data differs from canonical golden");}
 void cancel_pending(bool warm_reset,bool before_accept){
  start(0,0,100+checks,200+checks);block_memory=before_accept;offer(0);
  if(before_accept){for(unsigned i=0;i<3;i++)tick();require(!bus&&!d.physical_pending,"blocked physical read accepted");}
  else{for(unsigned i=0;i<20&&!bus;i++)tick();require(bus.has_value(),"missing accepted physical read");}
  d.reset=warm_reset;d.cancel=!warm_reset;tick();d.reset=0;d.cancel=0;block_memory=false;
  if(bus){require(!d.start_ready&&!d.req_ready,"warm cancel released pending lease");d.start=1;d.start_bank=1;tick();d.start=0;}
  response(0,4,2);require(d.start_ready&&!bus&&!d.physical_pending,"warm cancellation did not drain");
  pass(std::string(warm_reset?"reset":"cancel")+(before_accept?"_before_physical_accept":"_after_physical_accept"));
 }
 void held_kill(bool successful,bool warm_reset){
  start(0,0,100+checks,200+checks);offer(0);
  if(!successful){d.cancel=1;tick();d.cancel=0;}
  wait_response();const auto data=wide_bytes(d.rsp_data);const auto id=identity();const auto error=d.rsp_error;
  require(error==(successful?0:4),"held kill precondition");
  for(unsigned n=0;n<4;n++){d.reset=warm_reset;d.cancel=!warm_reset;tick();require(d.rsp_valid&&d.rsp_error==error&&data==wide_bytes(d.rsp_data)&&id==identity(),"kill changed offered response");}
  d.reset=0;d.cancel=0;response(0,error);require(d.start_ready,"held kill not drained");pass(std::string(warm_reset?"reset":"cancel")+(successful?"_held_success":"_held_error"));
 }
 void reject(uint32_t address,unsigned error,int bank=-1,bool zero_epoch=false,bool zero_generation=false){
  start(0,0,100+checks,200+checks);const auto before=d.count_physical_requests;
  d.req_addr=address;d.req_bank=bank<0?0:static_cast<unsigned>(bank);d.req_epoch=zero_epoch?0:d.start_epoch;d.req_generation=zero_generation?0:d.start_generation;d.req_token=++token;d.req_valid=1;
  require(tick().req,"reject request not accepted");d.req_valid=0;response(address,error,2);
  require(d.count_physical_requests==before&&d.start_ready,"invalid request emitted physical work");
 }
 void units(){
  start(0,0,10,20);const auto before_finish=d.count_requests;d.req_valid=1;d.req_addr=0;d.req_bank=0;d.req_epoch=10;d.req_generation=20;d.req_token=1;d.finish=1;
  require(!tick().req,"finish failed priority over request");d.finish=0;d.req_valid=0;require(d.start_ready&&d.count_requests==before_finish,"finish/request overlap took ownership");pass("finish_has_priority_over_simultaneous_request");
  for(unsigned bad=0;bad<3;bad++){
   start(0,bad==0?3:0,bad==1?0:1,bad==2?0:1);require(!d.active&&d.session_error==3&&d.start_ready,"invalid start identity accepted");
  }pass("zero_epoch_generation_reserved_bank_start_rejected");
  reject(16,2);reject(8,1);reject(518400,1);reject(0,3,1);reject(0,3,-1,true,false);reject(0,3,-1,false,true);pass("order_alignment_extent_and_lease_reject_without_physical_work");
  for(bool reset:{false,true})for(bool before:{false,true})cancel_pending(reset,before);
  for(bool reset:{false,true})for(bool success:{false,true})held_kill(success,reset);
  start(0,0,300,400);poison_next=true;exact(0);require(!bus,"wrong tag lost physical owner");stop();pass("wrong_generation_response_rejected_then_matching_response_drained");
  start(0,0,301,401);error_next=true;offer(0);response(0,5,2);require(d.start_ready,"memory error did not invalidate lease");pass("physical_error_invalidates_rows_and_retires_owner");
  start(0,0,302,402);for(unsigned a=0;a<1440;a+=16)exact(a);stop();
  start(1,0,303,403);for(unsigned a=0;a<1440;a+=16)exact(a);stop();pass("same_bank_changed_generation_and_content_cannot_hit_stale_rows");
  start(1,1,304,404);exact(345600);exact(432000);exact(0);exact(345616);exact(432016);exact(16);stop();pass("independent_plane_cursors_and_bank_switch");
 }
 void full(const std::vector<uint32_t>& schedule,const std::string& directory,size_t index){
  start(index,static_cast<uint32_t>(index),500+static_cast<uint32_t>(index),600+static_cast<uint32_t>(index));
  const uint64_t first=cycle;const auto physical_before=d.count_physical_requests,hit_before=d.count_row_hits;
  std::vector<uint8_t> output(518400);for(auto address:schedule){offer(address);const auto data=response(address,0,random()%3);for(size_t i=0;i<16;i++){require(data[i]==images[index].canonical[address+i],"full derived prefill response mismatch");output[address+i]=data[i];}}
  const uint64_t last=cycle;require(output==images[index].canonical,"full output not canonical");
  const auto bursts=d.count_physical_requests-physical_before;
  require(bursts==(retain?32400U:64800U),"unexpected full-frame physical burst count");
  const std::string output_name=directory+"/"+images[index].name+".canonical.bin";std::ofstream out(output_name,std::ios::binary);out.write(reinterpret_cast<const char*>(output.data()),static_cast<std::streamsize>(output.size()));require(out.good(),"canonical output save failed");out.close();
  log<<"{\"type\":\"frame\",\"name\":\""<<images[index].name<<"\",\"requests\":32400,\"bytes\":518400,\"physical_reads\":"<<bursts<<",\"row_hits\":"<<d.count_row_hits-hit_before<<",\"first_cycle\":"<<first<<",\"last_cycle\":"<<last<<",\"cycles\":"<<last-first<<",\"output\":\""<<images[index].name<<".canonical.bin\"}\n";
  stop();pass("derived_prefill_full_canonical_"+images[index].name);
 }
};
int main(int argc,char** argv){
 try{
  require(argc==7,"args canonical.tsv schedule.hex events.jsonl output_dir seed retain");const auto seed=static_cast<uint32_t>(std::stoul(argv[5]));const bool retain=std::stoul(argv[6])!=0;
  Verilated::commandArgs(argc,argv);Test test(seed,retain,argv[1],argv[3]);test.units();const auto schedule=load_schedule(argv[2]);test.full(schedule,argv[4],0);test.full(schedule,argv[4],1);
  require(!test.bus&&!test.d.busy&&!test.d.physical_pending&&test.d.count_physical_requests==test.d.count_physical_responses,"terminal owner not drained");
  test.log<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"retain\":"<<retain<<",\"checks\":"<<test.checks<<",\"requests\":"<<test.d.count_requests<<",\"responses\":"<<test.d.count_responses<<",\"physical_requests\":"<<test.d.count_physical_requests<<",\"physical_responses\":"<<test.d.count_physical_responses<<",\"row_hits\":"<<test.d.count_row_hits<<",\"cycles\":"<<test.cycle<<"}\n";
  std::cout<<"ROWPAIR_TEST_PASS seed="<<seed<<" retain="<<retain<<" cycles="<<test.cycle<<" checks="<<test.checks<<"\n";return 0;
 }catch(const std::exception& e){std::cerr<<"ROWPAIR_TEST_FAIL "<<e.what()<<"\n";return 1;}
}
