#include "Vcanonical_rgb565_timed.h"
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
using Bytes=std::vector<uint8_t>;
static void need(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}
static Bytes unhex(const std::string&s){need(s.size()%2==0,"hex extent");Bytes b;for(size_t i=0;i<s.size();i+=2)b.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));return b;}
static uint32_t physical(uint32_t logical){const uint32_t base=logical<345600?0:logical<432000?345600:432000,width=logical<345600?720:360;const auto y=(logical-base)/width,x=(logical-base)%width;return base+((y/8)*(width/8)+x/8)*64+(y%8)*8+x%8;}
static std::string hexwide(const VlWide<4>& w){std::ostringstream s;s<<std::hex<<std::setfill('0');for(unsigned i=0;i<16;i++)s<<std::setw(2)<<((w[i/4]>>((i%4)*8))&255U);return s.str();}
static uint64_t hashbyte(uint64_t h,uint8_t b){return (h^b)*1099511628211ULL;}
struct Image{std::string name;Bytes canonical,tiles,rgb;};
static std::vector<Image> images(const std::string& canonical,const std::string& rgb){
 std::map<std::string,Bytes> golden;std::ifstream gf(rgb);need(bool(gf),"RGB golden file");std::string line;
 while(std::getline(gf,line)){const auto t=line.find('\t');need(t!=std::string::npos,"RGB golden row");golden[line.substr(0,t)]=unhex(line.substr(t+1));}
 std::ifstream cf(canonical);need(bool(cf),"canonical actual file");std::vector<Image> out;
 while(std::getline(cf,line)){std::istringstream row(line);std::string id,profile,hx;std::getline(row,id,'\t');std::getline(row,profile,'\t');std::getline(row,hx);
  if(profile!="0"||(id!="actual_001"&&id!="actual_006"))continue;
  Image image{id,unhex(hx),Bytes(518400),golden.at(id)};need(image.canonical.size()==518400&&image.rgb.size()==691200,"source image extent");
  for(uint32_t i=0;i<518400;i++)image.tiles[physical(i)]=image.canonical[i];
  out.push_back(std::move(image));
 }
 need(out.size()==2&&out[0].name=="actual_001"&&out[1].name=="actual_006","source image identity/order");return out;
}
template<size_t N> static std::string histogram(const std::array<uint64_t,N>& values){std::ostringstream s;s<<"[";for(size_t i=0;i<N;i++){if(i)s<<",";s<<values[i];}s<<"]";return s.str();}
struct ControllerOwner{uint32_t address;unsigned beats;};
struct Bus{uint32_t address,bank,epoch,generation;uint64_t due;size_t image;bool poison,error;};
struct Line{uint32_t address,epoch,token;};
struct Pixel{uint32_t address,epoch,word;bool operator==(const Pixel&o)const{return address==o.address&&epoch==o.epoch&&word==o.word;}};
class Bench{
public:
 Vcanonical_rgb565_timed d;uint32_t seed,rng;bool burst,retain,blocked=false,hold_pixel=false,poison_next=false,error_next=false,checking=false;size_t selected=0;uint64_t cycle=0,start_cycle=0,first_pixel=0,last_pixel=0;
 uint64_t pixels=0,lines=0,line_acks=0,physical_reads=0,physical_acks=0,held_pixels=0,ready_stalls=0;uint32_t expected_epoch=0,expected_generation=0,expected_bank=0;unsigned checks=0;
 std::array<uint64_t,16> state_hist{};std::array<uint64_t,4> adapter_hist{};std::array<uint64_t,8> reader_hist{};
 uint64_t reader_pending_cycles=0,adapter_pending_cycles=0,controller_busy_cycles=0,bridge_pending_cycles=0;
 std::optional<ControllerOwner> controller_owner;
 std::optional<Line> byte_owner;
 std::vector<Image> source;std::ofstream log;std::optional<Bus> bus;std::optional<Line> line;std::optional<Pixel> held;Bytes actual;uint64_t row_hash=1469598103934665603ULL,row_first=0;
 Bench(uint32_t s,bool b,bool r,const std::string& c,const std::string& rgb,const std::string& events):seed(s),rng(s),burst(b),retain(r),source(images(c,rgb)),log(events){
  need(bool(log),"event output");d.clk=0;d.power_on_reset=1;d.reset=0;d.start=0;d.cancel=0;d.out_ready=0;
  tick();tick();d.power_on_reset=0;tick();for(unsigned i=0;i<1000&&!d.controller_ready;i++)tick();need(d.controller_ready,"controller cold init");log<<"{\"type\":\"config\",\"seed\":"<<seed<<",\"retain\":"<<retain<<",\"service\":\"ACTUAL_CONTROLLER_TIMED_SDRAM_PINS\"}\n";
 }
 uint32_t random(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
 void tick(){
  need(cycle<45000000,"finite timed converter watchdog");d.clk=0;d.eval();d.out_ready=!hold_pixel&&(random()%5!=0);
  d.eval();const bool kill=d.reset||d.cancel;Pixel now{d.out_addr,d.out_epoch,d.out_word};
  if(held&&!kill)need(d.out_valid&&now==*held,"RGB pixel changed under backpressure");
  held=d.out_valid&&!d.out_ready&&!kill?std::optional<Pixel>(now):std::nullopt;
  if(checking){need(d.state<state_hist.size()&&d.adapter_state<adapter_hist.size()&&d.reader_state<reader_hist.size(),"state histogram range");state_hist[d.state]++;adapter_hist[d.adapter_state]++;reader_hist[d.reader_state]++;reader_pending_cycles+=d.reader_pending;adapter_pending_cycles+=d.adapter_pending;controller_busy_cycles+=!d.controller_idle;bridge_pending_cycles+=d.bridge_pending;}
  const uint64_t posedge_time=Verilated::time()+5000;
  if(d.controller_valid&&d.controller_ready){need(!controller_owner,"timed controller ownership overlap");controller_owner=ControllerOwner{d.controller_addr,0};log<<"{\"type\":\"controller_req\",\"cycle\":"<<cycle<<",\"time_ps\":"<<posedge_time<<",\"write\":0,\"address\":"<<d.controller_addr<<",\"data\":0}\n";}
  if(d.controller_read_valid){need(controller_owner.has_value(),"controller beat without owner");controller_owner->beats++;log<<"{\"type\":\"controller_read\",\"cycle\":"<<cycle<<",\"time_ps\":"<<posedge_time<<",\"data\":"<<d.controller_read_data<<"}\n";}
  if(controller_owner&&controller_owner->beats==8&&d.controller_idle){log<<"{\"type\":\"controller_done\",\"cycle\":"<<cycle<<",\"time_ps\":"<<posedge_time<<",\"write\":0,\"address\":"<<controller_owner->address<<",\"data\":0}\n";controller_owner.reset();}
  if(d.bridge_state==3)log<<"{\"type\":\"bridge_fence\",\"cycle\":"<<cycle<<",\"time_ps\":"<<posedge_time<<",\"ctrl_idle\":"<<unsigned(d.controller_idle)<<",\"beats\":"<<unsigned(d.bridge_beats)<<",\"pending\":"<<unsigned(d.bridge_pending)<<"}\n";
  if(d.start&&d.start_ready)log<<"{\"type\":\"start\",\"cycle\":"<<cycle<<",\"bank\":"<<unsigned(d.start_bank)<<",\"epoch\":"<<d.start_epoch<<",\"generation\":"<<d.start_generation<<",\"image\":\""<<source[selected].name<<"\"}\n";
  if(kill)log<<"{\"type\":\"kill\",\"cycle\":"<<cycle<<",\"reset\":"<<unsigned(d.reset)<<",\"cancel\":"<<unsigned(d.cancel)<<",\"physical_pending\":"<<unsigned(d.reader_pending)<<",\"line_pending\":"<<unsigned(d.adapter_pending)<<"}\n";
  if(d.direct_consume){
   need(burst&&checking&&!kill&&!byte_owner&&!d.byte_req_valid&&!d.adapter_pending&&!d.adapter_byte_pending&&!d.byte_rsp_valid&&(d.state==2||d.state==4),"direct hit overlaps a lease or invalid state");
   need(d.direct_epoch==expected_epoch&&d.direct_addr<518400&&d.direct_data==source[selected].canonical[d.direct_addr],"direct hit identity/data");
   log<<"{\"type\":\"direct_byte\",\"cycle\":"<<cycle<<",\"address\":"<<d.direct_addr<<",\"epoch\":"<<d.direct_epoch<<",\"data\":"<<unsigned(d.direct_data)<<"}\n";
  }
  if(d.byte_req_valid&&d.byte_req_ready){
   need(!byte_owner,"external byte owner overlap");byte_owner=Line{d.byte_req_addr,d.byte_req_epoch,0};
   log<<"{\"type\":\"byte_req\",\"cycle\":"<<cycle<<",\"address\":"<<d.byte_req_addr<<",\"epoch\":"<<d.byte_req_epoch<<"}\n";
  }
  if(d.byte_rsp_valid&&d.byte_rsp_ready){
   need(byte_owner.has_value(),"byte response without owner");
   log<<"{\"type\":\"byte_rsp\",\"cycle\":"<<cycle<<",\"address\":"<<byte_owner->address<<",\"epoch\":"<<d.byte_rsp_epoch<<",\"data\":"<<unsigned(d.byte_rsp_data)<<",\"error\":"<<unsigned(d.byte_rsp_error)<<"}\n";
   byte_owner.reset();
  }
  if(d.line_req_valid&&d.line_req_ready){
   need(checking&&!line,"joined logical line owner overwritten");need(d.line_req_addr%16==0&&d.line_req_addr<518400&&d.line_req_epoch==expected_epoch,"joined logical request identity");
   line=Line{d.line_req_addr,d.line_req_epoch,d.line_req_token};need(d.line_req_token==lines,"joined token order");lines++;
   log<<"{\"type\":\"line_req\",\"cycle\":"<<cycle<<",\"address\":"<<line->address<<",\"epoch\":"<<line->epoch<<",\"token\":"<<line->token<<"}\n";
  }
  if(d.mem_rsp_valid&&bus&&bus->poison){need(!d.mem_rsp_ready,"wrong generation consumed physical owner");log<<"{\"type\":\"wrong_tag\",\"cycle\":"<<cycle<<",\"address\":"<<bus->address<<",\"generation\":"<<d.mem_rsp_generation<<",\"ready\":"<<unsigned(d.mem_rsp_ready)<<"}\n";bus->poison=false;bus->due=cycle+1;}
  else if(d.mem_rsp_valid&&d.mem_rsp_ready){
   need(bus.has_value(),"unsolicited physical response");log<<"{\"type\":\"phys_rsp\",\"cycle\":"<<cycle<<",\"address\":"<<d.mem_rsp_addr<<",\"bank\":"<<unsigned(d.mem_rsp_bank)<<",\"epoch\":"<<d.mem_rsp_epoch<<",\"generation\":"<<d.mem_rsp_generation<<",\"error\":"<<unsigned(d.mem_rsp_error)<<",\"data\":\""<<hexwide(d.mem_rsp_data)<<"\"}\n";bus.reset();physical_acks++;
  }
  if(d.mem_req_valid&&d.mem_req_ready){
   need(checking&&!bus,"physical request owner overwritten");need(d.mem_req_bank==expected_bank&&d.mem_req_epoch==expected_epoch&&d.mem_req_generation==expected_generation,"physical lease changed");need(d.mem_req_addr%16==0&&d.mem_req_addr<=518384,"physical tile burst bounds");
   bus=Bus{d.mem_req_addr,d.mem_req_bank,d.mem_req_epoch,d.mem_req_generation,cycle,selected,false,false};poison_next=false;error_next=false;physical_reads++;
   log<<"{\"type\":\"phys_req\",\"cycle\":"<<cycle<<",\"address\":"<<bus->address<<",\"bank\":"<<bus->bank<<",\"epoch\":"<<bus->epoch<<",\"generation\":"<<bus->generation<<",\"due\":"<<bus->due<<"}\n";
  }
  if(d.line_rsp_valid&&d.line_rsp_ready){
   need(line.has_value()&&d.line_rsp_addr==line->address&&d.line_rsp_epoch==line->epoch&&d.line_rsp_token==line->token,"joined logical ACK identity");need(!bus,"logical ACK before physical owner drained");
   log<<"{\"type\":\"line_rsp\",\"cycle\":"<<cycle<<",\"address\":"<<d.line_rsp_addr<<",\"epoch\":"<<d.line_rsp_epoch<<",\"bank\":"<<unsigned(d.line_rsp_bank)<<",\"generation\":"<<d.line_rsp_generation<<",\"token\":"<<d.line_rsp_token<<",\"error\":"<<unsigned(d.line_rsp_error)<<",\"data\":\""<<hexwide(d.line_rsp_data)<<"\"}\n";
   if(!kill&&d.line_rsp_error==0)for(unsigned i=0;i<16;i++)need(uint8_t(d.line_rsp_data[i/4]>>((i%4)*8))==source[selected].canonical[d.line_rsp_addr+i],"joined canonical response data");
   line.reset();line_acks++;
  }
  if(d.out_valid&&d.out_ready){
   need(checking&&!kill&&pixels<345600,"RGB output outside owned conversion");need(d.out_epoch==expected_epoch&&d.out_addr==pixels,"RGB output address/epoch");
   const uint16_t expected=uint16_t(source[selected].rgb[2*pixels])|uint16_t(source[selected].rgb[2*pixels+1]<<8);need(d.out_word==expected,"actual joined RGB differs from golden pixel "+std::to_string(pixels));
   if(pixels==0)first_pixel=cycle;
   if(pixels%720==0)row_first=cycle;
   last_pixel=cycle;actual.push_back(uint8_t(d.out_word));actual.push_back(uint8_t(d.out_word>>8));
   row_hash=hashbyte(hashbyte(row_hash,uint8_t(d.out_word)),uint8_t(d.out_word>>8));pixels++;
   if(pixels%720==0){log<<"{\"type\":\"pixel_row\",\"row\":"<<pixels/720-1<<",\"pixels\":720,\"epoch\":"<<expected_epoch<<",\"first_cycle\":"<<row_first<<",\"last_cycle\":"<<cycle<<",\"hash_fnv64\":"<<row_hash<<"}\n";row_hash=1469598103934665603ULL;}
  }
  if(hold_pixel&&d.out_valid)log<<"{\"type\":\"pixel_hold\",\"cycle\":"<<cycle<<",\"address\":"<<d.out_addr<<",\"epoch\":"<<d.out_epoch<<",\"word\":"<<d.out_word<<",\"ready\":"<<unsigned(d.out_ready)<<"}\n";
  held_pixels+=d.out_valid&&!d.out_ready;ready_stalls+=d.mem_req_valid&&!d.mem_req_ready;
  advance(Verilated::time()+5000);d.clk=1;d.eval();advance(Verilated::time()+5000);cycle++;d.clk=0;d.eval();
 }
 void advance(uint64_t target){
  unsigned events=0;
  while(d.eventsPending()&&d.nextTimeSlot()<=target){need(events++<1000,"timed event loop watchdog");const auto next=d.nextTimeSlot();need(next>=Verilated::time(),"time reversed");Verilated::timeInc(next-Verilated::time());d.eval();}
  if(target>Verilated::time()){Verilated::timeInc(target-Verilated::time());d.eval();}
 }
 void pass(const std::string& n){checks++;log<<"{\"type\":\"check\",\"name\":\""<<n<<"\",\"status\":\"PASS\",\"cycle\":"<<cycle<<"}\n";}
 void begin(size_t image,unsigned bank,unsigned epoch,unsigned generation){
  need(d.start_ready&&!bus&&!line,"begin before complete closure");selected=image;expected_bank=bank;expected_epoch=epoch;expected_generation=generation;
  state_hist.fill(0);adapter_hist.fill(0);reader_hist.fill(0);reader_pending_cycles=adapter_pending_cycles=controller_busy_cycles=bridge_pending_cycles=0;
  pixels=lines=line_acks=physical_reads=physical_acks=held_pixels=ready_stalls=0;first_pixel=last_pixel=0;actual.clear();row_hash=1469598103934665603ULL;checking=true;
  d.start_bank=bank;d.start_epoch=epoch;d.start_generation=generation;d.start=1;start_cycle=cycle;tick();d.start=0;
  need(d.busy&&!d.error&&!d.done&&d.lease_bank==bank&&d.lease_epoch==epoch&&d.lease_generation==generation,"joined accepted start");
  d.start_bank=3;d.start_epoch=epoch^0x80000000U;d.start_generation=generation^0x80000000U;
 }
 void drain(){for(unsigned i=0;i<1000&&!d.start_ready;i++)tick();need(d.start_ready&&!d.busy&&!bus&&!line&&!d.out_valid&&!d.done,"cancel failed full closure");checking=false;held.reset();}
 void stop(bool warm){d.reset=warm;d.cancel=!warm;tick();d.reset=0;d.cancel=0;held.reset();drain();}
 void until_pending(){for(unsigned i=0;i<1000&&!bus;i++)tick();need(bus.has_value(),"no physical pending probe");}
 void units(){
  for(bool warm:{false,true}){
   begin(0,0,100+checks,200+checks);until_pending();stop(warm);pass(warm?"timed_reset_unissued_bridge_request_drains":"timed_cancel_unissued_bridge_request_drains");
   begin(0,0,110+checks,210+checks);const auto before_commands=d.bridge_commands,before_beats=d.bridge_count_beats;
   until_pending();for(unsigned i=0;i<1000&&(!controller_owner||controller_owner->beats<3);i++)tick();
   need(controller_owner&&controller_owner->beats>=3&&controller_owner->beats<8&&d.bridge_pending,"issued mid-BL8 cancellation probe");
   stop(warm);need(!controller_owner&&!d.bridge_pending&&d.bridge_commands-before_commands==1&&d.bridge_count_beats-before_beats==8,"issued cancel/reset did not drain all eight controller captures");
   pass(warm?"timed_reset_after_three_controller_beats_drains_eight":"timed_cancel_after_three_controller_beats_drains_eight");
  }
  begin(0,0,303,403);hold_pixel=true;for(unsigned i=0;i<100000&&!d.out_valid;i++)tick();need(d.out_valid,"timed held RGB probe");for(unsigned i=0;i<8;i++)tick();stop(false);hold_pixel=false;pass("timed_held_pixel_then_cancel");
 }

 void full(size_t image,const std::string& directory){
  begin(image,unsigned(image),500+unsigned(image),600+unsigned(image));for(unsigned i=0;i<6500000&&!d.done;i++)tick();need(d.done&&!d.busy&&!bus&&!line&&d.start_ready&&!d.error,"full joined converter completion");
  need(pixels==345600&&actual==source[image].rgb,"full actual RGB output mismatch");need(lines==line_acks&&lines==32400&&physical_reads==physical_acks&&physical_reads==(retain?32400U:64800U),"joined frame request closure/count");
  need(d.count_reads==(burst?32400U:518400U)&&d.count_responses==d.count_reads&&d.count_direct_consumes==(burst?486000U:0U)&&d.count_canonical_consumed==518400&&d.count_byte_requests==d.count_reads&&d.count_hits==(burst?0U:486000U)&&d.count_misses==32400&&d.count_pixels==345600&&d.count_row_fills==240&&d.count_lookups==345600,"actual converter internal counts");
  const std::string name=source[image].name+".rgb565.bin";std::ofstream out(directory+"/"+name,std::ios::binary);out.write(reinterpret_cast<const char*>(actual.data()),std::streamsize(actual.size()));need(bool(out),"RGB output save");out.close();
  log<<"{\"type\":\"frame\",\"name\":\""<<source[image].name<<"\",\"epoch\":"<<expected_epoch<<",\"generation\":"<<expected_generation<<",\"bank\":"<<expected_bank<<",\"pixels\":"<<pixels<<",\"external_byte_leases\":"<<d.count_reads<<",\"external_byte_returns\":"<<d.count_responses<<",\"direct_consumes\":"<<d.count_direct_consumes<<",\"canonical_consumed\":"<<d.count_canonical_consumed<<",\"adapter_hits\":"<<d.count_hits<<",\"adapter_misses\":"<<d.count_misses<<",\"bytes\":"<<actual.size()<<",\"logical_reads\":"<<lines<<",\"physical_reads\":"<<physical_reads<<",\"start_cycle\":"<<start_cycle<<",\"first_pixel_cycle\":"<<first_pixel<<",\"last_pixel_cycle\":"<<last_pixel<<",\"closed_cycle\":"<<cycle<<",\"start_to_first_pixel\":"<<first_pixel-start_cycle<<",\"start_to_last_pixel\":"<<last_pixel-start_cycle<<",\"start_to_closed\":"<<cycle-start_cycle<<",\"held_pixel_cycles\":"<<held_pixels<<",\"physical_ready_stalls\":"<<ready_stalls<<",\"state_cycles\":"<<histogram(state_hist)<<",\"adapter_state_cycles\":"<<histogram(adapter_hist)<<",\"reader_state_cycles\":"<<histogram(reader_hist)<<",\"reader_pending_cycles\":"<<reader_pending_cycles<<",\"adapter_pending_cycles\":"<<adapter_pending_cycles<<",\"controller_busy_cycles\":"<<controller_busy_cycles<<",\"bridge_pending_cycles\":"<<bridge_pending_cycles<<",\"output\":\""<<name<<"\"}\n";
  pass("actual_full_RGB565_"+source[image].name);checking=false;for(unsigned i=0;i<3;i++)tick();
 }
};
int main(int argc,char**argv){try{need(argc==9,"args canonical.tsv rgb.tsv events outputdir seed retain +PRELOAD=file burst");Verilated::commandArgs(argc,argv);Bench b(uint32_t(std::stoul(argv[5])),std::stoul(argv[8])!=0,std::stoul(argv[6])!=0,argv[1],argv[2],argv[3]);b.units();b.full(0,argv[4]);b.full(1,argv[4]);need(!b.bus&&!b.line&&!b.d.busy,"terminal owners not drained");b.log<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<b.seed<<",\"retain\":"<<b.retain<<",\"checks\":"<<b.checks<<",\"cycles\":"<<b.cycle<<"}\n";std::cout<<"CONVERTER_JOIN_PASS seed="<<b.seed<<" retain="<<b.retain<<" cycles="<<b.cycle<<"\n";return 0;}catch(const std::exception&e){std::cerr<<"CONVERTER_JOIN_FAIL "<<e.what()<<"\n";return 1;}}
