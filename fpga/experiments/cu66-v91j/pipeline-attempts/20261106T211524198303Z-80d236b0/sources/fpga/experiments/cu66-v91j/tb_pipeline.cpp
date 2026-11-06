#include "Vcs88_pipeline_v91j.h"
#include "verilated.h"
#ifndef REFILL_OVERLAP
#define REFILL_OVERLAP 1
#endif
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>
#include <map>

static void need(bool test,const std::string &text){if(!test)throw std::runtime_error(text);}
static std::string quote(const std::string &s){std::string o="\"";for(char c:s){if(c=='"'||c=='\\')o+='\\';o+=c;}return o+'"';}
static std::vector<uint8_t> unhex(const std::string &s){
    if(s=="-")return {};
    need(s.size()%2==0,"odd hex");std::vector<uint8_t> r;
    for(size_t i=0;i<s.size();i+=2)r.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));
    return r;
}
static uint64_t hash_byte(uint64_t h,uint8_t b){return (h^b)*1099511628211ULL;}
struct Case{
    std::string id;unsigned error=0;std::vector<uint8_t> packet,prior,scales,operations;
    unsigned ref_valid=0,qvalid=0;uint32_t ref_fid=0,cache_fid=0;uint64_t ref_gen=0,cache_gen=0;
    std::array<std::vector<uint8_t>,3> dense;
};
static std::vector<Case> load(const std::string &path){
    std::ifstream f(path);need(bool(f),"vectors missing");std::vector<Case> out;std::string line;
    while(std::getline(f,line)){if(line.empty())continue;std::istringstream in(line);Case c;std::string p,a,b,m,y,u,v;
        in>>c.id>>c.error>>p>>c.ref_valid>>c.ref_fid>>c.ref_gen>>c.qvalid>>c.cache_fid>>c.cache_gen>>a>>b>>m>>y>>u>>v;
        need(!in.fail(),"vector columns "+c.id);std::string extra;need(!(in>>extra),"extra vector column");
        c.packet=unhex(p);c.prior=unhex(a);c.scales=unhex(b);c.operations=unhex(m);c.dense={unhex(y),unhex(u),unhex(v)};
        if(c.error==0||c.error==147){need(c.operations.size()==8100&&c.scales.size()==1350,"missing mapping goldens");}
        out.push_back(std::move(c));}
    need(!out.empty(),"empty corpus");return out;
}

struct Golden {unsigned plane=0,block=0,tile=0,cell=0,scale=0;std::vector<uint8_t> coefficients,dequant,residual;};
static std::map<std::string,Golden> goldens;
static std::string tile_key(const std::string &id,unsigned p,unsigned b){return id+":"+std::to_string(p)+":"+std::to_string(b);}
static void load_tiles(const std::string &path){
    std::ifstream file(path);need(bool(file),"transform goldens missing");std::string line;
    while(std::getline(file,line)){if(line.empty())continue;std::istringstream row(line);std::string id,c,d,r;Golden g;
        row>>id>>g.plane>>g.block>>g.tile>>g.cell>>g.scale>>c>>d>>r;need(!row.fail(),"transform golden columns");
        g.coefficients=unhex(c);g.dequant=unhex(d);g.residual=unhex(r);need(g.coefficients.size()==128&&g.dequant.size()==256&&g.residual.size()==256,"transform golden widths");
        need(goldens.emplace(tile_key(id,g.plane,g.block),std::move(g)).second,"duplicate transform golden");}
}
static int signed32(const std::vector<uint8_t> &bytes,unsigned index){uint32_t word=0;for(unsigned j=0;j<4;++j)word|=uint32_t(bytes[4*index+j])<<(8*j);return int(int32_t(word));}
static int signed_bits(uint32_t word,unsigned width){const uint32_t mask=(uint32_t(1)<<width)-1;word&=mask;return word&(uint32_t(1)<<(width-1))?int(int64_t(word)-(int64_t(1)<<width)):int(word);}
template<class Wide>static int packed_signed(const Wide &bits,unsigned index,unsigned width){unsigned at=index*width,word=at/32,shift=at%32;uint64_t value=bits[word];if(shift+width>32)value|=uint64_t(bits[word+1])<<32;return signed_bits(uint32_t(value>>shift),width);}
static uint64_t mix32(uint64_t hash,int value){const auto word=uint32_t(int32_t(value));for(unsigned j=0;j<4;++j)hash=hash_byte(hash,uint8_t(word>>(8*j)));return hash;}

struct Tuple{
    unsigned plane=0,block=0,index=0,tile=0,cell=0,scale=0;uint32_t frame_epoch=0,child_epoch=0;int value=0;uint32_t token=0;
    bool operator==(const Tuple &b)const{return plane==b.plane&&block==b.block&&index==b.index&&tile==b.tile&&cell==b.cell&&scale==b.scale&&frame_epoch==b.frame_epoch&&child_epoch==b.child_epoch&&value==b.value&&token==b.token;}
};
struct Request{bool write=false;uint32_t addr=0,epoch=0;std::array<uint32_t,4> data{};bool operator==(const Request &b)const{return write==b.write&&addr==b.addr&&epoch==b.epoch&&data==b.data;}};
class Bench{
public:
    Vcs88_pipeline_v91j d;std::mt19937 rng;uint64_t cycle=0;unsigned seed,profile=0;
    std::array<uint8_t,262144> ram{};std::array<uint32_t,16384> line_epoch{};
    struct Pending{Request req;uint64_t due;};std::optional<Pending> pending;std::optional<Request> held_request;std::optional<Tuple> held_output,held_coefficient;
    struct Read{uint32_t addr,epoch;uint8_t data;};std::optional<Read> local_read;
    std::ofstream trace;
    const Case *active=nullptr;bool monitor_active=false,record=false,force_stall=false,hold_response=false,force_output_hold=false;
    uint32_t next_epoch=0,frame_epoch=0;uint64_t begin_cycle=0,cache_cycles=0,cache_bytes=0;
    uint64_t inputs=0,coefficients=0,requests=0,acks=0,refill_observed=0,first_input=0,last_input=0,first_coef=0,last_coef=0,done_cycle=0;
    uint64_t queue_req_observed=0,queue_rsp_observed=0,queue_pop_observed=0,queue_stall_observed=0;
    unsigned queue_count_observed=0,queue_owned_observed=0;
    uint64_t assemble_during_math=0;
    uint64_t residual_comparisons=0,dq_comparisons=0,assembly_comparisons=0;
    uint64_t residuals=0,dq_tiles=0,launches=0,residual_tiles=0,last_residual=0,coefficient_done_cycle=0,residual_hash=0,residual_first=0;
    unsigned residual_index=0,residual_plane=0;uint32_t residual_token=0;std::array<unsigned,3> residual_counts{};Tuple residual_metadata{};
    uint64_t dense_comparisons=0,directed_comparisons=0,tiles=0,tile_hash=1469598103934665603ULL,tile_first=0;
    std::array<unsigned,3> observed_blocks{},observed_coefficients{};std::vector<uint32_t> child_epochs;
    std::vector<uint8_t> received;std::array<std::vector<unsigned>,3> positions;
    std::array<uint32_t,3> span_offset{},span_length{};
    unsigned output_plane=0;std::optional<std::pair<unsigned,unsigned>> held_input;
    explicit Bench(unsigned s,const std::string &path):rng(s),seed(s),trace(path){
        need(bool(trace),"tile trace open");ram.fill(0xa5);line_epoch.fill(0xffffffffU);
        d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=0;d.epoch=0;
        d.serial_clear=0;d.write_overlap=1;d.read_prefetch=1;d.tile_overlap=1;
        d.in_valid=0;d.in_last=0;d.in_data=0;d.out_ready=0;
        d.cache_valid=0;d.cache_last=0;d.cache_data=0;d.cache_ref_fid=0;d.cache_ref_generation=0;
        d.accepted_ref_valid=0;d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;
        d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;
        for(unsigned k=0;k<4;++k)d.mem_rsp_data[k]=0;
        tick();d.reset=0;tick();
    }
    unsigned random(unsigned n){return rng()%n;}
    Tuple coefficient_tuple()const{return {unsigned(d.coefficient_plane),unsigned(d.coefficient_block),unsigned(d.coefficient_index),unsigned(d.coefficient_tile),unsigned(d.coefficient_qcell),unsigned(d.coefficient_qscale),d.coefficient_epoch,d.current_child_epoch,int(int16_t(d.coefficient_value))};}
    Tuple tuple()const{return {unsigned(d.out_plane),unsigned(d.out_block),unsigned(d.out_index),unsigned(d.out_tile),unsigned(d.out_qcell),unsigned(d.out_qscale),d.out_epoch,d.out_child_epoch,signed_bits(d.out_value,24),d.out_token};}
    Request request()const{Request q;q.write=d.mem_req_write;q.addr=d.mem_req_addr;q.epoch=d.mem_req_epoch;for(unsigned k=0;k<4;++k)q.data[k]=d.mem_req_data[k];return q;}
    void observe_coefficient(){
        need(active!=nullptr,"output without active frame");const Tuple t=coefficient_tuple();need(t.plane<3&&t.index<64&&t.plane==output_plane,"tuple range/global plane order");
        const unsigned ordinal=observed_coefficients[t.plane]/64,index=observed_coefficients[t.plane]%64;
        need(ordinal<positions[t.plane].size(),"too many coefficient blocks");
        const unsigned tile=positions[t.plane][ordinal],qcell=t.plane?tile:(tile/90/2)*45+(tile%90/2);
        need(t.block==ordinal&&t.index==index&&t.tile==tile&&t.cell==qcell&&t.scale==active->scales[qcell],"coefficient positional/scale tuple mismatch "+active->id);
        need(t.frame_epoch==frame_epoch&&t.child_epoch!=0,"tuple epoch mismatch");
        const auto &gold=active->dense[t.plane];const size_t at=2*observed_coefficients[t.plane];
        need(at+2<=gold.size(),"missing coefficient golden");const int expected=int(int16_t(unsigned(gold[at])|(unsigned(gold[at+1])<<8)));
        need(t.value==expected,"coefficient value mismatch "+active->id);
        if(index==0){tile_hash=1469598103934665603ULL;tile_first=cycle+1;}
        const uint16_t bits=uint16_t(int16_t(t.value));tile_hash=hash_byte(hash_byte(tile_hash,uint8_t(bits)),uint8_t(bits>>8));
        ++observed_coefficients[t.plane];++coefficients;if(record)++dense_comparisons;else ++directed_comparisons;if(first_coef==0)first_coef=cycle+1;last_coef=cycle+1;
        if(index==63){++observed_blocks[t.plane];if(record)++tiles;
            if(ordinal+1==positions[t.plane].size()){
                ++output_plane;while(output_plane<3&&positions[output_plane].empty())++output_plane;
            }

        }
    }

    const Golden &golden(unsigned plane,unsigned block)const {need(active!=nullptr,"transform without active case");auto it=goldens.find(tile_key(active->id,plane,block));need(it!=goldens.end(),"missing transform golden "+active->id);return it->second;}
    void event(const std::string &stage,const Tuple &t,uint32_t token,uint64_t hash,unsigned samples,uint64_t first,uint64_t last,bool complete=true){
        if(record)trace<<"{\"type\":\"transform\",\"stage\":"<<quote(stage)<<",\"id\":"<<quote(active->id)<<",\"memory_profile\":"<<profile<<",\"plane\":"<<t.plane<<",\"block\":"<<t.block<<",\"tile\":"<<t.tile<<",\"qcell\":"<<t.cell<<",\"qscale\":"<<t.scale<<",\"frame_epoch\":"<<t.frame_epoch<<",\"child_epoch\":"<<t.child_epoch<<",\"token\":"<<token<<",\"value_hash\":"<<hash<<",\"samples\":"<<samples<<",\"first_cycle\":"<<first<<",\"last_cycle\":"<<last<<",\"complete\":"<<(complete?"true":"false")<<"}\n";
    }
    uint32_t child_for_plane(unsigned plane)const{unsigned ordinal=0;for(unsigned p=0;p<plane;++p)if(span_length[p])++ordinal;need(ordinal<child_epochs.size(),"missing child epoch owner");return child_epochs[ordinal];}
    Tuple debug_tuple()const{return {unsigned(d.inverse_plane),unsigned(d.inverse_block),0,unsigned(d.inverse_tile),unsigned(d.inverse_qcell),unsigned(d.inverse_qscale),d.inverse_epoch,d.inverse_child_epoch,0};}
    void observe_transform_stage(bool dequant){
        const Tuple t=debug_tuple();const auto &g=golden(t.plane,t.block);
        need(t.tile==g.tile&&t.cell==g.cell&&t.scale==g.scale&&t.frame_epoch==frame_epoch&&t.child_epoch==child_for_plane(t.plane)&&d.inverse_token!=0,"inverse stage metadata mismatch");
        uint64_t hash=1469598103934665603ULL;
        for(unsigned i=0;i<64;++i){const int actual=dequant?packed_signed(d.inverse_dequantized,i,20):packed_signed(d.inverse_coefficients,i,16);
            const int expected=dequant?signed32(g.dequant,i):int(int16_t(unsigned(g.coefficients[2*i])|(unsigned(g.coefficients[2*i+1])<<8)));
            need(actual==expected,"assembled/dequant exact mismatch "+active->id);
            if(dequant){hash=mix32(hash,actual);if(record)++dq_comparisons;}else{const uint16_t bits=uint16_t(int16_t(actual));hash=hash_byte(hash_byte(hash,uint8_t(bits)),uint8_t(bits>>8));if(record)++assembly_comparisons;}}
        if(dequant)++dq_tiles;else ++launches;
        event(dequant?"dequant":"assemble",t,d.inverse_token,hash,64,cycle+1,cycle+1);
    }
    void observe_residual(){
        const Tuple t=tuple();const auto &g=golden(t.plane,t.block);
        need(t.plane<3&&t.plane==residual_plane&&t.block==residual_counts[t.plane]/64&&t.index==residual_counts[t.plane]%64,"residual ordering");
        need(t.tile==g.tile&&t.cell==g.cell&&t.scale==g.scale&&t.frame_epoch==frame_epoch&&t.child_epoch==child_for_plane(t.plane)&&t.token!=0,"residual metadata mismatch");
        need(t.value==signed32(g.residual,t.index),"residual value mismatch "+active->id);
        if(t.index==0){residual_hash=1469598103934665603ULL;residual_first=cycle+1;residual_metadata=t;residual_token=d.out_token;}
        need(t.token==residual_token,"residual token changed within tile");
        residual_hash=mix32(residual_hash,t.value);++residuals;if(record)++residual_comparisons;++residual_counts[t.plane];residual_index=t.index+1;last_residual=cycle+1;
        if(t.index==63){++residual_tiles;event("residual",t,d.out_token,residual_hash,64,residual_first,cycle+1);residual_index=0;
            if(residual_counts[t.plane]/64==positions[t.plane].size()){++residual_plane;while(residual_plane<3&&positions[residual_plane].empty())++residual_plane;}}
    }
    void tick(){
        d.clk=0;d.out_ready=!force_output_hold&&(profile==0||random(4)!=0);
        d.mem_req_ready=!pending&&!force_stall&&(profile==0||random(4)!=0);
        d.mem_rsp_valid=pending&&cycle>=pending->due&&!hold_response;
        if(d.mem_rsp_valid){d.mem_rsp_epoch=pending->req.epoch;d.mem_rsp_error=0;for(unsigned k=0;k<4;++k){
            uint32_t value=0;for(unsigned j=0;j<4;++j)value|=uint32_t(ram[pending->req.addr+4*k+j])<<(8*j);d.mem_rsp_data[k]=value;}}
        d.eval();const bool cancel=d.reset||d.abort_packet;
        need(unsigned(d.queue_count)+unsigned(d.queue_pending)<=2,"refill owner bound");
        if(REFILL_OVERLAP==0)need(d.queue_count==0&&!d.queue_pending&&d.queue_requests==0,"disabled queue not static zero");
        if(cancel||d.error!=0||d.stage_cancel){held_request.reset();held_output.reset();held_coefficient.reset();}
        if(REFILL_OVERLAP!=0&&monitor_active&&!cancel){
            if(d.frame_read_req)++queue_req_observed;
            if(d.frame_read_rsp)++queue_rsp_observed;
            if(d.stage_write)++queue_pop_observed;
            if(d.queue_stall)++queue_stall_observed;
            need(bool(d.queue_push)==bool(d.frame_read_rsp),"queue response push conservation");
            need(bool(d.queue_pop)==bool(d.stage_write),"queue pop/child write conservation");
        }
        if(cancel)held_input.reset();
        if(held_input)need(d.in_valid&&std::make_pair(unsigned(d.in_data),unsigned(d.in_last))==*held_input,"held outer input changed");
        held_input=d.in_valid&&!d.in_ready&&!cancel?std::optional<std::pair<unsigned,unsigned>>(std::make_pair(unsigned(d.in_data),unsigned(d.in_last))):std::nullopt;
        if(held_request)need(d.mem_req_valid&&request()==*held_request,"held memory offer changed");
        if(held_output)need(d.out_valid&&tuple()==*held_output,"held coefficient tuple changed");
        held_request=d.mem_req_valid&&!d.mem_req_ready?std::optional<Request>(request()):std::nullopt;
        held_output=d.out_valid&&!d.out_ready?std::optional<Tuple>(tuple()):std::nullopt;
        if(cancel){local_read.reset();need(!d.out_valid&&!d.frame_read_req,"cancel leaked local traffic");}
        else {
            if(local_read){need(d.frame_read_rsp&&d.frame_rsp_addr==local_read->addr&&d.frame_rsp_epoch==local_read->epoch&&d.frame_read_data==local_read->data,"outer synchronous replay response binding");local_read.reset();}
            else need(!d.frame_read_rsp,"unsolicited outer replay response");
            if(d.frame_read_req){need(d.frame_read_addr<received.size(),"outer replay reads unavailable byte");local_read=Read{d.frame_read_addr,frame_epoch,received[d.frame_read_addr]};}
        }
        if(d.in_valid&&d.in_ready){received.push_back(d.in_data);++inputs;if(first_input==0)first_input=cycle+1;last_input=cycle+1;}
        if(d.stage_write){++refill_observed;need(monitor_active&&active!=nullptr&&d.coefficient_plane<3,"child input without frame");const unsigned p=d.coefficient_plane,at=d.stage_write_addr;
            need(at<span_length[p]&&span_offset[p]+at<active->packet.size(),"child refill span range");need(d.stage_write_data==active->packet[span_offset[p]+at],"child refill byte provenance");}
        if(monitor_active&&d.core_starts>child_epochs.size()){
            need(d.core_starts==child_epochs.size()+1,"child start conservation");
            if(!child_epochs.empty())need(d.current_child_epoch>child_epochs.back(),"nonmonotonic cross-plane child epoch");
            child_epochs.push_back(d.current_child_epoch);
        }
        if(d.coefficient_valid&&d.coefficient_ready){need(monitor_active,"coefficient outside current frame");observe_coefficient();if(d.inverse_math_state!=0)++assemble_during_math;}
        if(d.inverse_launch)observe_transform_stage(false);
        if(d.inverse_dequant)observe_transform_stage(true);
        if(d.out_valid&&d.out_ready){need(monitor_active,"residual outside current frame");observe_residual();}
        need(d.inverse_owned_banks<=2&&d.inverse_max_owned_banks<=2,"inverse owner bound");
        if(held_coefficient)need(d.coefficient_valid&&coefficient_tuple()==*held_coefficient,"held coefficient changed at inverse boundary");
        held_coefficient=d.coefficient_valid&&!d.coefficient_ready?std::optional<Tuple>(coefficient_tuple()):std::nullopt;
        const bool response=d.mem_rsp_valid&&d.mem_rsp_ready;
        if(response){need(pending.has_value(),"response without accepted owner");const auto &q=pending->req;
            if(q.write){for(unsigned k=0;k<4;++k)for(unsigned j=0;j<4;++j)ram[q.addr+4*k+j]=uint8_t(q.data[k]>>(8*j));line_epoch[q.addr/16]=q.epoch;}
            else need(line_epoch[q.addr/16]==q.epoch,"read before matching epoch physical write ACK");
            pending.reset();++acks;
        }
        if(d.mem_req_valid&&d.mem_req_ready){need(!pending,"multiple accepted external requests");const Request q=request();need(q.addr%16==0&&q.addr+16<=ram.size(),"external memory request bounds");
            pending=Pending{q,cycle+(profile==0?1:(q.write?16:18)+unsigned(((q.addr>>4)^seed)&3))};++requests;}
        d.clk=1;d.eval();++cycle;
        if(REFILL_OVERLAP!=0&&monitor_active&&!cancel){
            queue_count_observed=std::max(queue_count_observed,unsigned(d.queue_count));
            queue_owned_observed=std::max(queue_owned_observed,unsigned(d.queue_count)+unsigned(d.queue_pending));
        }
        if(monitor_active&&d.done&&done_cycle==0)done_cycle=cycle;
        if(monitor_active&&d.coefficient_done&&coefficient_done_cycle==0)coefficient_done_cycle=cycle;
    }
    static uint32_t be32(const std::vector<uint8_t> &b,unsigned n){return uint32_t(b[n])<<24|uint32_t(b[n+1])<<16|uint32_t(b[n+2])<<8|uint32_t(b[n+3]);}
    void prepare(const Case &c,unsigned p,bool emit){
        need(!pending&&!d.busy&&d.start_ready,"prepare with outstanding ownership");active=&c;profile=p;record=emit;monitor_active=false;held_input.reset();
        assemble_during_math=0;residuals=0;dq_tiles=0;launches=0;residual_tiles=0;last_residual=0;coefficient_done_cycle=0;residual_index=0;residual_plane=0;residual_counts.fill(0);
        inputs=0;coefficients=0;requests=0;acks=0;refill_observed=0;first_input=last_input=first_coef=last_coef=done_cycle=0;cache_cycles=cache_bytes=0;
        queue_req_observed=queue_rsp_observed=queue_pop_observed=queue_stall_observed=0;
        queue_count_observed=queue_owned_observed=0;
        observed_blocks.fill(0);observed_coefficients.fill(0);received.clear();child_epochs.clear();local_read.reset();held_output.reset();held_request.reset();held_coefficient.reset();
        for(auto &v:positions)v.clear();
        if(c.operations.size()==8100){for(unsigned axis=0,base=0;axis<3;++axis){unsigned n=axis?1350:5400;for(unsigned t=0;t<n;++t)if(c.operations[base+t]==2)positions[axis].push_back(t);base+=n;}}
        output_plane=0;while(output_plane<3&&positions[output_plane].empty())++output_plane;
        span_offset.fill(0);span_length.fill(0);
        if(c.packet.size()>=132){unsigned cursor=128+be32(c.packet,36)+be32(c.packet,40),end=cursor+be32(c.packet,48);
            for(unsigned axis=0;axis<3&&cursor+4<=end;++axis){unsigned chunks=be32(c.packet,cursor);cursor+=4;if(chunks==1&&cursor+8<=end){span_length[axis]=be32(c.packet,cursor+4);cursor+=8;span_offset[axis]=cursor;cursor+=span_length[axis];}}}
    }
    void preload(const Case &c){
        if(!c.qvalid)return;
        need(c.prior.size()==1350,"prior qcache length");const uint64_t before=cycle;
        d.cache_ref_fid=c.cache_fid;d.cache_ref_generation=c.cache_gen;
        for(unsigned i=0;i<1350;++i){d.cache_valid=1;d.cache_data=c.prior[i];d.cache_last=i==1349;
            need(d.cache_ready,"qcache preload unexpectedly blocked");tick();++cache_bytes;
            // Start's snapshot uses the tag latched at the first cache byte.
            if(i==0){d.cache_ref_fid=~c.cache_fid;d.cache_ref_generation=~c.cache_gen;}
        }
        d.cache_valid=0;d.cache_last=0;cache_cycles=cycle-before;
        const bool invalid=std::find(c.prior.begin(),c.prior.end(),uint8_t(3))!=c.prior.end();
        need(bool(d.cache_complete)==!invalid,"cache completion/invalid-value eligibility");if(invalid)need(d.cache_error==3,"invalid qcache reason");
    }
    void begin(const Case &c,std::optional<uint32_t> forced_epoch={}){
        need(d.start_ready,"start before drain");d.packet_bytes=c.packet.size();frame_epoch=forced_epoch.value_or(++next_epoch);d.epoch=frame_epoch;
        d.accepted_ref_valid=c.ref_valid;d.accepted_qcache_valid=c.qvalid;d.accepted_ref_fid=c.ref_fid;d.accepted_ref_generation=c.ref_gen;
        d.start=1;begin_cycle=cycle;tick();d.start=0;monitor_active=true;need(!d.cache_complete,"cache not consumed by frame start");
        d.accepted_ref_valid=!c.ref_valid;d.accepted_qcache_valid=!c.qvalid;d.accepted_ref_fid=~c.ref_fid;d.accepted_ref_generation=~c.ref_gen;
    }
    void feed_until(unsigned target=255){
        need(active!=nullptr,"no active input");size_t at=0;bool offered=false;
        for(unsigned watchdog=0;watchdog<12000000;++watchdog){
            d.clk=0;d.eval();if(d.frame_state==target){d.in_valid=0;d.in_last=0;return;}
            if(d.error||d.done){d.in_valid=0;d.in_last=0;return;}
            if(!offered&&at<active->packet.size())offered=profile==0||random(4)!=0;
            d.in_valid=offered;d.in_data=at<active->packet.size()?active->packet[at]:0;d.in_last=at+1==active->packet.size();
            d.clk=0;d.eval();bool accepted=d.in_valid&&d.in_ready;tick();if(accepted){++at;offered=false;}
        }
        throw std::runtime_error("frame watchdog "+active->id);
    }
    void settle(){d.in_valid=0;d.in_last=0;for(unsigned k=0;k<200000;++k){if(!pending&&!d.busy&&d.start_ready)return;tick();}throw std::runtime_error("ownership drain watchdog");}
    void finish(const Case &c){
        need(d.error==c.error,"frame error mismatch "+c.id+": got "+std::to_string(d.error)+" expected "+std::to_string(c.error));
        if(c.error==0){need(d.done&&!pending&&!d.inverse_busy&&d.inverse_owned_banks==0,"inverse completion not quiescent");for(unsigned p=0;p<3;++p){need(observed_coefficients[p]*2==c.dense[p].size(),"incomplete coefficient plane");need(residual_counts[p]==observed_coefficients[p],"incomplete residual plane");}need(launches==dq_tiles&&dq_tiles==residual_tiles,"inverse stage conservation");}
        else {need(!d.done,"failed frame completed");if(c.error==64||c.error==7||c.error==65)need(d.core_starts==0&&coefficients==0&&requests==0,"early reject produced decoder side effects");}
        if(c.error==147){need(observed_coefficients[0]*2==c.dense[0].size()&&observed_coefficients[1]*2==c.dense[1].size()&&observed_coefficients[2]==0,"late CRC provisional prefix scope");}
        if(c.error&&residual_index){event("residual",residual_metadata,residual_token,residual_hash,residual_index,residual_first,last_residual,false);residual_index=0;}
        settle();need(requests==acks,"accepted memory request not acknowledged");
        need(d.inverse_count_inputs==coefficients,"inverse input count");need(d.inverse_count_outputs==residuals,"inverse output count");
        if(REFILL_OVERLAP!=0){
            need(d.queue_requests==d.queue_responses&&d.queue_responses==d.queue_pops,"refill queue conservation at completion");
            need(d.queue_pops==refill_observed,"refill queue/child byte conservation");
            need(d.queue_count==0&&!d.queue_pending,"local owners remain after case");
            need(d.queue_requests==queue_req_observed&&d.queue_responses==queue_rsp_observed&&d.queue_pops==queue_pop_observed&&d.queue_stalls==queue_stall_observed,"independent queue event counters");
            need(d.queue_max_count==queue_count_observed&&d.queue_max_owned==queue_owned_observed,"independent queue highwaters");
        }
        need(d.refill_bytes==refill_observed,"child input/refill conservation");
        if(c.error==0||c.error==147)need(refill_observed==uint64_t(span_length[0])+span_length[1]+span_length[2],"full chunk refill coverage");
        std::cout<<"{\"type\":\"case\",\"id\":"<<quote(c.id)<<",\"refill_overlap\":"<<REFILL_OVERLAP<<",\"memory_profile\":"<<profile<<",\"status\":\"PASS\",\"error\":"<<unsigned(d.error)<<",\"seed\":"<<seed<<",\"coefficients\":"<<coefficients<<",\"core_starts\":"<<d.core_starts<<",\"refill_bytes\":"<<d.refill_bytes<<",\"frame_epoch\":"<<frame_epoch<<",\"child_epochs\":[";
        for(size_t k=0;k<child_epochs.size();++k){if(k)std::cout<<',';std::cout<<child_epochs[k];}
        std::cout<<"],\"refill_queue\":{\"requests\":"<<d.queue_requests<<",\"responses\":"<<d.queue_responses<<",\"pops\":"<<d.queue_pops<<",\"stalls\":"<<d.queue_stalls<<",\"cancel_queued\":"<<d.queue_cancel_queued<<",\"cancel_pending\":"<<d.queue_cancel_pending<<",\"max_count\":"<<unsigned(d.queue_max_count)<<",\"max_owned\":"<<unsigned(d.queue_max_owned)<<",\"final_count\":"<<unsigned(d.queue_count)<<",\"final_pending\":"<<unsigned(d.queue_pending)<<",\"observed_requests\":"<<queue_req_observed<<",\"observed_responses\":"<<queue_rsp_observed<<",\"observed_pops\":"<<queue_pop_observed<<",\"observed_stalls\":"<<queue_stall_observed<<",\"observed_max_count\":"<<queue_count_observed<<",\"observed_max_owned\":"<<queue_owned_observed<<"},\"inverse\":{\"assembled_tiles\":"<<launches<<",\"dq_tiles\":"<<dq_tiles<<",\"residual_tiles\":"<<residual_tiles<<",\"residual_samples\":"<<residuals<<",\"owned_banks\":"<<unsigned(d.inverse_owned_banks)<<",\"max_owned_banks\":"<<unsigned(d.inverse_max_owned_banks)<<",\"assembly_during_math_inputs\":"<<assemble_during_math<<",\"cancelled_banks\":"<<d.inverse_count_cancelled_banks<<"},\"coefficient_done_cycle\":"<<coefficient_done_cycle<<",\"last_residual\":"<<last_residual<<",\"cycles\":"<<cycle-begin_cycle<<",\"first_input\":"<<first_input<<",\"last_input\":"<<last_input<<",\"first_coef\":"<<first_coef<<",\"last_coef\":"<<last_coef<<",\"done_cycle\":"<<done_cycle<<",\"requests\":"<<requests<<",\"acks\":"<<acks<<",\"cache_cycles\":"<<cache_cycles<<",\"cache_bytes\":"<<cache_bytes<<",\"pending_drain\":false,\"full_frame_publication\":false}\n";
    }
    void abort_and_drain(bool warm_reset){
        d.in_valid=0;d.in_last=0;if(warm_reset)d.reset=1;else d.abort_packet=1;tick();d.reset=0;d.abort_packet=0;
        need(!d.out_valid&&!d.done,"cancel left visible coefficient/completion");
        settle();
    }
};
int main(int argc,char **argv){
    try{
        need(argc==5,"usage: Vcs88_pipeline_v91j cases.tsv transform_tiles.tsv seed transform-events.jsonl");auto cases=load(argv[1]);load_tiles(argv[2]);unsigned seed=unsigned(std::stoul(argv[3]));Bench b(seed,argv[4]);
        unsigned rows=0;const Case *good=nullptr,*delta=nullptr,*late=nullptr;
        for(unsigned profile=0;profile<2;++profile)for(const auto &c:cases){b.prepare(c,profile,true);b.preload(c);b.begin(c);b.feed_until();b.finish(c);++rows;if(c.error==147)late=&c;if(c.error==0&&c.dense[0].size()>0){if(!good)good=&c;if(c.qvalid&&!delta)delta=&c;}}
        need(good&&delta&&late,"need key, delta and late-CRC goldens for recovery checks");std::vector<std::string> checks;
        auto pass=[&](const std::string &name){checks.push_back(name);std::cout<<"{\"type\":\"directed\",\"name\":"<<quote(name)<<",\"status\":\"PASS\"}\n";};
        if(REFILL_OVERLAP!=0)for(bool reset:{false,true}){
            b.prepare(*good,0,false);b.preload(*good);b.begin(*good);b.feed_until(16);
            for(unsigned k=0;k<20&&!(b.d.queue_count==1&&b.d.queue_pending);++k)b.tick();
            need(b.d.queue_count==1&&b.d.queue_pending,"integrated queued/pending refill setup");
            b.abort_and_drain(reset);
            need(b.d.queue_count==0&&!b.d.queue_pending&&!b.d.frame_read_req&&!b.d.frame_read_rsp,"cancel retained integrated local refill traffic");
            if(!reset)need(b.d.queue_cancel_queued==1&&b.d.queue_cancel_pending==1,"integrated cancel owner accounting");
            pass(reset?"warm_reset_queued_and_pending_refill":"abort_queued_and_pending_refill");
        }
        // Cancellation with a real, accepted external write still outstanding.
        for(bool reset:{false,true}){
            b.prepare(*good,1,false);b.preload(*good);b.begin(*good);b.hold_response=true;
            b.feed_until(11);
            for(unsigned k=0;k<2000000&&!b.pending;++k)b.tick();
            need(b.pending.has_value(),"no accepted request for drain cancellation");auto owner=b.pending->req;
            b.d.in_valid=0;b.d.in_last=0;if(reset)b.d.reset=1;else b.d.abort_packet=1;b.tick();b.d.reset=0;b.d.abort_packet=0;
            need(!b.d.start_ready,"new start allowed before old ACK drain");
            const unsigned old_starts=b.d.core_starts;b.d.start=1;b.d.epoch=++b.next_epoch;b.tick();b.d.start=0;
            need(b.d.core_starts==old_starts&&b.pending&&b.pending->req==owner,"blocked replacement changed accepted owner");
            b.hold_response=false;b.settle();need(!b.pending,"old write not drained");
            pass(reset?"warm_reset_accepted_write_drain_blocks_start":"abort_accepted_write_drain_blocks_start");
        }
        // Hold a mapped output then cancel; its entire tuple must remain stable.
        b.prepare(*good,1,false);b.preload(*good);b.begin(*good);b.force_output_hold=true;b.feed_until(11);
        for(unsigned k=0;k<2000000&&!b.d.out_valid;++k){b.tick();}need(b.d.out_valid,"held mapped output absent");
        for(unsigned k=0;k<7;++k){b.tick();}b.force_output_hold=false;b.abort_and_drain(false);pass("abort_held_mapped_coefficient");
        // Cancel the new inverse path while IDCT owns a real assembled tile.
        b.prepare(*good,1,false);b.preload(*good);b.begin(*good);b.feed_until(11);
        for(unsigned k=0;k<2000000&&b.d.inverse_math_state!=3;++k)b.tick();need(b.d.inverse_math_state==3,"integrated IDCT ownership absent");
        b.abort_and_drain(false);need(!b.d.inverse_busy&&b.d.inverse_owned_banks==0,"IDCT cancel retained local owner");pass("abort_owned_idct_job");
        // A late inner-CRC failure must not poison a clean retry without reset.
        b.prepare(*late,0,false);b.preload(*late);b.begin(*late);b.feed_until();need(b.d.error==147&&!b.d.done,"late failure setup");b.settle();
        b.prepare(*good,0,false);b.preload(*good);b.begin(*good);b.feed_until();need(b.d.done&&b.d.error==0,"good retry after late failure");b.settle();pass("good_retry_after_failed_frame_without_reset");
        // Abort an incomplete trusted snapshot load; the interface must recover.
        b.prepare(*delta,0,false);b.d.cache_valid=1;b.d.cache_data=0;b.d.cache_last=0;b.d.cache_ref_fid=delta->cache_fid;b.d.cache_ref_generation=delta->cache_gen;
        for(unsigned k=0;k<9;++k){b.tick();}b.d.cache_valid=0;b.d.abort_packet=1;b.tick();b.d.abort_packet=0;b.tick();need(b.d.start_ready&&!b.d.cache_complete,"partial cache abort stranded ownership");pass("partial_cache_load_abort_releases_owner");
        // A consumed/overwritten qcache cannot authorize a later inherited map.
        b.prepare(*delta,0,false);b.preload(*delta);b.begin(*delta);b.abort_and_drain(false);
        auto missing=*delta;missing.error=7;b.prepare(missing,0,false);b.begin(missing);b.feed_until();need(b.d.error==7&&b.d.core_starts==0,"consumed qcache reused");b.settle();pass("one_shot_cache_requires_fresh_preload");
        // Reserved/stale frame epoch rejects before decoder side effects.
        b.prepare(*good,0,false);b.begin(*good,0);b.feed_until();need(b.d.error==65&&b.d.core_starts==0,"zero frame epoch accepted");b.settle();pass("zero_frame_epoch_rejected");
        pass("snapshot_inputs_latched_every_case");pass("serial_cache_tag_latched_first_byte");pass("all_coefficients_and_mapped_tuple_fields_exact");
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"refill_overlap\":"<<REFILL_OVERLAP<<",\"vectors\":"<<cases.size()<<",\"cases\":"<<rows<<",\"configurations\":2,\"directed_checks\":"<<checks.size()<<",\"dense_comparisons\":"<<b.dense_comparisons<<",\"assembly_comparisons\":"<<b.assembly_comparisons<<",\"dequant_comparisons\":"<<b.dq_comparisons<<",\"residual_comparisons\":"<<b.residual_comparisons<<",\"directed_dense_comparisons\":"<<b.directed_comparisons<<",\"tile_rows\":"<<b.tiles<<",\"directed_check_names\":[";
        for(size_t k=0;k<checks.size();++k){if(k)std::cout<<',';std::cout<<quote(checks[k]);}std::cout<<"]}\n";return 0;
    }catch(const std::exception &e){std::cerr<<"V91J_TEST_FAIL "<<e.what()<<'\n';return 1;}
}
