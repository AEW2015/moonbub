#include "Vcanonical_rgb565_lines.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <functional>
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
static uint64_t hash_u32(uint64_t h,unsigned value){for(unsigned s=0;s<4;++s)h=hash_byte(h,uint8_t(value>>(8*s)));return h;}
struct Frame {std::string id;unsigned profile;Bytes canonical;};
static std::vector<Frame> load_frames(const std::string &path){std::ifstream f(path);need(bool(f),"canonical actual file");std::string line;std::vector<Frame> out;while(std::getline(f,line)){std::istringstream in(line);std::array<std::string,3>a;for(auto &v:a)need(bool(std::getline(in,v,'\t')),"canonical row");out.push_back({a[0],unsigned(std::stoul(a[1])),unhex(a[2])});need(out.back().canonical.size()==518400,"canonical memory size");}need(!out.empty(),"canonical rows absent");return out;}
static std::map<std::string,Bytes> load_goldens(const std::string &path){std::ifstream f(path);need(bool(f),"RGB golden file");std::string line;std::map<std::string,Bytes> out;while(std::getline(f,line)){auto tab=line.find('\t');need(tab!=std::string::npos,"RGB row");auto id=line.substr(0,tab);need(!out.count(id),"duplicate RGB golden");out[id]=unhex(line.substr(tab+1));need(out[id].size()==691200,"RGB golden size");}return out;}
static std::vector<unsigned> schedule(){std::vector<unsigned> out;unsigned next_row=0;for(unsigned y=0;y<480;++y){unsigned last=y/2+1;if(last>239)last=239;while(next_row<=last){for(unsigned base:{345600U,432000U})for(unsigned x=0;x<360;++x)out.push_back(base+next_row*360+x);++next_row;}for(unsigned x=0;x<720;++x)out.push_back(y*720+x);}need(out.size()==518400,"independent schedule size");return out;}
struct Pending {unsigned address,epoch,delay;std::array<uint8_t,16> values;};
struct ByteOwner {unsigned address,epoch;};
struct Held {unsigned address,epoch,word;bool operator==(const Held &o)const{return address==o.address&&epoch==o.epoch&&word==o.word;}};
struct Request {unsigned address,epoch;bool operator==(const Request &o)const{return address==o.address&&epoch==o.epoch;}};
struct Bench {
    Vcanonical_rgb565_lines d;uint32_t rng,epoch=0;uint64_t cycle=0,reads=0,responses=0,pixels=0,lookups=0,lookup_responses=0,physical_reads=0,physical_responses=0;
    uint64_t read_hash=1469598103934665603ULL,word_hash=1469598103934665603ULL,lookup_hash=1469598103934665603ULL;
    uint64_t output_stalls=0,request_stalls=0,first_req=0,last_rsp=0,first_out=0,last_out=0,physical_hash=1469598103934665603ULL,byte_response_hash=1469598103934665603ULL;
    std::array<unsigned,240> cb_acks{},cr_acks{};std::array<int,2> valid_rows{{-1,-1}};
    const Frame *frame=nullptr;const Bytes *golden=nullptr;const std::vector<unsigned> addresses=schedule();
    std::vector<unsigned> physical_addresses;
    std::optional<Pending> pending;std::optional<ByteOwner> byte_owner;std::optional<Held> held;std::optional<Request> held_request;
    std::optional<uint64_t> local_response_due;
    bool hold_response=false,hold_output=false,hold_offer=false,wrong_epoch=false,bus_error=false,checking=false,record=false;
    std::ofstream trace;
    explicit Bench(unsigned seed,const std::string &path):rng(seed),trace(path){
        need(bool(trace),"row trace open");std::array<int,3> tags{{-1,-1,-1}};
        for(unsigned address:addresses){unsigned plane=address<345600?0:address<432000?1:2,line=address&~15U;
            if(tags[plane]!=int(line)){physical_addresses.push_back(line);tags[plane]=int(line);}}
        need(physical_addresses.size()==32400,"independent physical line schedule");
        d.clk=0;d.reset=1;tick();d.reset=0;tick();
    }
    unsigned random(unsigned n){rng=rng*1664525U+1013904223U;return rng%n;}
    void tick(){
        d.clk=0;d.mem_req_ready=!pending&&!hold_offer&&(frame==nullptr||frame->profile==0||random(5)!=0);
        d.mem_rsp_valid=pending&&pending->delay==0&&!hold_response;
        for(unsigned word=0;word<4;++word){d.mem_rsp_data[word]=0;if(pending)for(unsigned byte=0;byte<4;++byte)d.mem_rsp_data[word]|=uint32_t(pending->values[4*word+byte])<<(8*byte);}
        d.mem_rsp_epoch=pending?(pending->epoch+(wrong_epoch?1:0)):0;d.mem_rsp_error=bus_error;
        d.out_ready=!hold_output&&(frame==nullptr||frame->profile==0||random(4)!=0);d.eval();
        const bool kill=d.reset||d.cancel;
        Held now{d.out_addr,d.out_epoch,d.out_word};Request req{d.mem_req_addr,d.mem_req_epoch};
        if(held&&!kill)need(d.out_valid&&now==*held,"cached RGB output changed while held");
        if(held_request&&!kill)need(d.mem_req_valid&&req==*held_request,"cached request changed while held");
        held=d.out_valid&&!d.out_ready&&!kill?std::optional<Held>(now):std::nullopt;
        held_request=d.mem_req_valid&&!d.mem_req_ready&&!kill?std::optional<Request>(req):std::nullopt;
        if(kill||d.error)local_response_due.reset();
        if(local_response_due){
            need(d.lookup_response&&cycle==*local_response_due,"registered cache read latency/response");
            local_response_due.reset();++lookup_responses;
        }else if(!kill)need(!d.lookup_response,"unsolicited registered cache response");
        if(d.lookup_launch&&!kill){
            need(!local_response_due,"multiple local RAM lookup owners");local_response_due=cycle+1;
            need(checking&&lookups<345600&&d.out_addr==lookups,"local lookup order");
            unsigned top=unsigned(lookups/720/2),bottom=top<239?top+1:239;
            need((d.row_valid&(1U<<(top&1)))&&(d.row_valid&(1U<<(bottom&1))),"lookup before complete row fill");
            need(d.row_tag[top&1]==top&&d.row_tag[bottom&1]==bottom,"stale local row tag");
            need(cb_acks[top]==360&&cr_acks[top]==360&&cb_acks[bottom]==360&&cr_acks[bottom]==360,"lookup before all physical fill ACKs");
            lookup_hash=hash_byte(hash_byte(hash_byte(hash_u32(lookup_hash,unsigned(lookups)),uint8_t(top)),uint8_t(bottom)),uint8_t(d.row_valid));++lookups;
        }
        const bool byte_request=d.byte_req_valid&&d.byte_req_ready;
        const bool byte_response=d.byte_rsp_valid&&d.byte_rsp_ready;
        if(byte_request){
            need(checking&&frame&&!byte_owner&&reads<addresses.size(),"byte lease overwrite/range");
            need(d.byte_req_epoch==epoch&&d.byte_req_addr==addresses[reads],"inner byte address/epoch provenance");
            byte_owner=ByteOwner{d.byte_req_addr,d.byte_req_epoch};
            read_hash=hash_byte(hash_u32(read_hash,d.byte_req_addr),frame->canonical[d.byte_req_addr]);++reads;if(!first_req)first_req=cycle;
        }
        if(byte_response){
            need(bool(byte_owner)&&d.byte_rsp_epoch==byte_owner->epoch,"byte ACK without matching inner owner");
            unsigned address=byte_owner->address;
            if(checking&&!kill&&!d.error&&!d.byte_rsp_error){
                need(d.byte_rsp_data==frame->canonical[address],"gathered byte differs from actual candidate memory");
                byte_response_hash=hash_byte(hash_u32(byte_response_hash,address),d.byte_rsp_data);
                if(address>=345600){unsigned base=address<432000?345600:432000,row=(address-base)/360,column=(address-base)%360;
                    auto &count=address<432000?cb_acks[row]:cr_acks[row];need(count==column,"row ACK order/duplicate");++count;}
            }
            byte_owner.reset();++responses;last_rsp=cycle;
        }
        const bool req_accept=d.mem_req_valid&&d.mem_req_ready,rsp_accept=d.mem_rsp_valid&&d.mem_rsp_ready;
        if(req_accept){
            need(frame&&checking&&!pending&&physical_reads<physical_addresses.size(),"physical line offer without lease");
            need(d.mem_req_epoch==epoch&&d.mem_req_addr==physical_addresses[physical_reads],"physical line schedule/provenance");
            need(d.mem_req_addr%16==0&&d.mem_req_addr+16<=frame->canonical.size(),"physical line range/alignment");
            Pending next{d.mem_req_addr,d.mem_req_epoch,frame->profile==0?8:8+random(5),{}};
            physical_hash=hash_u32(physical_hash,d.mem_req_addr);
            for(unsigned i=0;i<16;++i){next.values[i]=frame->canonical[d.mem_req_addr+i];physical_hash=hash_byte(physical_hash,next.values[i]);}
            pending=next;++physical_reads;
        }
        if(rsp_accept){need(bool(pending),"physical ACK without owner");if(!wrong_epoch){pending.reset();++physical_responses;}}
        else if(pending&&pending->delay&&!req_accept)--pending->delay;
        if(d.out_valid&&d.out_ready){
            need(golden&&checking&&!kill&&pixels<345600,"cached RGB outside active candidate");
            need(d.out_epoch==epoch&&d.out_addr==pixels,"cached RGB output identity/order");
            unsigned value=unsigned((*golden)[2*pixels])|(unsigned((*golden)[2*pixels+1])<<8);
            need(d.out_word==value,"cached RGB exact mismatch pixel "+std::to_string(pixels));
            word_hash=hash_byte(hash_byte(word_hash,uint8_t(d.out_word)),uint8_t(d.out_word>>8));
            if(!first_out){first_out=cycle;}last_out=cycle;++pixels;
        }
        if(d.out_valid&&!d.out_ready)++output_stalls;
        if(d.mem_req_valid&&!d.mem_req_ready)++request_stalls;
        d.clk=1;d.eval();++cycle;
        if(kill){need(d.row_valid==0&&!d.out_valid,"cancel retained local valid tags/output");valid_rows={{-1,-1}};}
        else if(checking&&!d.error){
            for(unsigned slot=0;slot<2;++slot){
                if(d.row_valid&(1U<<slot)){
                    unsigned row=d.row_tag[slot];need(row<240&&(row&1)==slot,"row bank tag/parity");
                    need(cb_acks[row]==360&&cr_acks[row]==360,"row marked valid before complete ACK fill");
                    if(valid_rows[slot]!=int(row)){
                        if(record)trace<<"{\"type\":\"row_fill\",\"id\":\""<<frame->id<<"\",\"memory_profile\":"<<frame->profile<<",\"epoch\":"<<epoch<<",\"row\":"<<row<<",\"slot\":"<<slot<<",\"cb_acks\":360,\"cr_acks\":360,\"cycle\":"<<cycle<<"}\n";
                        valid_rows[slot]=int(row);
                    }
                }else valid_rows[slot]=-1;
            }
        }
    }
    void begin(const Frame &f,const Bytes &g,bool emit=false){
        need(!pending&&!byte_owner&&!d.busy&&d.start_ready,"cache start before physical drain");frame=&f;golden=&g;checking=true;record=emit;
        reads=responses=pixels=lookups=lookup_responses=physical_reads=physical_responses=0;read_hash=word_hash=lookup_hash=physical_hash=byte_response_hash=1469598103934665603ULL;
        output_stalls=request_stalls=first_req=last_rsp=first_out=last_out=0;cb_acks.fill(0);cr_acks.fill(0);valid_rows={{-1,-1}};
        ++epoch;d.start_epoch=epoch;d.start=1;tick();d.start=0;need(d.busy&&!d.done&&!d.error&&d.row_valid==0&&d.line_valid==0,"cached start active/tag invalidation");
        // Mutating the input descriptor cannot change the accepted lease.
        d.start_epoch=epoch^0x10000000U;
    }
    void stop(bool warm_reset){d.cancel=!warm_reset;d.reset=warm_reset;tick();d.cancel=0;d.reset=0;held.reset();held_request.reset();need(!d.out_valid&&!d.done&&d.row_valid==0&&d.line_valid==0,"cache canceled local state");}
    void drain(){hold_response=false;for(unsigned n=0;n<100&&!d.start_ready;++n){tick();}need(!pending&&!byte_owner&&!d.busy&&d.start_ready&&!d.done&&!d.out_valid,"cache physical owner drain");checking=false;record=false;}
    void wait_pending(unsigned kind,unsigned column,unsigned wanted_row=0){
        for(unsigned n=0;n<100000;++n){
            if(pending){unsigned address=pending->address;unsigned got=address<345600?2:address<432000?0:1;unsigned col=got==2?address%720:(address-(got==0?345600:432000))%360;
                unsigned row=got==2?address/720:(address-(got==0?345600:432000))/360;
                if(got==kind&&col==column&&row==wanted_row){hold_response=true;return;}}
            tick();
        }
        throw std::runtime_error("directed pending phase absent");
    }
    void prefix_retry(const Frame &f,const Bytes &g){begin(f,g);for(unsigned n=0;n<100000&&pixels<64;++n){tick();}need(pixels>=64,"cache clean retry prefix");stop(false);drain();}
};
int main(int argc,char **argv){try{
    need(argc==5,"usage: Vcanonical_rgb565_lines canonical_actual.tsv rgb_goldens.tsv seed cache-events.jsonl");
    auto frames=load_frames(argv[1]);auto goldens=load_goldens(argv[2]);unsigned seed=unsigned(std::stoul(argv[3]));Bench b(seed,argv[4]);unsigned cases=0;uint64_t all_pixels=0;
    for(const auto &f:frames){
        need(goldens.count(f.id),"missing cache RGB golden "+f.id);const auto &g=goldens.at(f.id);uint64_t immutable=hash(f.canonical);b.begin(f,g,true);uint64_t began=b.cycle;
        for(uint64_t n=0;n<100000000&&!b.d.done&&!b.d.error;++n){b.tick();}
        need(b.d.done&&!b.d.error&&!b.d.busy&&!b.pending,"cache complete watchdog/error");
        need(b.pixels==345600&&b.reads==518400&&b.responses==b.reads&&b.lookups==345600&&b.lookup_responses==345600,"cached completion counters");
        need(b.d.count_reads==b.reads&&b.d.count_responses==b.responses&&b.d.count_pixels==b.pixels,"cached hardware bus counters");
        need(b.d.count_luma_reads==345600&&b.d.count_chroma_reads==172800&&b.d.count_row_fills==240,"cache external reuse counters");
        need(b.d.count_lookups==345600&&b.d.count_cache_hits==345600,"registered local lookup counters");
        need(b.d.row_valid==3&&b.d.row_tag[0]==238&&b.d.row_tag[1]==239,"final cache row ownership");
        need(b.physical_reads==32400&&b.physical_responses==32400,"physical line read/ACK count");
        need(b.d.count_physical_requests==32400&&b.d.count_physical_responses==32400,"hardware physical ownership counters");
        need(b.d.count_byte_requests==518400&&b.d.count_hits==486000&&b.d.count_misses==32400,"hardware byte/line cache counters");
        need(b.d.line_valid==7&&b.d.line_address[0]==345584&&b.d.line_address[1]==431984&&b.d.line_address[2]==518384,"final plane line tags");
        need(b.byte_response_hash==b.read_hash,"actual gathered byte ACK stream mismatch");
        need(hash(f.canonical)==immutable&&b.word_hash==hash(g),"candidate changed or cached final RGB hash");
        if(f.profile)need(b.output_stalls>0&&b.request_stalls>0,"cached slow stalls not observed");
        std::cout<<"{\"type\":\"case\",\"id\":\""<<f.id<<"\",\"memory_profile\":"<<f.profile<<",\"seed\":"<<seed<<",\"status\":\"PASS\",\"epoch\":"<<b.epoch<<",\"pixels\":"<<b.pixels<<",\"reads\":"<<b.reads<<",\"responses\":"<<b.responses<<",\"read_schedule_hash\":"<<b.read_hash<<",\"physical_read_hash\":"<<b.physical_hash<<",\"byte_response_hash\":"<<b.byte_response_hash<<",\"physical_reads\":"<<b.physical_reads<<",\"physical_responses\":"<<b.physical_responses<<",\"physical_x16_beats\":"<<b.physical_reads*8<<",\"line_hits\":"<<b.d.count_hits<<",\"line_misses\":"<<b.d.count_misses<<",\"rgb565_hash\":"<<b.word_hash<<",\"canonical_input_hash\":"<<immutable<<",\"cycles\":"<<b.cycle-began<<",\"first_read\":"<<b.first_req<<",\"last_response\":"<<b.last_rsp<<",\"first_output\":"<<b.first_out<<",\"last_output\":"<<b.last_out<<",\"output_stalls\":"<<b.output_stalls<<",\"request_stalls\":"<<b.request_stalls<<",\"luma_reads\":"<<b.d.count_luma_reads<<",\"chroma_reads\":"<<b.d.count_chroma_reads<<",\"row_fills\":"<<b.d.count_row_fills<<",\"lookups\":"<<b.lookups<<",\"lookup_responses\":"<<b.lookup_responses<<",\"cache_hits\":"<<b.d.count_cache_hits<<",\"lookup_hash\":"<<b.lookup_hash<<",\"final_row_valid\":"<<unsigned(b.d.row_valid)<<",\"final_row_tags\":["<<unsigned(b.d.row_tag[0])<<','<<unsigned(b.d.row_tag[1])<<"],\"publication\":false}\n";
        ++cases;all_pixels+=b.pixels;
    }
    auto f=frames.front();f.profile=1;const auto &g=goldens.at(f.id);std::vector<std::string> checks;
    auto pass=[&](const std::string &name){checks.push_back(name);};
    const std::array<std::string,3> phase_names{{"cb_fill","cr_fill","luma"}};
    for(bool reset:{false,true}){
        b.hold_offer=true;b.begin(f,g);
        for(unsigned n=0;n<1000&&!b.d.mem_req_valid;++n){b.tick();}
        need(b.d.mem_req_valid&&b.byte_owner&&!b.pending,"stalled physical offer absent");
        b.stop(reset);b.hold_offer=false;b.drain();pass(reset?"warm_reset_unaccepted_line_offer":"abort_unaccepted_line_offer");
    }
    for(unsigned kind=0;kind<3;++kind)for(bool reset:{false,true}){
        b.begin(f,g);b.wait_pending(kind,kind==2?0:16);need(kind==2||b.d.row_valid==0,"partial first row became valid");b.stop(reset);
        need(b.d.draining&&!b.d.start_ready,"cached abort lost accepted read owner");uint64_t old_reads=b.reads;b.d.start=1;b.d.start_epoch=b.epoch+99;
        for(unsigned n=0;n<7;++n){b.tick();}b.d.start=0;need(b.d.draining&&!b.d.start_ready&&b.reads==old_reads&&!b.d.out_valid,"cache replacement bypassed physical drain");
        b.drain();pass(std::string(reset?"warm_reset_":"abort_")+phase_names[kind]+"_pending_drain");b.prefix_retry(f,g);
    }
    for(unsigned kind=0;kind<2;++kind)for(bool reset:{false,true}){
        b.begin(f,g);b.wait_pending(kind,16,2);
        need(b.pixels==1440&&b.d.row_valid==2&&b.d.row_tag[1]==1,"late eviction phase/retained row absent");
        b.stop(reset);need(b.pending&&b.d.draining&&!b.d.start_ready,"late eviction lost accepted physical owner");
        uint64_t old_reads=b.reads;b.d.start=1;b.d.start_epoch=b.epoch+77;
        for(unsigned n=0;n<7;++n){b.tick();}b.d.start=0;
        need(b.reads==old_reads&&!b.d.start_ready&&b.d.row_valid==0,"late eviction replacement bypassed drain");
        b.drain();pass(std::string(reset?"warm_reset_late_":"abort_late_")+phase_names[kind]+"_eviction");b.prefix_retry(f,g);
    }
    for(unsigned state:{6U,7U})for(bool reset:{false,true}){
        b.begin(f,g);for(unsigned n=0;n<100000&&b.d.state!=state;++n){b.tick();}need(b.d.state==state,"registered local phase absent");
        b.stop(reset);b.drain();pass(std::string(reset?"warm_reset_local_":"abort_local_")+std::to_string(state));
    }
    for(bool reset:{false,true}){
        b.hold_output=true;b.begin(f,g);for(unsigned n=0;n<100000&&!b.d.out_valid;++n){b.tick();}need(b.d.out_valid,"cached held pixel absent");
        for(unsigned n=0;n<13;++n){b.tick();}b.stop(reset);b.hold_output=false;b.drain();pass(reset?"warm_reset_held_pixel":"abort_held_pixel");
    }
    for(bool reset:{false,true}){
        b.begin(f,g);for(unsigned n=0;n<100000;++n){
            if(b.d.state==3&&b.d.fill_plane==1&&b.d.fill_row==0&&b.d.fill_column==359&&b.d.byte_rsp_valid)break;
            b.tick();
        }
        need(b.d.state==3&&b.d.fill_column==359&&b.d.byte_rsp_valid,"last inner fill ACK absent");b.stop(reset);
        need(!b.pending&&!b.d.draining&&b.d.row_valid==0,"last fill ACK published canceled row");b.drain();pass(reset?"warm_reset_last_fill_ack_same_edge":"abort_last_fill_ack_same_edge");
    }
    for(unsigned kind=0;kind<3;++kind)for(bool wrong:{true,false}){
        b.begin(f,g);b.wait_pending(kind,kind==2?0:16);b.hold_response=false;b.wrong_epoch=wrong;b.bus_error=!wrong;
        for(unsigned n=0;n<100&&!b.d.error;++n){b.tick();}
        need(b.d.error==(wrong?129:130)&&!b.d.done&&b.pixels==0,"cached response fault did not reject");
        if(wrong)need(b.pending&&b.d.draining&&!b.d.start_ready,"wrong epoch released genuine cache owner");else need(!b.pending,"matching bus error retained physical request");
        b.wrong_epoch=b.bus_error=false;b.drain();pass(std::string(wrong?"wrong_epoch_":"bus_error_")+phase_names[kind]);b.prefix_retry(f,g);
    }
    b.d.start_epoch=0;b.d.start=1;b.tick();b.d.start=0;need(b.d.error==131&&!b.d.busy&&!b.d.done,"cached zero epoch rejection");pass("zero_epoch_rejected");
    pass("start_epoch_snapshot_immutable");pass("complete_rows_only_and_parity_ownership");pass("registered_lookup_odd_even_edges_and_bottom_alias");pass("clean_retry_after_cancel_and_fault");
    std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"pixels\":"<<all_pixels<<",\"reads_per_frame\":518400,\"row_fills_per_frame\":240,\"logical_cache_bytes\":1440,\"line_slots_logical_bytes\":48,\"physical_reads_per_frame\":32400,\"directed_checks\":"<<checks.size()<<",\"directed_check_names\":[";
    for(size_t i=0;i<checks.size();++i){std::cout<<(i?",":"")<<'"'<<checks[i]<<'"';}std::cout<<"],\"scope\":\"Three aligned 128-bit plane slots behind frozen chroma cache; x16 data beats priced; no HUD/publication\"}\n";return 0;
}catch(const std::exception &e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
