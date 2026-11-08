#ifdef V91E_LEGACY
#include "Vbr88_pipeline.h"
using Pipeline=Vbr88_pipeline;
#else
#include "Vingress_probe.h"
using Pipeline=Vingress_probe;
#endif
#include "verilated.h"
#ifndef SYNC_STAGING
#define SYNC_STAGING 1
#endif
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <sstream>
#include <string>
#include <vector>

static void require(bool value,const std::string& message) { if(!value) throw std::runtime_error(message); }
static std::vector<uint8_t> hexbytes(const std::string& s) {
    require(s.size()%2==0,"odd hex length"); std::vector<uint8_t> data;
    for(size_t i=0;i<s.size();i+=2) data.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));
    return data;
}
struct Case {std::string id;unsigned blocks=0;std::vector<uint8_t> packet,dense,packed;};
struct Telemetry {
    uint64_t cycles=0;
    uint64_t stage_reads=0,stage_responses=0,stage_writes=0,stage_wait=0,stage_word_hold=0,stage_buffer_max=0;
    std::array<uint64_t,4> stage_reads_by_purpose{};
    std::array<uint64_t,4> emitter{};
    uint64_t max_tile_owned=0,max_tile_ready=0,tile_starts=0,tile_publishes=0,tile_releases=0;
    uint64_t prepare_output_overlap=0,prepare_output_hold=0,tile_read_output_overlap=0,tile_bank_wait=0,both_ready_wait=0,tile_prep_done_wait=0,publish_release_same_edge=0,output_valid=0;
    std::array<uint64_t,16> packet{};
    std::array<uint64_t,32> scratch{};
    std::array<uint64_t,4> coefficients{},band_ends{},first_coef_band{},last_coef_band{},band_end{};
    uint64_t max_assembly=0,max_cache=0,max_head=0,max_outstanding=0,max_write_slot=0,max_owned_lines=0,max_prefetch_offer=0;
    uint64_t write_enqueues=0,write_accepts=0,write_acks=0,full_wait=0,packing_during_write_pending=0;
    uint64_t prefetch_offers=0,prefetch_accepts=0,prefetch_acks=0,prefetch_uses=0,dense_during_read_pending=0,prefetch_drain_wait=0;
    uint64_t coef_stall=0,metadata_wait=0,band_end_stall=0,mem_req_stall=0,mem_pending=0,input_starved=0;
    uint64_t first_input=0,last_input=0,metadata_accept=0,last_sparse_coef=0,packet_done_observed=0;
    uint64_t seal_accepted=0,scratch_sealed_observed=0,first_dense=0,last_dense=0,integrated_done=0;
};
struct Counts {uint64_t cycles=0,input=0,dense=0,reads=0,writes=0,stalls=0,metadata_wait=0,memory_wait=0;
    uint64_t request_service_hash=1469598103934665603ULL,request_multiset_hash=0,ordered_write_service_hash=1469598103934665603ULL,read_once_lines=0,write_once_lines=0;Telemetry telemetry;};
struct Edge {bool input,output,request,response;unsigned block,index,epoch;int value;};
static void checksum(std::vector<uint8_t>& data) {
    uint32_t crc=0xffffffffU;
    for(size_t i=0;i<data.size()-4;++i) {
        crc^=data[i];for(unsigned bit=0;bit<8;++bit)crc=(crc>>1)^((crc&1)?0xedb88320U:0);
    }
    crc^=0xffffffffU;
    for(unsigned i=0;i<4;++i)data[data.size()-4+i]=uint8_t(crc>>(8*i));
}
static Case oversized_scratch() {
    Case c;c.id="valid-coded-over-budget";c.blocks=8192;
    const std::array<unsigned,4> bits{8192,81920,50000,0};
    const std::array<unsigned,3> counts{40960,25000,0};
    unsigned bytes=46;
    for(unsigned size:bits)bytes+=6+(size+7)/8;
    c.packet.assign(bytes,0);
    auto put=[&](unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)c.packet[at+j]=uint8_t(value>>(8*j));};
    c.packet[0]='B';c.packet[1]='R';c.packet[2]='8';c.packet[3]='8';c.packet[4]=1;
    put(6,c.blocks);c.packet[10]=1;
    for(unsigned j=0;j<3;++j)put(30+4*j,counts[j]);
    unsigned at=42;
    for(unsigned band=0;band<4;++band) {
        unsigned size=6+(bits[band]+7)/8;put(14+4*band,size);
        c.packet[at+1]=band==0?255:0;put(at+2,bits[band]);
        for(unsigned j=0;j<(bits[band]+7)/8;++j)c.packet[at+6+j]=0xff;
        at+=size;
    }
    checksum(c.packet);return c;
}

static Case zero_tiles(unsigned blocks) {
    Case c;c.id="directed:tile-zero"+std::to_string(blocks);c.blocks=blocks;
    const unsigned dcbytes=(blocks+7)/8,dcsize=6+dcbytes;
    c.packet.assign(42+dcsize+18+4,0);
    auto put=[&](unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)c.packet[at+j]=uint8_t(value>>(8*j));};
    c.packet[0]='B';c.packet[1]='R';c.packet[2]='8';c.packet[3]='8';c.packet[4]=1;put(6,blocks);c.packet[10]=1;
    put(14,dcsize);for(unsigned j=1;j<4;++j)put(14+4*j,6);
    c.packet[43]=255;put(44,blocks);
    for(unsigned j=0;j<dcbytes;++j)c.packet[48+j]=0xff;
    if(blocks%8)c.packet[48+dcbytes-1]=uint8_t(0xffU<<(8-blocks%8));
    checksum(c.packet);c.dense.assign(blocks*128,0);
    c.packed.assign(32+((blocks*2+15)&~15U),0);
    auto packed_put=[&](unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)c.packed[at+j]=uint8_t(value>>(8*j));};
    packed_put(0,0x43393150);packed_put(4,blocks);packed_put(24,c.packed.size());
    return c;
}

class Sim {
public:
    Pipeline d;
    Telemetry telemetry;
    std::ofstream tile_stream;
    bool record_tiles=false;
    uint64_t request_service_hash=1469598103934665603ULL,request_multiset_hash=0,ordered_write_service_hash=1469598103934665603ULL;
    std::array<unsigned,16384> read_visits{},write_visits{};
    std::array<uint8_t,262144> ram{};
    std::array<uint32_t,16384> line_epoch{};
    struct Request {bool valid=false,write=false;unsigned address=0,epoch=0;std::array<uint32_t,4> data{};uint64_t due=0,accepted=0;} pending;
    uint64_t cycle=0,rng=1,seed;
    std::string current_case;
    uint32_t next_epoch=0,current_epoch=0,current_blocks=0,current_packet_bytes=0;
    std::array<uint8_t,49152> staging_bytes{};
    std::array<uint32_t,49152> staging_epochs{};
    bool staging_pending=false,coef_held=false,stage_cancel_pending_witness=false;
    unsigned held_coef_band=0,held_coef_block=0,held_coef_index=0,held_coef_epoch=0;
    int held_coef_value=0;
    uint32_t staging_address=0,staging_epoch=0;
    uint64_t staging_due=0;
    bool slow=false,overlap=false,prefetch=false,tile_overlap=false,req_held=false,out_held=false;
    std::array<uint32_t,4> old_req_data{};
    unsigned old_req_address=0,old_req_epoch=0;bool old_req_write=false;
    unsigned old_block=0,old_index=0,old_epoch=0;int old_value=0;
    uint64_t min_response_delay=~uint64_t(0),max_response_delay=0;
    unsigned injected_error=0;
    bool force_request_stall=false,inject_stale_response=false;

    explicit Sim(uint64_t s):seed(s) {
        ram.fill(0xa5);line_epoch.fill(0xffffffffU);
        d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=0;d.blocks=0;d.epoch=0;
        d.serial_clear=0;d.write_overlap=0;d.read_prefetch=0;d.tile_overlap=0;d.in_valid=0;d.in_data=0;d.in_last=0;d.out_ready=0;
        d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;
        for(unsigned j=0;j<4;++j)d.mem_rsp_data[j]=0;
        step(true);d.reset=0;
    }
    uint32_t random(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint32_t(rng);}

#ifndef V91E_LEGACY
    void observe_staging() {
        if constexpr(SYNC_STAGING!=0) {
            if(d.stage_cancel){staging_pending=false;return;}
            auto& t=telemetry;
            require(bool(d.stage_pending)==staging_pending,"staging one-read owner");
            require(!(d.stage_write&&d.stage_read_req),"staging write/read overlap");
            if(d.stage_write) {
                require(d.in_valid&&d.in_ready&&d.stage_write_addr<current_packet_bytes,"staging accepted byte write");
                staging_bytes.at(d.stage_write_addr)=d.stage_write_data;
                staging_epochs.at(d.stage_write_addr)=current_epoch;++t.stage_writes;
            }
            if(d.stage_read_rsp) {
                require(staging_pending&&cycle==staging_due,"staging response not one edge after request");
                require(d.stage_rsp_addr==staging_address&&d.stage_rsp_epoch==staging_epoch,"staging response ownership");
                require(d.stage_read_data==staging_bytes.at(staging_address),"staging synchronous read data");
                staging_pending=false;++t.stage_responses;
            }
            if(d.stage_read_req) {
                require(!staging_pending&&!d.stage_write&&d.stage_read_addr<current_packet_bytes,"staging read request bound");
                require(staging_epochs.at(d.stage_read_addr)==current_epoch&&d.stage_req_epoch==current_epoch,"staging read from stale packet");
                staging_pending=true;staging_address=d.stage_read_addr;staging_epoch=d.stage_req_epoch;staging_due=cycle+1;
                ++t.stage_reads;++t.stage_reads_by_purpose.at(d.stage_purpose);
            }
            if(d.packet_state==13)++t.stage_wait;
            if(d.stage_word_valid&&!d.stage_word_ready)++t.stage_word_hold;
            t.stage_buffer_max=std::max(t.stage_buffer_max,uint64_t(d.stage_buffer_bytes));
            require(t.stage_buffer_max<=46,"staging cache bound");
        } else {
            require(!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_write,"legacy generate exposes staging traffic");
        }
    }
    void observe() {
        observe_staging();
        auto& t=telemetry;const uint64_t edge=++t.cycles;
        require(d.dbg_running,"telemetry sampled outside running edge");
        ++t.emitter.at(d.dbg_emitter_state);
        const auto population=[](unsigned bits){uint64_t n=0;for(;bits;bits>>=1)n+=bits&1;return n;};
        const unsigned emitter_state=!d.dbg_tile_mode?3:!d.out_valid?0:d.out_ready?1:2;
        require(d.dbg_emitter_state==emitter_state,"independent emitter state");
        t.max_tile_owned=std::max(t.max_tile_owned,population(d.dbg_bank_owned));
        t.max_tile_ready=std::max(t.max_tile_ready,population(d.dbg_bank_ready));
        if(d.dbg_tile_prepare_start)++t.tile_starts;
        if(d.dbg_tile_publish)++t.tile_publishes;
        if(d.dbg_tile_release)++t.tile_releases;
        if(d.dbg_tile_preparing&&d.out_valid&&d.out_ready)++t.prepare_output_overlap;
        if(d.dbg_tile_preparing&&d.out_valid&&!d.out_ready)++t.prepare_output_hold;
        if(d.dbg_tile_mode&&pending.valid&&!pending.write&&d.out_valid&&d.out_ready)++t.tile_read_output_overlap;
        if(d.dbg_tile_mode&&d.dbg_scratch_state==28)++t.tile_bank_wait;
        if(d.dbg_tile_mode&&d.dbg_scratch_state==28&&d.dbg_bank_ready==3)++t.both_ready_wait;
        if(d.dbg_tile_mode&&d.dbg_scratch_state==29)++t.tile_prep_done_wait;
        if(d.dbg_tile_publish&&d.dbg_tile_release)++t.publish_release_same_edge;
        if(d.out_valid)++t.output_valid;
        require(t.max_tile_owned<=2&&t.max_tile_ready<=2,"bounded tile ownership");
        require(!d.dbg_tile_preparing||!(d.dbg_bank_ready&(1U<<d.dbg_prepare_bank)),"producer owns emitted/ready bank");
        for(unsigned b=0;b<2;++b)if(d.dbg_bank_ready&(1U<<b))
            require(d.dbg_bank_epoch[b]==current_epoch&&d.dbg_bank_block[b]<current_blocks,"tile bank epoch owner");
        ++t.packet.at(d.packet_state);++t.scratch.at(d.dbg_scratch_state);
        // Independent external pending ownership agrees with the scratch flag.
        require(bool(d.dbg_scratch_outstanding)==pending.valid,"scratch outstanding ownership");
        if(pending.valid)++t.mem_pending;
        t.max_prefetch_offer=std::max(t.max_prefetch_offer,uint64_t(d.dbg_prefetch_offer));
        if(d.dbg_prefetch_launch)++t.prefetch_offers;
        if(d.dbg_prefetch_offer&&d.mem_req_valid&&d.mem_req_ready)++t.prefetch_accepts;
        if(d.dbg_prefetch_offer&&pending.valid&&d.mem_rsp_valid&&d.mem_rsp_epoch==pending.epoch&&!d.mem_rsp_error)++t.prefetch_acks;
        if(d.dbg_prefetch_use)++t.prefetch_uses;
        if(d.dbg_prefetch_offer&&pending.valid&&d.out_valid&&d.out_ready)++t.dense_during_read_pending;
        if(d.dbg_scratch_state==27)++t.prefetch_drain_wait;
        t.max_write_slot=std::max(t.max_write_slot,uint64_t(d.dbg_write_slot_valid));
        t.max_owned_lines=std::max(t.max_owned_lines,uint64_t(d.dbg_write_slot_valid)+uint64_t(d.dbg_scratch_assembly_bytes!=0));
        if(d.dbg_write_enqueue)++t.write_enqueues;
        if(d.dbg_write_slot_valid&&d.mem_req_valid&&d.mem_req_ready)++t.write_accepts;
        if(d.dbg_write_slot_valid&&pending.valid&&d.mem_rsp_valid&&d.mem_rsp_epoch==pending.epoch)++t.write_acks;
        if(d.dbg_scratch_state==26)++t.full_wait;
        if(pending.valid&&pending.write&&(d.dbg_scratch_state==1||d.dbg_scratch_state==2))++t.packing_during_write_pending;
        require(t.max_owned_lines<=2&&t.max_write_slot<=1,"bounded overlap ownership");
        require(!d.dbg_assembler_full||!d.dbg_coef_ready,"full assembler accepted producer");
        if(d.dbg_seal_valid&&d.dbg_seal_ready)require(!pending.valid&&!d.dbg_write_slot_valid&&!d.dbg_scratch_assembly_bytes,"seal before write drain");
        t.max_assembly=std::max(t.max_assembly,uint64_t(d.dbg_scratch_assembly_bytes));
        t.max_cache=std::max(t.max_cache,population(d.dbg_scratch_cache_valid));
        t.max_head=std::max(t.max_head,population(d.dbg_scratch_head_valid));
        t.max_outstanding=std::max(t.max_outstanding,uint64_t(pending.valid));
        require(t.max_assembly<=16&&t.max_cache<=4&&t.max_head<=3&&t.max_outstanding<=1,"bounded local storage highwater");
        if(d.dbg_coef_valid&&!d.dbg_coef_ready)++t.coef_stall;
        if(d.dbg_meta_valid&&!d.dbg_meta_ready)++t.metadata_wait;
        if(d.dbg_band_end_valid&&!d.dbg_band_end_ready)++t.band_end_stall;
        if(d.mem_req_valid&&!d.mem_req_ready)++t.mem_req_stall;
        if(d.in_ready&&!d.in_valid)++t.input_starved;
        if(d.in_valid&&d.in_ready){if(!t.first_input)t.first_input=edge;t.last_input=edge;}
        if(d.dbg_meta_valid&&d.dbg_meta_ready)t.metadata_accept=edge;
        if(d.dbg_coef_valid&&d.dbg_coef_ready){
            const unsigned band=d.dbg_coef_band;++t.coefficients.at(band);t.last_sparse_coef=edge;
            if(!t.first_coef_band.at(band))t.first_coef_band.at(band)=edge;
            t.last_coef_band.at(band)=edge;
        }
        if(d.dbg_band_end_valid&&d.dbg_band_end_ready){++t.band_ends.at(d.dbg_band_end_band);t.band_end.at(d.dbg_band_end_band)=edge;}
        if(d.dbg_packet_done&&!t.packet_done_observed)t.packet_done_observed=edge;
        if(d.dbg_seal_valid&&d.dbg_seal_ready)t.seal_accepted=edge;
        if(d.scratch_sealed&&!t.scratch_sealed_observed)t.scratch_sealed_observed=edge;
        if(d.out_valid&&d.out_ready){if(!t.first_dense)t.first_dense=edge;t.last_dense=edge;}
    }
    void check_telemetry(bool success) {
        const auto& t=telemetry;uint64_t packet_sum=0,scratch_sum=0;
        for(unsigned i=0;i<t.packet.size();++i){require(t.packet[i]==d.count_packet_state[i],"packet state histogram");packet_sum+=t.packet[i];}
        for(unsigned i=0;i<t.scratch.size();++i){require(t.scratch[i]==d.count_scratch_state[i],"scratch state histogram");scratch_sum+=t.scratch[i];}
        require(packet_sum==d.count_cycles&&scratch_sum==d.count_cycles&&t.cycles==d.count_cycles,"state histogram cycle reconciliation");
#define CHECK_TELEMETRY(cpp,rtl) require(t.cpp==d.rtl,std::string("RTL telemetry mismatch " #cpp)+" expected="+std::to_string(t.cpp)+" actual="+std::to_string(d.rtl)+" case="+current_case)
        for(unsigned i=0;i<4;++i)require(t.emitter[i]==d.count_emitter_state[i],"emitter histogram");
        require(t.emitter[0]+t.emitter[1]+t.emitter[2]+t.emitter[3]==t.cycles,"emitter histogram cycle reconciliation");
        CHECK_TELEMETRY(stage_reads,count_stage_reads);CHECK_TELEMETRY(stage_responses,count_stage_responses);
        CHECK_TELEMETRY(stage_writes,count_stage_writes);CHECK_TELEMETRY(stage_wait,count_stage_fetch_wait);
        CHECK_TELEMETRY(stage_word_hold,count_stage_word_hold);
        require(t.stage_buffer_max==d.stage_buffer_highwater,"staging buffer highwater");
        CHECK_TELEMETRY(max_tile_owned,max_tile_owned);CHECK_TELEMETRY(max_tile_ready,max_tile_ready);
        CHECK_TELEMETRY(tile_starts,count_tile_starts);CHECK_TELEMETRY(tile_publishes,count_tile_publishes);CHECK_TELEMETRY(tile_releases,count_tile_releases);
        CHECK_TELEMETRY(prepare_output_overlap,count_prepare_output_overlap);CHECK_TELEMETRY(prepare_output_hold,count_prepare_output_hold);
        CHECK_TELEMETRY(tile_read_output_overlap,count_tile_read_output_overlap);CHECK_TELEMETRY(tile_bank_wait,count_tile_bank_wait);
        CHECK_TELEMETRY(both_ready_wait,count_both_ready_wait);CHECK_TELEMETRY(tile_prep_done_wait,count_tile_prep_done_wait);
        CHECK_TELEMETRY(publish_release_same_edge,count_publish_release_same_edge);CHECK_TELEMETRY(output_valid,count_output_valid);
        CHECK_TELEMETRY(max_assembly,max_assembly_bytes);CHECK_TELEMETRY(max_cache,max_cache_valid);
        CHECK_TELEMETRY(max_head,max_head_valid);CHECK_TELEMETRY(max_outstanding,max_outstanding);
        CHECK_TELEMETRY(max_prefetch_offer,max_prefetch_offer);
        CHECK_TELEMETRY(prefetch_offers,count_prefetch_offers);CHECK_TELEMETRY(prefetch_accepts,count_prefetch_accepts);
        CHECK_TELEMETRY(prefetch_acks,count_prefetch_acks);CHECK_TELEMETRY(prefetch_uses,count_prefetch_uses);
        CHECK_TELEMETRY(dense_during_read_pending,count_dense_during_read_pending);CHECK_TELEMETRY(prefetch_drain_wait,count_prefetch_drain_wait);
        CHECK_TELEMETRY(max_write_slot,max_write_slot);CHECK_TELEMETRY(max_owned_lines,max_owned_lines);
        CHECK_TELEMETRY(write_enqueues,count_write_enqueues);CHECK_TELEMETRY(write_accepts,count_write_accepts);
        CHECK_TELEMETRY(write_acks,count_write_acks);CHECK_TELEMETRY(full_wait,count_full_wait);
        CHECK_TELEMETRY(packing_during_write_pending,count_packing_during_write_pending);
        for(unsigned b=0;b<4;++b) {
            require(t.first_coef_band[b]==d.ts_first_coef_band[b]&&t.last_coef_band[b]==d.ts_last_coef_band[b]&&
                t.band_end[b]==d.ts_band_end[b],"per-band event timestamps");
        }
        CHECK_TELEMETRY(coef_stall,count_coef_stall);CHECK_TELEMETRY(metadata_wait,count_metadata_wait);
        CHECK_TELEMETRY(band_end_stall,count_band_end_stall);CHECK_TELEMETRY(mem_req_stall,count_mem_req_stall);
        CHECK_TELEMETRY(mem_pending,count_mem_pending);CHECK_TELEMETRY(input_starved,count_input_starved);
        CHECK_TELEMETRY(first_input,ts_first_input);CHECK_TELEMETRY(last_input,ts_last_input);
        CHECK_TELEMETRY(metadata_accept,ts_metadata_accept);CHECK_TELEMETRY(last_sparse_coef,ts_last_sparse_coef);
        CHECK_TELEMETRY(packet_done_observed,ts_packet_done_observed);CHECK_TELEMETRY(seal_accepted,ts_seal_accepted);
        CHECK_TELEMETRY(scratch_sealed_observed,ts_scratch_sealed_observed);
        CHECK_TELEMETRY(first_dense,ts_first_dense);CHECK_TELEMETRY(last_dense,ts_last_dense);CHECK_TELEMETRY(integrated_done,ts_integrated_done);
#undef CHECK_TELEMETRY
        if(success) {
            require(t.scratch[0]>0,"pre-allocation scratch IDLE omitted");
            const unsigned bands=d.dbg_meta_raw?1:4;
            for(unsigned b=0;b<4;++b) {
                require(t.band_ends[b]==unsigned(b<bands),"context end count");
                require(bool(t.coefficients[b])==bool(t.first_coef_band[b])&&
                    bool(t.coefficients[b])==bool(t.last_coef_band[b]),"empty context coefficient timestamps");
                if(t.coefficients[b]) require(t.first_coef_band[b]<=t.last_coef_band[b]&&t.last_coef_band[b]<t.band_end[b],"per-band acceptance fence");
            }
            require(t.first_input&&t.first_input<=t.last_input&&t.last_input<=t.metadata_accept&&
                t.metadata_accept<=t.last_sparse_coef&&t.last_sparse_coef<=t.packet_done_observed&&
                t.packet_done_observed<=t.seal_accepted&&t.seal_accepted<t.scratch_sealed_observed&&
                t.scratch_sealed_observed<=t.first_dense&&t.first_dense<=t.last_dense&&
                t.last_dense<t.integrated_done&&t.integrated_done==t.cycles,"successful event fence ordering");
        }
    }
#endif
    Edge step(bool offer=true) {
        d.mem_req_ready=!force_request_stall&&!pending.valid&&(!slow||offer);
        d.mem_rsp_valid=pending.valid&&(cycle>=pending.due||inject_stale_response);
        d.mem_rsp_epoch=pending.epoch+unsigned(inject_stale_response);d.mem_rsp_error=d.mem_rsp_valid&&injected_error;
        for(unsigned j=0;j<4;++j) {
            uint32_t value=0;
            if(pending.valid&&!pending.write)for(unsigned b=0;b<4;++b)value|=uint32_t(ram[pending.address+4*j+b])<<(8*b);
            d.mem_rsp_data[j]=value;
        }
        d.clk=0;d.eval();bool cancel=d.reset||d.start||d.abort_packet;
        if(cancel)require(!d.out_valid&&!d.in_ready,"cancel edge accepted output/input");
        if constexpr(SYNC_STAGING!=0){if(d.stage_cancel){
            if(staging_pending&&d.stage_context_active&&!cancel)stage_cancel_pending_witness=true;
            staging_pending=false;}}
        if(coef_held&&!d.stage_cancel&&!cancel)require(d.dbg_coef_valid&&d.dbg_coef_band==held_coef_band&&
            d.dbg_coef_block==held_coef_block&&d.dbg_coef_index==held_coef_index&&int16_t(d.dbg_coef_value)==held_coef_value&&
            d.dbg_coef_epoch==held_coef_epoch,"held sparse coefficient changed during RAM fetch");
        coef_held=d.dbg_coef_valid&&!d.dbg_coef_ready&&!d.stage_cancel&&!cancel;
        held_coef_band=d.dbg_coef_band;held_coef_block=d.dbg_coef_block;held_coef_index=d.dbg_coef_index;
        held_coef_value=int16_t(d.dbg_coef_value);held_coef_epoch=d.dbg_coef_epoch;
        if(req_held&&!cancel) {
            require(d.mem_req_valid,"held memory request dropped");
            require(d.mem_req_write==old_req_write&&d.mem_req_addr==old_req_address&&d.mem_req_epoch==old_req_epoch,"held memory request fields changed");
            for(unsigned j=0;j<4;++j)require(d.mem_req_data[j]==old_req_data[j],"held memory request data changed");
        }
        const bool failing_response=d.mem_rsp_valid&&(d.mem_rsp_error||d.mem_rsp_epoch!=pending.epoch);
        if(out_held&&!cancel&&!failing_response)require(d.out_valid&&d.out_block==old_block&&d.out_index==old_index&&
            int16_t(d.out_value)==old_value&&d.out_epoch==old_epoch,"held dense output changed");
        req_held=d.mem_req_valid&&!d.mem_req_ready&&!cancel;
        old_req_address=d.mem_req_addr;old_req_epoch=d.mem_req_epoch;old_req_write=d.mem_req_write;
        for(unsigned j=0;j<4;++j)old_req_data[j]=d.mem_req_data[j];
        out_held=d.out_valid&&!d.out_ready&&!cancel;
        old_block=d.out_block;old_index=d.out_index;old_epoch=d.out_epoch;old_value=int16_t(d.out_value);
        Edge e{bool(d.in_valid&&d.in_ready),bool(d.out_valid&&d.out_ready),
            bool(d.mem_req_valid&&d.mem_req_ready),bool(d.mem_rsp_valid&&d.mem_rsp_ready),
            d.out_block,d.out_index,d.out_epoch,int16_t(d.out_value)};
#ifndef V91E_LEGACY
        const bool observed=!cancel&&d.dbg_running;
        if(observed)observe();
#endif
        Request accepted;
        if(e.request) {
            require(!pending.valid,"more than one outstanding memory request");
            require((d.mem_req_addr&15)==0&&d.mem_req_addr+16<=d.used_bytes,"memory address bound");
            accepted.valid=true;accepted.write=d.mem_req_write;accepted.address=d.mem_req_addr;accepted.epoch=d.mem_req_epoch;
            for(unsigned j=0;j<4;++j)accepted.data[j]=d.mem_req_data[j];
            // Epochs differ between trials for ownership safety; service cost
            // depends on address and seed only so A/B memory traces match.
            unsigned latency=slow?(accepted.write?16:18)+unsigned(((accepted.address>>4)^seed)&3):1;
            accepted.due=cycle+latency;accepted.accepted=cycle;
            uint64_t token=1469598103934665603ULL;
            auto hash_word=[&](uint64_t value){for(unsigned b=0;b<8;++b){
                request_service_hash^=uint8_t(value>>(8*b));request_service_hash*=1099511628211ULL;
                token^=uint8_t(value>>(8*b));token*=1099511628211ULL;
                if(accepted.write){ordered_write_service_hash^=uint8_t(value>>(8*b));ordered_write_service_hash*=1099511628211ULL;}}};
            hash_word(accepted.write);hash_word(accepted.address);hash_word(latency);
            if(accepted.write)for(unsigned j=0;j<4;++j)hash_word(accepted.data[j]);
            request_multiset_hash+=token;
            if(accepted.write) require(++write_visits.at(accepted.address/16)==1,"duplicate write line");
            else require(++read_visits.at(accepted.address/16)==1,"duplicate read line");
            if(!accepted.write) {
                require(line_epoch[accepted.address/16]==accepted.epoch,"read from unwritten/stale memory line");
                require(d.scratch_sealed&&d.packet_state==7,"memory read before full packet/store validation");
            }
        }
        ingress_pre(d);d.clk=1;d.eval();ingress_post(d);d.clk=0;d.eval();
#ifndef V91E_LEGACY
        if(observed&&d.done)telemetry.integrated_done=telemetry.cycles;
#endif
        if(e.response&&!inject_stale_response) {
            require(pending.valid,"response without outstanding request");
            uint64_t delay=cycle-pending.accepted;
            require(delay>=1,"zero latency memory response");
            min_response_delay=std::min(min_response_delay,delay);max_response_delay=std::max(max_response_delay,delay);
            // Writes take effect only at their delayed acknowledgement. Reset
            // and abort never remove this pending external side effect.
            if(pending.write) {
                for(unsigned j=0;j<4;++j)for(unsigned b=0;b<4;++b)ram[pending.address+4*j+b]=uint8_t(pending.data[j]>>(8*b));
                line_epoch[pending.address/16]=pending.epoch;
            }
            pending.valid=false;injected_error=0;
        }
        if(e.request)pending=accepted;
        // The external driver withdraws a consumed response after its edge.
        // Keep the recorded edge intact, then settle combinational public pins;
        // retaining valid with the old payload after ownership retired would
        // look like an unsolicited second response until the next step.
        if(e.response){d.mem_rsp_valid=0;d.mem_rsp_error=0;d.eval();}
        inject_stale_response=false;
        ++cycle;return e;
    }

    std::string public_snapshot() const {
        std::ostringstream o;
        o<<"pending="<<pending.valid<<" rsp="<<unsigned(d.mem_rsp_valid)<<" outstanding="<<unsigned(d.dbg_scratch_outstanding)
         <<" valid="<<unsigned(d.out_valid)<<" tuple="<<d.out_block<<":"<<unsigned(d.out_index)<<":"<<int16_t(d.out_value)<<":"<<d.out_epoch
         <<" state="<<unsigned(d.dbg_scratch_state)<<" error="<<unsigned(d.error)<<" ready="<<unsigned(d.dbg_bank_ready)
         <<" prep="<<unsigned(d.dbg_prepare_bank)<<":"<<d.dbg_prepare_block<<" emit="<<unsigned(d.dbg_emit_bank)
         <<" bank0="<<d.dbg_bank_block[0]<<":"<<d.dbg_bank_epoch[0]<<" bank1="<<d.dbg_bank_block[1]<<":"<<d.dbg_bank_epoch[1];
        return o.str();
    }

    void start(const Case& c,bool clear) {
        telemetry=Telemetry{};request_service_hash=1469598103934665603ULL;request_multiset_hash=0;ordered_write_service_hash=1469598103934665603ULL;read_visits.fill(0);write_visits.fill(0);
        current_case=c.id;current_epoch=++next_epoch;current_blocks=c.blocks;current_packet_bytes=c.packet.size();staging_pending=false;stage_cancel_pending_witness=false;
        d.in_valid=0;d.out_ready=0;d.packet_bytes=c.packet.size();d.blocks=c.blocks;d.epoch=current_epoch;d.serial_clear=clear;d.write_overlap=overlap;d.read_prefetch=prefetch;d.tile_overlap=tile_overlap;
        d.start=1;step();d.start=0;
        require(!d.done&&!d.error&&d.count_cycles==0,"start status/counter flush");
        d.packet_bytes=0;d.blocks=0;d.epoch=0;d.serial_clear=!clear;d.write_overlap=!overlap;d.read_prefetch=!prefetch;d.tile_overlap=!tile_overlap;
    }

    Counts run(const Case& c,bool clear,bool delayed,unsigned expected_error=0,bool check_image=true) {
        slow=delayed;rng=1469598103934665603ULL;
        for(unsigned char ch:c.id){rng^=ch;rng*=1099511628211ULL;}rng^=seed;if(!rng)rng=1;
        start(c,clear);Counts n;size_t supplied=0,produced=0;bool held=false;uint64_t tile_first=0;
        // Include all bytes, allocator credit, write ACKs, descriptor readback,
        // tile clearing/merge, finite read service and final dense delivery.
        uint64_t watchdog=50000000ULL+uint64_t(c.blocks)*400;
        while(!d.done&&!d.error) {
            require(++n.cycles<watchdog,"pipeline watchdog "+c.id);
            bool offer=random()%4!=0,ready=random()%4!=0,memready=random()%4!=0;
            if(!held&&supplied<c.packet.size()&&(!delayed||offer)) {
                d.in_data=c.packet[supplied];d.in_last=supplied+1==c.packet.size();held=true;
            }
            d.in_valid=held;d.out_ready=!delayed||ready;d.eval();
            if(d.out_valid&&!d.out_ready)++n.stalls;
            if(d.metadata_wait)++n.metadata_wait;
            if(pending.valid)++n.memory_wait;
            Edge e=step(memready);
            if(e.input){++supplied;++n.input;held=false;}
            if(e.request){if(old_req_write)++n.writes;else ++n.reads;}
            if(e.output) {
                require(expected_error==0,"dense output before expected failure "+c.id);
                require(produced+1<c.dense.size(),"excess dense output "+c.id);
                int value=int16_t(unsigned(c.dense[produced])|(unsigned(c.dense[produced+1])<<8));
                require(e.block==produced/128&&e.index==(produced/2)%64&&e.value==value&&e.epoch==current_epoch,
                    "dense coefficient/epoch mismatch "+c.id+" at "+std::to_string(produced/2));
                if(e.index==0)tile_first=n.cycles;
                if(record_tiles&&tile_stream.is_open()&&e.index==63) {
                    tile_stream<<"{\"id\":\""<<c.id<<"\",\"serial_clear\":"<<clear<<",\"memory_profile\":"<<delayed
                        <<",\"write_overlap\":"<<overlap<<",\"read_prefetch\":"<<prefetch<<",\"tile_overlap\":"<<tile_overlap<<",\"sync_staging\":"<<SYNC_STAGING<<",\"block\":"<<e.block<<",\"first_dense\":"<<tile_first<<",\"last_dense\":"<<n.cycles<<"}\n";
                    require(bool(tile_stream),"tile event write failure");
                }
                produced+=2;++n.dense;
            }
        }
        require(d.error==expected_error,"pipeline error "+c.id+" got "+std::to_string(d.error)+" expected "+std::to_string(expected_error));
        require(bool(d.done)==(expected_error==0),"pipeline completion status "+c.id);
        if(!expected_error) {
            require(produced==c.dense.size()&&supplied==c.packet.size(),"packet/dense completion counts");
            require(d.used_bytes==c.packed.size()&&!pending.valid,"used bytes or final memory ACK");
            require(n.reads==n.writes&&n.writes==c.packed.size()/16,"packed burst accounting "+c.id);
            for(unsigned line=0;line<c.packed.size()/16;++line) {
                require(read_visits.at(line)==1&&write_visits.at(line)==1,"per-line traffic coverage");
                ++n.read_once_lines;++n.write_once_lines;
            }
            require(telemetry.prefetch_offers==telemetry.prefetch_accepts&&telemetry.prefetch_accepts==telemetry.prefetch_acks&&
                telemetry.prefetch_acks==telemetry.prefetch_uses,"prefetch offered/accepted/ACKed/used exactness");
            require(telemetry.output_valid==n.dense+n.stalls,"independent valid output reconciliation");
            if(tile_overlap&&!d.dbg_meta_raw)require(telemetry.tile_starts==c.blocks&&telemetry.tile_publishes==c.blocks&&telemetry.tile_releases==c.blocks,"tile bank lifecycle count");
            if(check_image)require(std::equal(c.packed.begin(),c.packed.end(),ram.begin()),"packed memory image mismatch "+c.id);
        }
        require(d.count_cycles==n.cycles&&d.count_input_bytes==n.input&&d.count_dense==n.dense&&
            d.count_reads==n.reads&&d.count_writes==n.writes&&d.count_dense_stall==n.stalls,"integrated counters "+c.id);
#ifndef V91E_LEGACY
        check_telemetry(!expected_error);n.telemetry=telemetry;
#endif
        n.request_service_hash=request_service_hash;n.request_multiset_hash=request_multiset_hash;n.ordered_write_service_hash=ordered_write_service_hash;
        d.in_valid=0;d.out_ready=1;
        for(unsigned j=0;j<4;++j){step();require(!d.out_valid&&!d.in_ready,"terminal data leaked");}
        return n;
    }

    std::vector<std::string> staging_check_names;
    unsigned directed_staging(const Case& raw) {
        if constexpr(SYNC_STAGING==0)return 0;
        else {
            overlap=true;prefetch=true;tile_overlap=true;
            auto passed=[&](const char* name){staging_check_names.emplace_back(name);};
            auto cancel=[&](){d.abort_packet=1;step();d.abort_packet=0;};
            auto quiet=[&](){d.in_valid=0;d.out_ready=1;for(unsigned j=0;j<9;++j){step();require(!d.stage_read_req&&!d.stage_read_rsp&&!d.dbg_coef_valid&&!d.dbg_meta_valid,"stale staging response after cancellation");}};
            Case tail=zero_tiles(3);run(tail,false,true);
            require(telemetry.stage_reads_by_purpose[0]==46&&telemetry.stage_reads_by_purpose[1]==28&&
                telemetry.stage_reads_by_purpose[2]==1&&telemetry.stage_reads_by_purpose[3]==0,"staging unaligned header/descriptor/tail schedule");
            passed("unaligned_header_descriptor_partial_word");
            Case padding=tail;padding.packet[48]|=1;checksum(padding.packet);
            auto rejected=run(padding,false,true,0x17,false);
            require(rejected.writes==0&&rejected.reads==0,"staging padding admitted before descriptor validation");
            passed("padding_rejected_before_metadata");
            auto until_port=[&](bool response){
                slow=true;start(tail,false);size_t at=0;bool seen=false;
                for(unsigned j=0;j<20000&&!seen;++j){
                    d.in_valid=at<tail.packet.size();if(d.in_valid){d.in_data=tail.packet[at];d.in_last=at+1==tail.packet.size();}
                    d.out_ready=1;d.eval();seen=response?bool(d.stage_read_rsp):bool(d.stage_read_req);
                    if(!seen&&step().input)++at;
                }
                require(seen,"staging cancellation port setup");d.in_valid=0;
            };
            until_port(false);cancel();quiet();run(tail,false,true);passed("abort_queued_ram_request");
            for(unsigned action=0;action<3;++action){
                until_port(true);
                if(action==0)cancel();
                else if(action==1){d.reset=1;step();d.reset=0;}
                else start(raw,false);
                quiet();run(raw,false,true);
                passed(action==0?"abort_registered_ram_response":action==1?"reset_registered_ram_response":"restart_registered_ram_response");
            }
            // A long DC code makes the next byte fetch coincide with a held
            // sparse coefficient once the two write-line owners are full.
            Case extreme=zero_tiles(32);extreme.id="directed:staging-extreme-dc";
            const unsigned bits=32*14,dcbytes=bits/8,dcsize=6+dcbytes;
            extreme.packet.assign(42+dcsize+18+4,0);
            auto put=[&](unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)extreme.packet[at+j]=uint8_t(value>>(8*j));};
            extreme.packet[0]='B';extreme.packet[1]='R';extreme.packet[2]='8';extreme.packet[3]='8';extreme.packet[4]=1;
            put(6,32);extreme.packet[10]=1;put(14,dcsize);for(unsigned j=1;j<4;++j)put(14+4*j,6);
            extreme.packet[42]=13;extreme.packet[43]=255;put(44,bits);
            unsigned bit=0;for(unsigned block=0;block<32;++block)for(unsigned j=0;j<14;++j){
                if(j<2){extreme.packet[48+bit/8]|=uint8_t(1U<<(7-bit%8));}
                ++bit;}
            checksum(extreme.packet);extreme.dense.assign(32*128,0);extreme.packed.assign(96,0);
            for(unsigned block=0;block<32;++block){extreme.dense[block*128+1]=8;extreme.packed[32+block*2+1]=8;}
            auto packed_put=[&](unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)extreme.packed[at+j]=uint8_t(value>>(8*j));};
            packed_put(0,0x43393150);packed_put(4,32);packed_put(24,96);
            bool pending_cancel_seen=false;std::ostringstream cancellation_phases;
            for(unsigned bad_index=0;bad_index<8;++bad_index){
                Case grammar=extreme;grammar.id="directed:staging-context-range-failure:"+std::to_string(bad_index);
                for(unsigned j=0;j<14;++j){const unsigned position=bad_index*14+j;
                    grammar.packet[48+position/8]|=uint8_t(1U<<(7-position%8));}
                checksum(grammar.packet);
                const auto context_reject=run(grammar,false,true,0x15,false);
                require(context_reject.reads==0&&context_reject.writes==0,
                    "context range failure reached external memory before a complete DC line");
                pending_cancel_seen|=stage_cancel_pending_witness;
                cancellation_phases<<" index="<<bad_index<<" reads="<<telemetry.stage_reads<<" responses="<<telemetry.stage_responses
                    <<" witness="<<stage_cancel_pending_witness;
            }
            require(pending_cancel_seen,"context failure did not cancel an in-flight staging read"+cancellation_phases.str());
            passed("context_failure_cancels_inflight_fetch");
            force_request_stall=true;slow=true;start(extreme,false);size_t at=0;bool witnessed=false;
            for(unsigned j=0;j<200000&&!witnessed;++j){
                d.in_valid=at<extreme.packet.size();if(d.in_valid){d.in_data=extreme.packet[at];d.in_last=at+1==extreme.packet.size();}
                d.out_ready=1;d.eval();witnessed=d.dbg_coef_valid&&!d.dbg_coef_ready&&(d.stage_read_req||d.stage_pending);
                if(!witnessed&&step().input)++at;
            }
            require(witnessed,"held sparse coefficient never overlapped synchronous fetch");d.in_valid=0;
            for(unsigned j=0;j<31;++j){step();require(d.dbg_coef_valid&&!d.dbg_coef_ready,"held sparse coefficient hidden by RAM fetch");}
            cancel();force_request_stall=false;quiet();run(extreme,false,true);passed("held_sparse_visible_during_ram_fetch");
            force_request_stall=true;slow=true;start(raw,false);at=0;bool raw_hold=false;
            for(unsigned j=0;j<200000&&!raw_hold;++j){d.in_valid=at<raw.packet.size();if(d.in_valid){d.in_data=raw.packet[at];d.in_last=at+1==raw.packet.size();}
                d.out_ready=1;d.eval();raw_hold=d.dbg_coef_valid&&!d.dbg_coef_ready;if(!raw_hold&&step().input)++at;}
            require(raw_hold,"RAW synchronous pair hold setup");d.in_valid=0;
            for(unsigned j=0;j<31;++j){step();require(d.dbg_coef_valid&&!d.dbg_coef_ready&&!d.stage_read_req&&!d.stage_pending,"RAW fetched next pair before old acceptance");}
            cancel();force_request_stall=false;quiet();run(raw,false,true);passed("raw_pair_held_until_acceptance");
            return unsigned(staging_check_names.size());
        }
    }

    unsigned directed_tiles() {
        overlap=true;prefetch=true;tile_overlap=true;unsigned checks=0;
        const Case c=zero_tiles(16);
        auto setup=[&](bool pending_read) {
            slow=true;start(c,false);size_t at=0;bool ready=false;
            for(unsigned j=0;j<200000&&!ready;++j) {
                d.in_valid=at<c.packet.size();if(d.in_valid){d.in_data=c.packet[at];d.in_last=at+1==c.packet.size();}
                d.out_ready=pending_read;
                if(step().input)++at;
                ready=pending_read ? pending.valid&&!pending.write&&d.dbg_tile_preparing&&d.out_valid : bool(d.out_valid);
            }
            require(ready,"tile overlap directed setup");d.in_valid=0;
            if(pending_read){pending.due=cycle+1000;d.out_ready=0;step();}
        };
        auto cancel=[&]() {d.abort_packet=1;step();d.abort_packet=0;};
        auto drain=[&]() {
            d.in_valid=0;d.out_ready=1;
            for(unsigned j=0;j<3000&&(pending.valid||d.busy);++j)step();
            require(!pending.valid&&!d.busy,"tile accepted read drain");
        };
        // Both banks ready cannot let the producer lap a held emitted bank.
        setup(false);d.out_ready=0;
        for(unsigned j=0;j<300&&d.dbg_bank_ready!=3;++j)step();
        require(d.dbg_bank_ready==3&&!d.dbg_tile_preparing&&d.dbg_scratch_state==28,"two ready tile-bank setup");
        const auto starts=d.count_tile_starts;const auto block=d.out_block;const auto index=d.out_index;const auto value=int16_t(d.out_value);
        for(unsigned j=0;j<257;++j){step();require(d.out_valid&&d.out_block==block&&d.out_index==index&&int16_t(d.out_value)==value&&
            d.dbg_bank_ready==3&&d.count_tile_starts==starts&&!pending.valid,"held emitted bank was overwritten or lapped");}
        cancel();drain();run(c,false,true);++checks;
        // Cache response for next-tile preparation may arrive during held output.
        setup(true);const auto held_block=d.out_block;const auto held_index=d.out_index;const auto held_value=int16_t(d.out_value);
        const auto pre_ack=public_snapshot();pending.due=cycle;Edge e=step();require(e.response&&!e.output&&!pending.valid&&d.out_valid&&
            d.out_block==held_block&&d.out_index==held_index&&int16_t(d.out_value)==held_value,"tile preparation ACK changed emitted value pre="+pre_ack+" post="+public_snapshot());
        cancel();drain();run(c,false,true);++checks;
        // An accepted preparation read survives cancellation with both tile owners invalid.
        setup(true);const auto owner=pending;cancel();
        require(pending.valid&&pending.epoch==owner.epoch&&d.draining&&!d.out_valid&&d.dbg_bank_ready==0,"tile abort lost accepted read owner");
        pending.due=cycle;step();drain();run(c,false,true);++checks;
        // A matching error ACK wins over the otherwise ready emitted scalar.
        setup(true);d.out_ready=1;injected_error=1;pending.due=cycle;e=step();
        require(e.response&&!e.output&&!pending.valid&&!d.out_valid&&!d.scratch_sealed&&d.dbg_bank_ready==0,"tile read error leaked output");
        step();require(d.error==0x25,"tile read error status");cancel();drain();run(c,false,true);++checks;
        // A stale response fails output closed but cannot retire the actual owner.
        setup(true);d.out_ready=1;const auto stale_owner=pending;inject_stale_response=true;e=step();
        require(e.response&&!e.output&&pending.valid&&pending.epoch==stale_owner.epoch&&d.dbg_scratch_outstanding&&
            !d.out_valid&&d.dbg_bank_ready==0,"tile stale ACK retired actual owner");
        step();require(d.error==0x26,"tile stale response status");pending.due=cycle;step();drain();run(c,false,true);++checks;
        // Held reset still owns a physical read until its matching ACK.
        setup(true);d.reset=1;
        for(unsigned j=0;j<9;++j){step();require(pending.valid&&!d.out_valid&&d.dbg_bank_ready==0,"tile held reset lost physical hazard");}
        pending.due=cycle;step();require(!pending.valid,"tile ACK during held reset");d.reset=0;drain();run(c,false,true);++checks;
        // Replacement input may arrive before old preparation read drains, but
        // the new allocator cannot take ownership until the physical response.
        setup(true);const auto old_owner=pending;start(c,false);size_t at=0;d.out_ready=0;
        for(unsigned j=0;j<300;++j){d.in_valid=at<c.packet.size();if(d.in_valid){d.in_data=c.packet[at];d.in_last=at+1==c.packet.size();}
            if(step().input)++at;
            require(pending.valid&&pending.epoch==old_owner.epoch&&!d.dbg_allocation&&!d.out_valid,"tile replacement allocated before old read drain");}
        pending.due=cycle;step();cancel();drain();run(c,false,true);++checks;
        // New bank publication can coincide with the previous tile's last
        // scalar acceptance; next-bank scalar zero is delivered on a later edge.
        setup(false);d.out_ready=0;
        for(unsigned j=0;j<300&&d.dbg_bank_ready!=3;++j)step();
        require(d.dbg_bank_ready==3,"tile handoff setup");d.out_ready=1;
        for(unsigned j=0;j<63;++j){e=step();require(e.output&&e.block==0&&e.index==j,"tile bank sequence before handoff");}
        e=step();require(e.output&&e.block==0&&e.index==63&&!d.done,"tile release early terminal");
        e=step();require(e.output&&e.block==1&&e.index==0,"next tile did not preserve block order");
        cancel();drain();run(c,false,true);++checks;
        // Prepare completion and the old bank's final scalar may share an
        // edge, with neither a payload overwrite nor a skipped next owner.
        setup(true);d.out_ready=1;
        while(d.out_index<63){e=step();require(e.output,"tile simultaneous publish setup stalled");}
        d.out_ready=0;pending.due=cycle;step();
        for(unsigned j=0;j<100&&!d.dbg_tile_publish;++j)step();
        require(d.dbg_tile_publish&&d.out_valid&&d.out_index==63,"tile exact publication/release setup");
        const auto simultaneous=d.count_publish_release_same_edge;const auto previous_block=d.out_block;
        d.out_ready=1;e=step();require(e.output&&e.index==63&&d.count_publish_release_same_edge==simultaneous+1,"tile same-edge publish/release collision");
        e=step();require(e.output&&e.block==previous_block+1&&e.index==0,"tile same-edge next owner sequence");
        cancel();drain();run(c,false,true);++checks;
        // An offered but unaccepted next-tile read remains immutable under
        // request backpressure while the current scalar is held.
        slow=true;start(c,false);at=0;bool offered=false,stream_seen=false;
        for(unsigned j=0;j<200000&&!offered;++j){d.in_valid=at<c.packet.size();if(d.in_valid){d.in_data=c.packet[at];d.in_last=at+1==c.packet.size();}
            d.out_ready=1;if(d.out_valid)stream_seen=true;if(stream_seen)force_request_stall=true;
            d.eval();if(d.mem_req_valid&&!d.mem_req_write&&d.out_valid&&d.dbg_tile_preparing&&!pending.valid){offered=true;break;}
            if(step().input)++at;}
        require(offered,"tile unaccepted read offer setup");d.in_valid=0;d.out_ready=0;
        for(unsigned j=0;j<31;++j){step();require(d.mem_req_valid&&!pending.valid&&d.out_valid,"tile offered read changed under backpressure");}
        cancel();force_request_stall=false;require(!pending.valid&&!d.out_valid&&d.dbg_bank_ready==0,"tile unaccepted read abort leaked owner");
        drain();run(c,false,true);++checks;
        // Final scalar held cannot complete the chunk, even after all tile prep.
        slow=true;start(c,false);at=0;bool final=false;
        for(unsigned j=0;j<200000&&!final;++j){d.in_valid=at<c.packet.size();if(d.in_valid){d.in_data=c.packet[at];d.in_last=at+1==c.packet.size();}
            d.out_ready=1;d.eval();if(d.out_valid&&d.out_block==c.blocks-1&&d.out_index==63){d.out_ready=0;final=true;break;}
            if(step().input)++at;}
        require(final,"tile final scalar setup");d.in_valid=0;
        for(unsigned j=0;j<257;++j){step();require(d.out_valid&&!d.done&&!pending.valid&&d.dbg_bank_ready!=0,"tile final held completion fence");}
        d.out_ready=1;e=step();require(e.output&&!d.done,"tile final child acceptance timing");step();require(d.done&&!d.error,"tile final integrated completion");++checks;
        tile_overlap=false;return checks;
    }

    unsigned directed_overlap(const Case& raw) {
        require(overlap,"overlap-directed configuration");unsigned checks=0;
        auto feed=[&](size_t& at) {
            d.in_valid=at<raw.packet.size();
            if(d.in_valid){d.in_data=raw.packet[at];d.in_last=at+1==raw.packet.size();}
        };
        // Return with an accepted first write and a partial/full second line.
        auto setup=[&](bool full) {
            slow=true;start(raw,false);size_t at=0;bool extended=false,ready=false;
            for(unsigned j=0;j<30000&&!ready;++j) {
                feed(at);d.out_ready=1;if(step().input)++at;
                if(pending.valid&&!extended){require(pending.write,"overlap setup direction");pending.due=cycle+1000;extended=true;}
                ready=extended&&pending.valid&&(full?d.dbg_scratch_state==26:
                    (d.dbg_scratch_assembly_bytes>0&&d.dbg_scratch_assembly_bytes<16));
            }
            require(ready,"accepted write/second assembler setup");d.in_valid=0;
        };
        auto drain=[&]() {
            d.in_valid=0;d.out_ready=1;
            for(unsigned j=0;j<3000&&(pending.valid||d.busy);++j)step();
            require(!pending.valid&&!d.busy,"directed accepted-write drain");
        };
        // A full second line backpressures; ACK and enqueue share one edge.
        setup(true);const unsigned address=pending.address;
        require(d.dbg_write_slot_valid&&d.dbg_assembler_full&&!d.dbg_coef_ready,"full queue producer backpressure");
        for(unsigned j=0;j<13;++j){step();require(d.dbg_scratch_state==26&&pending.address==address,"full queue changed accepted owner");}
        const uint64_t enqueues=d.count_write_enqueues,acks=d.count_write_acks;
        pending.due=cycle;Edge e=step();
        require(e.response&&!e.request&&!pending.valid&&d.dbg_write_slot_valid&&!d.dbg_assembler_full&&
            d.count_write_enqueues==enqueues+1&&d.count_write_acks==acks+1,"simultaneous ACK/enqueue ownership");
        e=step();require(e.request&&pending.address==address+16,"replacement physical request order");
        d.abort_packet=1;step();d.abort_packet=0;drain();run(raw,false,true);++checks;
        // An unaccepted, offered write may be withdrawn without a physical ACK.
        slow=true;force_request_stall=true;start(raw,false);size_t at=0;
        for(unsigned j=0;j<30000&&!d.mem_req_valid;++j){feed(at);if(step().input)++at;}
        require(d.mem_req_valid&&d.dbg_write_slot_valid&&!pending.valid,"unaccepted offered-slot setup");
        for(unsigned j=0;j<17;++j)step();
        d.abort_packet=1;step();d.abort_packet=0;force_request_stall=false;
        require(!pending.valid&&!d.dbg_write_slot_valid&&!d.dbg_scratch_assembly_bytes,"abort retained unaccepted line");
        drain();run(raw,false,true);++checks;
        // Accepted owner plus partial assembly survives held warm reset as a
        // hazard, while every unaccepted local byte is cancelled.
        setup(false);const auto owner=pending;d.reset=1;
        for(unsigned j=0;j<9;++j){step();require(pending.valid&&pending.epoch==owner.epoch&&
            !d.dbg_write_slot_valid&&!d.dbg_scratch_assembly_bytes,"held reset ownership");}
        d.reset=0;pending.due=cycle;step();drain();run(raw,false,true);++checks;
        // Error ACK has priority over a full-line enqueue.
        setup(true);const uint64_t before=d.count_write_enqueues;
        injected_error=1;pending.due=cycle;step();
        require(!pending.valid&&!d.dbg_write_slot_valid&&!d.dbg_scratch_assembly_bytes&&
            d.count_write_enqueues==before,"error ACK enqueued waiting line");
        step();require(d.error==0x25&&!d.scratch_sealed,"error ACK publication fence");
        d.abort_packet=1;step();d.abort_packet=0;drain();run(raw,false,true);++checks;
        // A stale response cannot retire the actual accepted owner or enqueue
        // a waiting line. Its later matching response is still required.
        setup(true);const auto stale_owner=pending;
        inject_stale_response=true;step();
        require(pending.valid&&pending.epoch==stale_owner.epoch&&d.dbg_scratch_outstanding&&
            !d.dbg_write_slot_valid&&!d.dbg_scratch_assembly_bytes,"stale ACK retired real owner");
        step();require(d.error==0x26&&!d.scratch_sealed,"stale ACK error fence");
        pending.due=cycle;step();drain();run(raw,false,true);++checks;
        // Stale abort is scoped to its epoch. The pipeline abort API always
        // targets its active owner, so exercise this via a replacement owner:
        // reset/start and drain assertions above protect epoch reuse.
        // Delay the final data ACK after packet done; seal must remain blocked.
        slow=true;start(raw,false);at=0;bool held_final=false,saw_done=false;
        const unsigned last_data=unsigned(raw.packed.size())-16;
        for(unsigned j=0;j<30000&&!held_final;++j){feed(at);if(step().input)++at;
            if(pending.valid&&pending.write&&pending.address==last_data){pending.due=cycle+2000;held_final=true;}}
        require(held_final,"last data ACK fence setup");d.in_valid=0;
        for(unsigned j=0;j<300;++j){step();saw_done|=bool(d.dbg_packet_done);
            require(!d.dbg_seal_ready&&!d.scratch_sealed&&!d.out_valid&&pending.valid,"last data ACK seal barrier");}
        require(saw_done,"packet done did not reach delayed final-write barrier");
        pending.due=cycle;step();require(!pending.valid,"final data physical ACK");
        d.abort_packet=1;step();d.abort_packet=0;drain();run(raw,false,true);++checks;
        return checks;
    }

    unsigned directed_prefetch(const Case& raw) {
        overlap=true;prefetch=true;unsigned checks=0;
        auto prepare=[&](bool accept,bool hold=true) {
            slow=true;force_request_stall=false;start(raw,false);size_t at=0;bool ready=false;
            for(unsigned j=0;j<100000&&!ready;++j) {
                d.in_valid=at<raw.packet.size();
                if(d.in_valid){d.in_data=raw.packet[at];d.in_last=at+1==raw.packet.size();}
                d.out_ready=1;d.eval();
                if(d.dbg_prefetch_launch){ready=true;break;}
                if(step().input)++at;
            }
            require(ready&&d.out_valid&&d.scratch_sealed,"prefetch dense-window setup");
            d.out_ready=!hold;force_request_stall=!accept;
            const auto before=d.count_prefetch_offers;step();d.in_valid=0;
            require(d.dbg_prefetch_offer&&d.count_prefetch_offers==before+1&&!pending.valid,"prefetch offer ownership");
            if(hold)require(d.out_valid,"prefetch launch changed held dense scalar");
            else require(d.dbg_scratch_state==27&&!d.out_valid&&!d.done,"same-edge launch/last-scalar drain");
            if(accept){step();require(pending.valid&&!pending.write&&d.dbg_prefetch_offer,"prefetch physical acceptance");pending.due=cycle+1000;}
        };
        auto drain=[&]() {
            force_request_stall=false;d.in_valid=0;d.out_ready=1;
            for(unsigned j=0;j<3000&&(pending.valid||d.busy);++j)step();
            require(!pending.valid&&!d.busy,"prefetch hazard drain");
        };
        auto cancel=[&]() {d.abort_packet=1;step();d.abort_packet=0;};
        // A ready-low offer and held dense coefficient each remain immutable;
        // neither ownership is transferred by the request's mere existence.
        prepare(false);const auto held=old_value;
        for(unsigned j=0;j<31;++j){step();require(d.dbg_prefetch_offer&&!pending.valid&&d.out_valid&&int16_t(d.out_value)==held,"stalled prefetch/dense owner");}
        cancel();require(!pending.valid&&!d.dbg_prefetch_offer&&!d.out_valid,"unaccepted prefetch cancel");
        drain();run(raw,false,true);++checks;
        // A cache ACK may arrive while dense is held; raw_value owns that scalar.
        prepare(true);const int value=int16_t(d.out_value);pending.due=cycle;Edge e=step();
        require(e.response&&!e.output&&!pending.valid&&!d.dbg_prefetch_offer&&d.out_valid&&int16_t(d.out_value)==value,"prefetch ACK changed held dense scalar");
        d.out_ready=1;e=step();require(e.output&&e.value==value,"held scalar after cache update");
        cancel();drain();run(raw,false,true);++checks;
        // Logical cancellation cannot retire the accepted read's physical owner.
        prepare(true);const auto owner=pending;cancel();
        require(pending.valid&&pending.epoch==owner.epoch&&d.draining&&!d.out_valid&&!d.dbg_prefetch_offer,"accepted prefetch abort lost physical owner");
        for(unsigned j=0;j<17;++j){step();require(pending.valid&&!d.dbg_meta_ready,"bank reused before read ACK");}
        pending.due=cycle;step();drain();run(raw,false,true);++checks;
        // Matching error ACK wins over dense acceptance and cache use.
        prepare(true);d.out_ready=1;injected_error=1;pending.due=cycle;e=step();
        require(e.response&&!e.output&&!pending.valid&&!d.scratch_sealed&&!d.dbg_prefetch_offer,"prefetch error ACK leaked dense/cache owner");
        step();require(d.error==0x25&&!d.out_valid,"prefetch ACK error did not fail closed");
        cancel();drain();run(raw,false,true);++checks;
        // An unrelated response fails the logical epoch but cannot retire the
        // true accepted read. No dense handshake occurs on this error edge.
        prepare(true);d.out_ready=1;inject_stale_response=true;e=step();
        require(e.response&&!e.output&&pending.valid&&d.dbg_scratch_outstanding&&!d.scratch_sealed,"stale prefetch ACK retired owner");
        step();require(d.error==0x26&&!d.out_valid,"stale prefetch ACK did not fail closed");
        pending.due=cycle;step();drain();run(raw,false,true);++checks;
        // Reset remains cancellation even if the matching ACK arrives while held.
        prepare(true);d.reset=1;
        for(unsigned j=0;j<9;++j){step();require(pending.valid&&!d.out_valid,"held reset lost accepted prefetch");}
        pending.due=cycle;step();require(!pending.valid,"read ACK not drained during reset");
        d.reset=0;drain();run(raw,false,true);++checks;
        // Accepted read completion is required before next-scalar demand reuse.
        prepare(true);d.out_ready=1;e=step();
        require(e.output&&d.dbg_scratch_state==27&&!d.out_valid,"prefetch completion barrier setup");
        for(unsigned j=0;j<31;++j){step();require(pending.valid&&!d.out_valid&&!d.done&&d.dbg_scratch_state==27,"pending read bypassed tile-demand barrier");}
        pending.due=cycle;step();require(!pending.valid&&d.dbg_scratch_state!=27,"read ACK did not release demand");
        cancel();drain();run(raw,false,true);++checks;
        // A request first offered on the same edge as a line's final scalar
        // acceptance must also enter the barrier (pre-edge owner was absent).
        prepare(true,false);require(pending.valid&&d.dbg_scratch_state==27,"newly launched owner was not retained");
        cancel();pending.due=cycle;step();drain();run(raw,false,true);++checks;
        prefetch=false;return checks;
    }

    unsigned directed(const Case& simple,const Case& raw) {
        unsigned checks=0;
        Case bad=simple;bad.id="crc-corruption";bad.packet.back()^=1;
        run(bad,false,true,0x13,false);++checks;
        bad=simple;bad.id="invalid-block-bound";bad.blocks=0;
        run(bad,false,true,0x11,false);++checks;
        bad=simple;bad.id="bad-last-descriptor-before-admission";
        bad.packet[61]=20;checksum(bad.packet);
        auto failure=run(bad,false,true,0x14,false);
        require(failure.writes==0&&failure.reads==0,"metadata failure reached scratch memory");++checks;
        bad=raw;bad.id="late-raw-range-abort";
        bad.packet[42+126]=1;bad.packet[42+127]=8;checksum(bad.packet);
        failure=run(bad,false,true,0x15,false);
        require(failure.writes>0&&failure.reads==0,"late semantic failure not provisional");++checks;
        failure=run(oversized_scratch(),false,true,0x21,false);
        require(failure.writes==0&&failure.reads==0,"over-budget packet wrote memory before admission");++checks;
        injected_error=1;
        failure=run(simple,false,true,0x25,false);
        require(failure.writes==1&&failure.reads==0,"write ACK error did not fail closed");++checks;
        // On the exact edge after a write error reaches the store, pipeline
        // error has not yet latched. A replacement start must override the
        // old owner's internal cancellation and remain in RECEIVE.
        slow=true;start(simple,false);size_t fault_at=0;bool saw_error_ack=false;
        for(unsigned j=0;j<20000&&!saw_error_ack;++j) {
            d.in_valid=fault_at<simple.packet.size();if(d.in_valid){d.in_data=simple.packet[fault_at];d.in_last=fault_at+1==simple.packet.size();}
            if(pending.valid)injected_error=1;
            Edge e=step();if(e.input)++fault_at;
            saw_error_ack=e.response;
        }
        require(saw_error_ack&&!d.error,"exact error/start race setup");
        start(simple,false);d.eval();
        require(d.in_ready,"replacement start lost after write ACK error");
        run(simple,false,true);++checks;
        // Cancellation with a delayed accepted write, then replacement starts
        // before that write ACK. The new allocator must wait; the old write
        // still commits, but cannot hit an already allocated replacement bank.
        for(unsigned action=0;action<3;++action) {
            slow=true;start(simple,false);size_t at=0;
            for(unsigned j=0;j<20000&&!pending.valid;++j) {
                d.in_valid=at<simple.packet.size();if(d.in_valid){d.in_data=simple.packet[at];d.in_last=at+1==simple.packet.size();}
                if(step().input)++at;
            }
            require(pending.valid&&pending.write,"cancel delayed write setup");
            pending.due=cycle+500;uint32_t old_epoch=pending.epoch;
            if(action==0)d.abort_packet=1;else if(action==1)d.reset=1;
            else {d.start=1;d.packet_bytes=simple.packet.size();d.blocks=simple.blocks;d.epoch=++next_epoch;d.serial_clear=0;}
            d.in_valid=0;d.out_ready=1;Edge e=step();
            require(!e.output&&!e.request&&pending.valid&&pending.epoch==old_epoch,"cancel lost accepted write");
            d.abort_packet=0;d.reset=0;d.start=0;
            if(action==1) {
                d.reset=1;
                for(unsigned j=0;j<10;++j){step();require(pending.valid,"warm reset forgot write");}
                d.reset=0;
            }
            start(simple,false);at=0;bool waited=false;unsigned outputs=0;
            for(unsigned j=0;j<20000&&!d.done&&!d.error;++j) {
                d.in_valid=at<simple.packet.size();if(d.in_valid){d.in_data=simple.packet[at];d.in_last=at+1==simple.packet.size();}
                d.out_ready=1;if(d.metadata_wait)waited=true;
                Edge edge=step();if(edge.input)++at;
                if(edge.output){require(edge.epoch==current_epoch,"old epoch dense leak");++outputs;}
                if(pending.valid&&pending.epoch!=old_epoch)require(!d.metadata_wait,"new memory operation before allocation");
            }
            require(waited&&d.done&&!d.error&&outputs==simple.dense.size()/2,"replacement/drain failed");
            require(std::equal(simple.packed.begin(),simple.packed.end(),ram.begin()),"delayed old write damaged replacement");
            d.in_valid=0;step();++checks;
        }
        slow=true;start(simple,false);size_t at=0;unsigned produced=0;
        for(unsigned j=0;j<20000;++j) {
            d.in_valid=at<simple.packet.size();if(d.in_valid){d.in_data=simple.packet[at];d.in_last=at+1==simple.packet.size();}
            d.out_ready=produced+1<simple.dense.size()/2;
            Edge e=step();if(e.input)++at;if(e.output)++produced;
            if(produced+1==simple.dense.size()/2&&d.out_valid)break;
        }
        require(produced+1==simple.dense.size()/2&&d.out_valid,"final dense hold setup");
        d.out_ready=0;
        for(unsigned j=0;j<257;++j){step();require(!d.done&&d.out_valid,"premature integrated done while final dense held");}
        d.out_ready=1;require(step().output,"final dense transfer");
        for(unsigned j=0;j<4&&!d.done;++j)step();
        require(d.done&&!d.error,"integrated final acceptance fence");++checks;
        return checks;
    }
};

template<size_t N> static void print_array(const std::array<uint64_t,N>& values) {
    std::cout<<"[";for(size_t i=0;i<N;++i){if(i)std::cout<<",";std::cout<<values[i];}std::cout<<"]";
}
static void print(const Counts& n) {
    std::cout<<"\"cycles\":"<<n.cycles<<",\"input_bytes\":"<<n.input<<",\"dense_coefficients\":"<<n.dense
        <<",\"read_requests\":"<<n.reads<<",\"write_requests\":"<<n.writes<<",\"output_stalls\":"<<n.stalls
        <<",\"metadata_wait\":"<<n.metadata_wait<<",\"memory_pending_edges\":"<<n.memory_wait
        <<",\"request_service_hash\":\""<<n.request_service_hash<<"\""
        <<",\"request_service_multiset_hash\":\""<<n.request_multiset_hash<<"\""
        <<",\"ordered_write_service_hash\":\""<<n.ordered_write_service_hash<<"\""
        <<",\"memory_line_coverage\":{\"read_once_lines\":"<<n.read_once_lines<<",\"write_once_lines\":"<<n.write_once_lines<<"}";
#ifndef V91E_LEGACY
    const auto& t=n.telemetry;
    std::cout<<",\"observability\":{\"packet_state_cycles\":";print_array(t.packet);
    std::cout<<",\"scratch_state_cycles\":";print_array(t.scratch);
    std::cout<<",\"emitter_state_cycles\":";print_array(t.emitter);
    std::cout<<",\"first_coefficient_by_band\":";print_array(t.first_coef_band);
    std::cout<<",\"last_coefficient_by_band\":";print_array(t.last_coef_band);
    std::cout<<",\"band_end_by_band\":";print_array(t.band_end);
    std::cout<<",\"highwaters\":{\"assembly_bytes\":"<<t.max_assembly<<",\"cache_lines\":"<<t.max_cache
        <<",\"ac_heads\":"<<t.max_head<<",\"outstanding_requests\":"<<t.max_outstanding
        <<",\"tile_owned\":"<<t.max_tile_owned<<",\"tile_ready\":"<<t.max_tile_ready<<",\"prefetch_offer\":"<<t.max_prefetch_offer<<",\"write_slot\":"<<t.max_write_slot<<",\"owned_lines\":"<<t.max_owned_lines<<"}";
    std::cout<<",\"write_overlap_counters\":{\"enqueues\":"<<t.write_enqueues<<",\"physical_accepts\":"<<t.write_accepts
        <<",\"physical_acks\":"<<t.write_acks<<",\"full_wait_edges\":"<<t.full_wait
        <<",\"packing_during_write_pending\":"<<t.packing_during_write_pending<<"}";
    std::cout<<",\"staging_counters\":{\"reads\":"<<t.stage_reads<<",\"responses\":"<<t.stage_responses
        <<",\"writes\":"<<t.stage_writes<<",\"fetch_wait_edges\":"<<t.stage_wait<<",\"word_hold_edges\":"<<t.stage_word_hold<<",\"buffer_highwater\":"<<t.stage_buffer_max
        <<",\"reads_by_purpose\":["<<t.stage_reads_by_purpose[0]<<","<<t.stage_reads_by_purpose[1]<<","<<t.stage_reads_by_purpose[2]<<","<<t.stage_reads_by_purpose[3]<<"]}";
    std::cout<<",\"read_prefetch_counters\":{\"offers\":"<<t.prefetch_offers<<",\"physical_accepts\":"<<t.prefetch_accepts
        <<",\"physical_acks\":"<<t.prefetch_acks<<",\"uses\":"<<t.prefetch_uses<<",\"dense_during_pending\":"<<t.dense_during_read_pending
        <<",\"drain_wait_edges\":"<<t.prefetch_drain_wait<<"}";
    std::cout<<",\"tile_overlap_counters\":{\"prepare_starts\":"<<t.tile_starts<<",\"publishes\":"<<t.tile_publishes<<",\"releases\":"<<t.tile_releases
        <<",\"prepare_output_overlap\":"<<t.prepare_output_overlap<<",\"prepare_output_hold\":"<<t.prepare_output_hold
        <<",\"read_output_overlap\":"<<t.tile_read_output_overlap<<",\"bank_wait_edges\":"<<t.tile_bank_wait
        <<",\"both_ready_wait_edges\":"<<t.both_ready_wait<<",\"prep_done_wait_edges\":"<<t.tile_prep_done_wait
        <<",\"publish_release_same_edge\":"<<t.publish_release_same_edge<<",\"output_valid_edges\":"<<t.output_valid<<"}";
    std::cout<<",\"coefficient_handshakes_by_band\":";print_array(t.coefficients);
    std::cout<<",\"band_end_handshakes_by_band\":";print_array(t.band_ends);
    std::cout<<",\"overlapping_edges\":{\"coefficient_stall\":"<<t.coef_stall
        <<",\"metadata_wait\":"<<t.metadata_wait<<",\"band_end_stall\":"<<t.band_end_stall
        <<",\"memory_request_stall\":"<<t.mem_req_stall<<",\"memory_pending\":"<<t.mem_pending
        <<",\"input_starved\":"<<t.input_starved<<",\"dense_stall\":"<<n.stalls<<"}"
        <<",\"timestamps\":{\"first_input\":"<<t.first_input<<",\"last_input\":"<<t.last_input
        <<",\"metadata_accept\":"<<t.metadata_accept<<",\"last_sparse_coef\":"<<t.last_sparse_coef
        <<",\"packet_done_observed\":"<<t.packet_done_observed<<",\"seal_accepted\":"<<t.seal_accepted
        <<",\"scratch_sealed_observed\":"<<t.scratch_sealed_observed<<",\"first_dense\":"<<t.first_dense
        <<",\"last_dense\":"<<t.last_dense<<",\"integrated_done\":"<<t.integrated_done<<"}}";
#endif
}
int historical_pipeline_main(int argc,char** argv) {
    Verilated::commandArgs(argc,argv);
    try {
        require(argc==3||argc==4,"usage: tb_pipeline vectors.txt seed [tile-events.jsonl]");Sim sim(std::stoull(argv[2]));
        if(argc==4){sim.tile_stream.open(argv[3]);require(bool(sim.tile_stream),"cannot open tile event output");}
        std::ifstream stream(argv[1]);require(bool(stream),"cannot open vector text");
        std::vector<Case> cases;std::string packet,dense,packed;
        for(Case c;stream>>c.id>>c.blocks>>packet>>dense>>packed;) {
            c.packet=hexbytes(packet);c.dense=hexbytes(dense);c.packed=hexbytes(packed);cases.push_back(c);
        }
        require(!cases.empty(),"empty vector corpus");
        auto simple=std::find_if(cases.begin(),cases.end(),[](const Case& c){return c.blocks==1&&c.packet.size()<100;});
        require(simple!=cases.end(),"no simple packet for cancellation checks");
        auto raw=std::find_if(cases.begin(),cases.end(),[](const Case& c){return c.blocks==1&&c.packet[5]==1;});
        require(raw!=cases.end(),"no raw packet for cancellation checks");
        unsigned checks=sim.directed(*simple,*raw);sim.overlap=true;checks+=sim.directed(*simple,*raw);checks+=sim.directed_overlap(*raw);checks+=sim.directed_prefetch(*raw);checks+=sim.directed_tiles();const unsigned staging_checks=sim.directed_staging(*raw);checks+=staging_checks;uint64_t dense_count=0;sim.record_tiles=true;
        for(const auto& c:cases)for(unsigned profile=0;profile<2;++profile)for(unsigned clear=0;clear<1;++clear)for(unsigned tile=1;tile<2;++tile) {
            sim.overlap=true;sim.prefetch=true;sim.tile_overlap=tile;
            Counts n=sim.run(c,clear,profile);dense_count+=n.dense;
            std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"serial_clear\":"<<clear
                <<",\"memory_profile\":"<<profile<<",\"write_overlap\":1,\"read_prefetch\":1,\"tile_overlap\":"<<tile<<",\"sync_staging\":"<<SYNC_STAGING<<",\"used_bytes\":"<<c.packed.size()<<",";print(n);std::cout<<"}\n";
        }
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<sim.seed
            <<",\"sync_staging\":"<<SYNC_STAGING<<",\"packets\":"<<cases.size()<<",\"configurations\":2,\"case_rows\":"<<cases.size()*2
            <<",\"dense_comparisons\":"<<dense_count<<",\"directed_checks\":"<<checks
            <<",\"sync_staging_checks\":"<<staging_checks<<",\"sync_staging_check_names\":[";
        for(size_t j=0;j<sim.staging_check_names.size();++j){if(j)std::cout<<",";std::cout<<"\""<<sim.staging_check_names[j]<<"\"";}
        std::cout<<"],\"minimum_memory_response_delay\":"<<sim.min_response_delay
            <<",\"maximum_memory_response_delay\":"<<sim.max_response_delay<<"}\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
