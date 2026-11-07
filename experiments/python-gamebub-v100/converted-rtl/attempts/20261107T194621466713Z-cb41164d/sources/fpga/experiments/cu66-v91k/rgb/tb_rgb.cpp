#include "Vcanonical_rgb565_v91k.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using Bytes=std::vector<uint8_t>;
static void need(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
static Bytes unhex(const std::string &s){need(s.size()%2==0,"hex length");Bytes b;for(size_t i=0;i<s.size();i+=2)b.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));return b;}
static uint64_t hash_byte(uint64_t h,uint8_t b){return (h^b)*1099511628211ULL;}
static uint64_t hash(const Bytes &b){uint64_t h=1469598103934665603ULL;for(auto x:b)h=hash_byte(h,x);return h;}
struct Frame {std::string id;unsigned profile;Bytes canonical;};
static std::vector<Frame> load_frames(const std::string &path){std::ifstream f(path);need(bool(f),"canonical actual file");std::string line;std::vector<Frame> out;while(std::getline(f,line)){std::istringstream in(line);std::array<std::string,3>a;for(auto &v:a)need(bool(std::getline(in,v,'\t')),"canonical row");out.push_back({a[0],unsigned(std::stoul(a[1])),unhex(a[2])});need(out.back().canonical.size()==518400,"canonical full memory length");}need(!out.empty(),"canonical actual rows");return out;}
static std::map<std::string,Bytes> load_goldens(const std::string &path){std::ifstream f(path);need(bool(f),"RGB golden file");std::string line;std::map<std::string,Bytes> out;while(std::getline(f,line)){auto tab=line.find('\t');need(tab!=std::string::npos,"RGB golden row");auto id=line.substr(0,tab);need(!out.count(id),"duplicate RGB golden");out[id]=unhex(line.substr(tab+1));need(out[id].size()==691200,"RGB golden size");}return out;}
struct Pending {unsigned address,epoch,delay;uint8_t value;};
struct Held {unsigned address,epoch,word;bool operator==(const Held &o)const{return address==o.address&&epoch==o.epoch&&word==o.word;}};
struct Request {unsigned address,epoch;bool operator==(const Request &o)const{return address==o.address&&epoch==o.epoch;}};
struct Bench {
    Vcanonical_rgb565_v91k d;uint32_t rng,epoch=0;uint64_t cycle=0,reads=0,responses=0,pixels=0,read_hash=1469598103934665603ULL,word_hash=1469598103934665603ULL,output_stalls=0,request_stalls=0,first_req=0,last_rsp=0,first_out=0,last_out=0;
    const Frame *frame=nullptr;const Bytes *golden=nullptr;std::optional<Pending> pending;std::optional<Held> held;std::optional<Request> held_request;
    bool hold_response=false,hold_output=false,wrong_epoch=false,bus_error=false,checking=false;
    explicit Bench(unsigned seed):rng(seed){d.clk=0;d.reset=1;tick();d.reset=0;tick();}
    unsigned random(unsigned n){rng=rng*1664525U+1013904223U;return rng%n;}
    unsigned want_address(unsigned pixel,unsigned part)const {if(part==0)return pixel;unsigned y=pixel/720,x=pixel%720,k=(part-1)%4;unsigned cx=x/2+k%2,cy=y/2+k/2;if(cx>=360)cx=359;if(cy>=240)cy=239;return (part<=4?345600:432000)+cy*360+cx;}
    void tick(){
        d.clk=0;d.mem_req_ready=!pending&&(frame==nullptr||frame->profile==0||random(5)!=0);
        d.mem_rsp_valid=pending&&pending->delay==0&&!hold_response;
        d.mem_rsp_data=pending?pending->value:0;d.mem_rsp_epoch=pending?(pending->epoch+(wrong_epoch?1:0)):0;d.mem_rsp_error=bus_error;
        d.out_ready=!hold_output&&(frame==nullptr||frame->profile==0||random(4)!=0);d.eval();
        const bool kill=d.reset||d.cancel;
        Held now{d.out_addr,d.out_epoch,d.out_word};Request req{d.mem_req_addr,d.mem_req_epoch};
        if(held&&!kill)need(d.out_valid&&now==*held,"RGB output changed while held");
        if(held_request&&!kill)need(d.mem_req_valid&&req==*held_request,"RGB request changed while held");
        held=d.out_valid&&!d.out_ready&&!kill?std::optional<Held>(now):std::nullopt;
        held_request=d.mem_req_valid&&!d.mem_req_ready&&!kill?std::optional<Request>(req):std::nullopt;
        const bool req_accept=d.mem_req_valid&&d.mem_req_ready,rsp_accept=d.mem_rsp_valid&&d.mem_rsp_ready;
        if(req_accept){need(frame&&checking&&!pending,"RGB request without memory lease");need(d.mem_req_epoch==epoch,"RGB read epoch");need(d.mem_req_addr==want_address(unsigned(reads/9),unsigned(reads%9)),"RGB address schedule/provenance");need(d.mem_req_addr<frame->canonical.size(),"RGB byte address range");pending=Pending{d.mem_req_addr,d.mem_req_epoch,frame->profile==0?1:1+random(5),frame->canonical[d.mem_req_addr]};for(unsigned s=0;s<4;++s)read_hash=hash_byte(read_hash,uint8_t(d.mem_req_addr>>(8*s)));read_hash=hash_byte(read_hash,pending->value);++reads;if(!first_req)first_req=cycle;}
        if(rsp_accept){need(bool(pending),"RGB response without accepted owner");if(!wrong_epoch){pending.reset();++responses;last_rsp=cycle;}}
        else if(pending&&pending->delay&&!req_accept)--pending->delay;
        if(d.out_valid&&d.out_ready){need(golden&&checking&&!kill,"RGB output outside active candidate");need(d.out_epoch==epoch&&d.out_addr==pixels,"RGB pixel identity/order");unsigned value=unsigned((*golden)[2*pixels])|(unsigned((*golden)[2*pixels+1])<<8);need(d.out_word==value,"RGB exact mismatch pixel "+std::to_string(pixels));word_hash=hash_byte(hash_byte(word_hash,uint8_t(value)),uint8_t(value>>8));if(!first_out)first_out=cycle;last_out=cycle;++pixels;}
        if(d.out_valid&&!d.out_ready)++output_stalls;
        if(d.mem_req_valid&&!d.mem_req_ready)++request_stalls;
        d.clk=1;d.eval();++cycle;
    }
    void begin(const Frame &f,const Bytes &g){need(!pending&&!d.busy&&d.start_ready,"RGB start before bus drain");frame=&f;golden=&g;checking=true;reads=responses=pixels=0;read_hash=word_hash=1469598103934665603ULL;output_stalls=request_stalls=first_req=last_rsp=first_out=last_out=0;++epoch;d.start_epoch=epoch;d.start=1;tick();d.start=0;need(d.busy&&!d.done&&!d.error,"RGB start not active");}
    void stop(bool warm_reset){d.cancel=!warm_reset;d.reset=warm_reset;tick();d.cancel=0;d.reset=0;held.reset();held_request.reset();need(!d.out_valid&&!d.done,"RGB canceled output/completion");}
    void drain(){hold_response=false;for(unsigned n=0;n<100&&!d.start_ready;++n)tick();need(!pending&&!d.busy&&d.start_ready&&!d.done&&!d.out_valid,"RGB physical read drain");checking=false;}
    void wait_pending(){for(unsigned n=0;n<100&&!pending;++n)tick();need(bool(pending),"RGB pending read absent");}
    void prefix_retry(const Frame &f,const Bytes &g){begin(f,g);for(unsigned n=0;n<10000&&pixels<64;++n)tick();need(pixels>=64,"RGB clean retry prefix");stop(false);drain();}
};
int main(int argc,char **argv){try{
    need(argc==4,"usage: Vcanonical_rgb565_v91k canonical_actual.tsv rgb_goldens.tsv seed");auto frames=load_frames(argv[1]);auto goldens=load_goldens(argv[2]);unsigned seed=unsigned(std::stoul(argv[3]));Bench b(seed);unsigned cases=0;uint64_t all_pixels=0;
    for(const auto &f:frames){need(goldens.count(f.id),"missing RGB golden "+f.id);const auto &g=goldens.at(f.id);uint64_t immutable=hash(f.canonical);b.begin(f,g);uint64_t began=b.cycle;for(uint64_t n=0;n<100000000&&!b.d.done&&!b.d.error;++n)b.tick();need(b.d.done&&!b.d.error&&!b.d.busy&&!b.pending,"RGB complete watchdog/error");need(b.pixels==345600&&b.reads==3110400&&b.responses==b.reads,"RGB complete counters");need(b.d.count_reads==b.reads&&b.d.count_responses==b.responses&&b.d.count_pixels==b.pixels,"RGB hardware counters");need(hash(f.canonical)==immutable&&b.word_hash==hash(g),"RGB immutable source or final output hash");if(f.profile)need(b.output_stalls>0&&b.request_stalls>0,"RGB slow stalls not observed");std::cout<<"{\"type\":\"case\",\"id\":\""<<f.id<<"\",\"memory_profile\":"<<f.profile<<",\"seed\":"<<seed<<",\"status\":\"PASS\",\"epoch\":"<<b.epoch<<",\"pixels\":"<<b.pixels<<",\"reads\":"<<b.reads<<",\"responses\":"<<b.responses<<",\"read_schedule_hash\":"<<b.read_hash<<",\"rgb565_hash\":"<<b.word_hash<<",\"canonical_input_hash\":"<<immutable<<",\"cycles\":"<<b.cycle-began<<",\"first_read\":"<<b.first_req<<",\"last_response\":"<<b.last_rsp<<",\"first_output\":"<<b.first_out<<",\"last_output\":"<<b.last_out<<",\"output_stalls\":"<<b.output_stalls<<",\"request_stalls\":"<<b.request_stalls<<",\"publication\":false}\n";++cases;all_pixels+=b.pixels;}
    auto f=frames.front();f.profile=1;const auto &g=goldens.at(f.id);std::vector<std::string> checks;auto pass=[&](const std::string &name){checks.push_back(name);};
    for(bool reset:{false,true}){b.hold_response=true;b.begin(f,g);b.wait_pending();b.stop(reset);need(b.d.draining&&!b.d.start_ready,"RGB cancel lost accepted read owner");unsigned old_epoch=b.epoch;uint64_t old_reads=b.reads;b.d.start=1;b.d.start_epoch=old_epoch+99;for(unsigned n=0;n<7;++n)b.tick();b.d.start=0;need(b.d.draining&&!b.d.start_ready&&b.reads==old_reads&&!b.d.out_valid,"RGB replacement bypassed drain");b.drain();pass(reset?"warm_reset_pending_read_drain":"abort_pending_read_drain");b.prefix_retry(f,g);}
    for(bool reset:{false,true}){b.hold_output=true;b.begin(f,g);for(unsigned n=0;n<1000&&!b.d.out_valid;++n)b.tick();need(b.d.out_valid,"RGB held output absent");for(unsigned n=0;n<13;++n)b.tick();b.stop(reset);b.hold_output=false;b.drain();pass(reset?"warm_reset_held_pixel":"abort_held_pixel");}
    for(bool wrong:{true,false}){b.begin(f,g);b.wrong_epoch=wrong;b.bus_error=!wrong;for(unsigned n=0;n<100&&!b.d.error;++n)b.tick();need(b.d.error==(wrong?1:2)&&!b.d.done&&b.pixels==0,"RGB bad response not rejected");b.wrong_epoch=b.bus_error=false;b.drain();pass(wrong?"response_epoch_mismatch":"response_bus_error");b.prefix_retry(f,g);}
    b.d.start_epoch=0;b.d.start=1;b.tick();b.d.start=0;need(b.d.error==3&&!b.d.busy&&!b.d.done,"RGB zero epoch rejection");pass("zero_epoch_rejected");pass("clean_retry_after_cancel_and_fault");
    std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"pixels\":"<<all_pixels<<",\"reads_per_frame\":3110400,\"directed_checks\":"<<checks.size()<<",\"directed_check_names\":[";for(size_t i=0;i<checks.size();++i)std::cout<<(i?",":"")<<'"'<<checks[i]<<'"';std::cout<<"],\"scope\":\"RTL base RGB565 replay from actual canonical candidate memory, no HUD or publication\"}\n";return 0;
}catch(const std::exception &e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
