#include "Vpacked_scratch.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

static void need(bool ok,const std::string& message) { if(!ok) throw std::runtime_error(message); }
struct Event { unsigned band,block,index; int value; };
struct Case { std::string id; unsigned blocks,raw; std::array<unsigned,3> counts; unsigned used;
    std::vector<Event> events; std::vector<int> dense; std::vector<uint8_t> image; };
static std::vector<uint8_t> unhex(const std::string& value) {
    need(value.size()%2==0,"hex length"); std::vector<uint8_t> result;
    for(size_t at=0;at<value.size();at+=2) result.push_back(static_cast<uint8_t>(std::stoul(value.substr(at,2),nullptr,16)));
    return result;
}
struct Sim {
    std::unique_ptr<Vpacked_scratch> d=std::make_unique<Vpacked_scratch>();
    std::vector<uint8_t> memory=std::vector<uint8_t>(262144,0xa5);
    struct Request { bool write; unsigned address,epoch,delay; std::array<uint32_t,4> data; } pending{};
    bool has_pending=false, stalled=false, inject=false, inject_error=false;
    unsigned inject_epoch=0, min_delay=1, fixed_delay=0;
    uint64_t cycles=0, reads=0,writes=0,req_wait=0,out_wait=0,ack_wait=0;
    uint64_t random=0x91d5eeda;
    unsigned next_epoch=1;
    bool bad_address=false;
    uint64_t draw() { random^=random<<13; random^=random>>7; random^=random<<17; return random; }
    Sim() {
        d->clk=0; d->reset=0; d->begin_valid=0; d->coef_valid=0; d->band_end_valid=0;
        d->seal_valid=0; d->abort_valid=0; d->dense_ready=0; d->mem_req_ready=0;
        d->mem_rsp_valid=0; d->mem_rsp_error=0; d->eval();
        d->reset=1; tick(); d->reset=0; tick();
    }
    void tick() {
        d->clk=0;
        d->mem_req_ready=!has_pending && (!stalled || draw()%4!=0);
        bool actual_response=has_pending && pending.delay==0 && !inject;
        d->mem_rsp_valid=inject || actual_response;
        d->mem_rsp_epoch=inject ? inject_epoch : pending.epoch;
        d->mem_rsp_error=inject_error;
        for(unsigned word=0;word<4;++word) {
            uint32_t value=0;
            if(actual_response && !pending.write)
                for(unsigned b=0;b<4;++b) value|=uint32_t(memory[pending.address+word*4+b])<<(8*b);
            d->mem_rsp_data[word]=value;
        }
        d->eval();
        const bool accept=d->mem_req_valid && d->mem_req_ready;
        const bool response=d->mem_rsp_valid && d->mem_rsp_ready;
        Request captured{};
        if(accept) {
            need(!has_pending,"more than one outstanding request");
            captured.write=d->mem_req_write; captured.address=d->mem_req_addr; captured.epoch=d->mem_req_epoch;
            captured.delay=fixed_delay ? fixed_delay : min_delay+(stalled ? unsigned(draw()%8):0);
            for(unsigned w=0;w<4;++w) captured.data[w]=d->mem_req_data[w];
            need(captured.address%16==0 && captured.address+16<=memory.size(),"memory bounds/alignment");
            need(captured.address+16<=d->used_bytes,"request beyond allocation");
            if(captured.write) ++writes; else ++reads;
        }
        if(d->mem_req_valid && !d->mem_req_ready) ++req_wait;
        if(d->dense_valid && !d->dense_ready) ++out_wait;
        if(has_pending && !actual_response) ++ack_wait;
        // The external bus commits accepted writes when it produces their ACK.
        // Abort/reset cannot roll this back; the byte image retains old writes.
        if(actual_response && response && pending.write)
            for(unsigned w=0;w<4;++w) for(unsigned b=0;b<4;++b)
                memory[pending.address+w*4+b]=uint8_t(pending.data[w]>>(8*b));
        d->clk=1; d->eval(); ++cycles;
        if(actual_response && response) has_pending=false;
        else if(has_pending && !inject && pending.delay) --pending.delay;
        if(accept) { pending=captured; has_pending=true; }
        inject=false; inject_error=false;
        d->clk=0; d->eval();
        need(cycles<200000000,"global watchdog");
    }
    template<typename F> void until(F condition,unsigned limit=2000000) {
        for(unsigned n=0;!condition();++n) { need(n<limit,"interface watchdog"); tick(); }
    }
    void clear() {
        d->coef_valid=0; d->band_end_valid=0; d->seal_valid=0; d->begin_valid=0;
        d->abort_epoch=d->active_epoch; d->abort_valid=1; tick(); d->abort_valid=0;
        until([&]{return bool(d->begin_ready);}); need(!has_pending,"begin before old response drain");
        need(d->error==0,"abort failed to clear error");
    }
    unsigned begin(unsigned blocks,unsigned raw,const std::array<unsigned,3>& counts,bool serial=false) {
        until([&]{return bool(d->begin_ready);});
        const unsigned epoch=next_epoch++;
        d->begin_blocks=blocks; d->begin_raw=raw; d->begin_count1=counts[0];
        d->begin_count2=counts[1]; d->begin_count3=counts[2]; d->begin_epoch=epoch;
        d->begin_serial_clear=serial; d->begin_valid=1; tick(); d->begin_valid=0;
        return epoch;
    }
    void event(const Event& e,unsigned epoch) {
        until([&]{return bool(d->coef_ready) || d->error;}); need(!d->error,"event prior failure");
        d->coef_band=e.band; d->coef_block=e.block; d->coef_index=e.index;
        d->coef_value=uint16_t(e.value); d->coef_epoch=epoch; d->coef_valid=1;
        tick(); d->coef_valid=0;
    }
    void end(unsigned band,unsigned epoch) {
        until([&]{return bool(d->band_end_ready) || d->error;}); need(!d->error,"end prior failure");
        d->band_end_band=band; d->band_end_epoch=epoch; d->band_end_valid=1; tick(); d->band_end_valid=0;
    }
    void seal(unsigned epoch) {
        until([&]{return bool(d->seal_ready) || d->error;}); need(!d->error,"seal prior failure");
        d->seal_epoch=epoch; d->seal_valid=1; tick(); d->seal_valid=0;
    }
    uint64_t run(const Case& c,bool stalls,bool serial) {
        clear(); stalled=stalls; random=0x91d5eeda;
        for(unsigned char character:c.id) random=(random^character)*1099511628211ULL;
        const auto start=cycles, old_reads=reads,old_writes=writes;
        const unsigned epoch=begin(c.blocks,c.raw,c.counts,serial); need(!d->error,"begin rejected "+c.id);
        size_t cursor=0;
        for(unsigned band=0;band<(c.raw?1U:4U);++band) {
            while(cursor<c.events.size() && c.events[cursor].band==band) {
                if(stalls && draw()%3==0) tick();
                event(c.events[cursor++],epoch);
            }
            end(band,epoch);
        }
        need(cursor==c.events.size(),"event band order"); seal(epoch);
        size_t output=0;
        for(unsigned n=0;!d->done;++n) {
            need(n<4000000,"dense watchdog "+c.id); need(!d->error,"dense error "+c.id+" code "+std::to_string(d->error));
            d->dense_ready=!stalls || draw()%4!=0;
            if(d->dense_valid && d->dense_ready) {
                need(output<c.dense.size(),"excess dense output");
                need(d->dense_block==output/64 && d->dense_index==output%64 && d->dense_epoch==epoch,"dense position/epoch");
                need(int16_t(d->dense_value)==c.dense[output],"dense mismatch "+c.id+" at "+std::to_string(output));
                ++output;
            }
            tick();
        }
        need(output==c.dense.size(),"dense count "+c.id);
        need(d->sealed && !has_pending,"done before sealed/drained");
        need(c.used==d->used_bytes && c.image.size()==c.used,"used_bytes");
        need(std::equal(c.image.begin(),c.image.end(),memory.begin()),"packed image mismatch "+c.id);
        need(writes-old_writes==c.used/16 && reads-old_reads==c.used/16,"burst ledger "+c.id);
        std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"stalls\":"<<stalls
                 <<",\"serial_clear\":"<<serial<<",\"cycles\":"<<cycles-start<<",\"outputs\":"<<output
                 <<",\"write_bursts\":"<<writes-old_writes<<",\"read_bursts\":"<<reads-old_reads<<"}\n";
        d->dense_ready=0; return cycles-start;
    }
    void expect_error(unsigned code) { until([&]{return bool(d->error);},1000); need(d->error==code,"wrong error "+std::to_string(d->error)+" expected "+std::to_string(code)); clear(); }
    unsigned directed() {
        unsigned tests=0;
        clear();
        // Exact one-bank budget admission and the next aligned allocation.
        begin(8192,0,{0,0,61432}); need(!d->error && d->used_bytes==262144,"exact capacity admission"); clear(); ++tests;
        begin(8192,0,{0,0,61433}); expect_error(1); ++tests;
        begin(2047,1,{0,0,0}); need(!d->error && d->used_bytes==262048,"largest raw fit"); clear(); ++tests;
 begin(0,0,{0,0,0}); expect_error(1); ++tests;
        begin(8193,0,{0,0,0}); expect_error(1); ++tests;
        begin(1,0,{6,0,0}); expect_error(1); ++tests;
        begin(1,1,{1,0,0}); expect_error(1); ++tests;
        begin(2048,1,{0,0,0}); expect_error(1); ++tests;
        unsigned e=begin(1,0,{0,0,0}); event({0,0,0,2049},e); expect_error(3); ++tests;
        e=begin(1,0,{0,0,0}); event({0,0,0,1},e-1); expect_error(2); ++tests;
        e=begin(1,0,{0,0,0}); end(0,e); expect_error(4); ++tests;
        e=begin(1,0,{1,0,0}); event({0,0,0,0},e); end(0,e); event({1,0,63,1},e); expect_error(3); ++tests;
        e=begin(1,0,{2,0,0}); event({0,0,0,0},e); end(0,e); event({1,0,1,1},e); event({1,0,1,1},e); expect_error(3); ++tests;
        e=begin(1,0,{1,0,0}); event({0,0,0,0},e); end(0,e); event({1,0,1,0},e); expect_error(3); ++tests;
        e=begin(1,1,{0,0,0}); event({0,0,1,0},e); expect_error(3); ++tests;
        // Empty bands are explicit, and success cannot be committed early.
        e=begin(1,0,{0,0,0}); d->seal_epoch=e; d->seal_valid=1; tick(); d->seal_valid=0;
        need(!d->sealed && !d->dense_valid && !d->seal_ready,"early seal accepted"); clear(); ++tests;
        // A late abort from the prior owner must not cancel its replacement.
        e=begin(1,0,{0,0,0}); d->abort_epoch=e-1; d->abort_valid=1; tick(); d->abort_valid=0;
        need(!d->error && d->coef_ready && d->active_epoch==e,"stale abort changed replacement"); clear(); ++tests;
        // Retain a real accepted delayed write across cancellation and warm reset.
        for(bool reset_mode:{false,true}) {
            fixed_delay=40; e=begin(8,0,{0,0,0});
            for(unsigned b=0;b<8;++b) event({0,b,0,7},e);
            until([&]{return has_pending;}); need(pending.write,"delayed request is write");
            d->abort_epoch=e; d->abort_valid=!reset_mode; d->reset=reset_mode; tick();
            d->begin_valid=1; d->begin_epoch=next_epoch; d->begin_blocks=1;
            for(unsigned wait=0;wait<10;++wait) { need(!d->begin_ready,"new allocation while accepted write pending"); tick(); }
            d->abort_valid=0;
            if(reset_mode) { while(has_pending) { need(!d->begin_ready,"reset permits pending reuse"); tick(); } d->reset=0; }
            d->begin_valid=0; until([&]{return bool(d->begin_ready);});
            need(memory[32]==7 && memory[33]==0,"accepted old write erased by cancellation");
            fixed_delay=0; ++tests;
        }
        // No outstanding response is accepted as success.
        inject=true; inject_epoch=e; tick(); expect_error(6); ++tests;
        // A mismatched response does not retire the accepted pending write.
        fixed_delay=40; e=begin(8,0,{0,0,0});
        for(unsigned b=0;b<8;++b) event({0,b,0,9},e);
        until([&]{return has_pending;}); inject=true; inject_epoch=e+999; tick();
        need(d->error==6 && has_pending && !d->begin_ready,"stale response discarded pending hazard");
        until([&]{return bool(d->begin_ready);}); need(memory[32]==9,"stale response cancelled accepted write"); clear(); fixed_delay=0; ++tests;
        // Memory error ACK retires the request and fails closed.
        fixed_delay=3; e=begin(8,0,{0,0,0});
        for(unsigned b=0;b<8;++b) event({0,b,0,11},e);
        until([&]{return has_pending && pending.delay==0;}); inject_error=true; tick(); expect_error(5); fixed_delay=0; ++tests;
        // Descriptor and signed value corruption are caught during the read drain.
        for(unsigned corruption=0;corruption<3;++corruption) {
            e=begin(1,0,{1,0,0}); event({0,0,0,0},e); end(0,e); event({1,0,1,1},e);
            end(1,e); end(2,e); end(3,e); seal(e);
            const unsigned address=corruption==0 ? 0U : (corruption==1 ? 32U : 48U);
            until([&]{return has_pending && !pending.write && pending.address==address;});
            if(corruption==0) memory[0]^=1;
            else if(corruption==1) { memory[32]=1; memory[33]=8; }
            else { memory[48]=0; memory[49]=0; memory[50]=0; memory[51]=0; }
            expect_error(corruption==0 ? 7U : 3U); ++tests;
        }
        // Repeated epochs remain rejected after a warm reset.
        d->reset=1; tick(); d->reset=0; tick();
        d->begin_epoch=e; d->begin_blocks=1; d->begin_raw=0; d->begin_count1=0; d->begin_count2=0; d->begin_count3=0;
        d->begin_valid=1; tick(); d->begin_valid=0; expect_error(2); ++tests;
        return tests;
    }
};
int main(int argc,char** argv) {
    Verilated::commandArgs(argc,argv);
    try {
        need(argc==2,"usage: Vpacked_scratch vectors.txt"); std::ifstream input(argv[1]); need(bool(input),"vectors open");
        std::vector<Case> cases; std::string dense_hex,packed_hex;
        Case c; size_t event_count;
        while(input>>c.id>>c.blocks>>c.raw>>c.counts[0]>>c.counts[1]>>c.counts[2]>>c.used>>event_count>>dense_hex>>packed_hex) {
            c.events.clear(); c.dense.clear(); c.image=unhex(packed_hex);
            for(size_t n=0;n<event_count;++n) { Event event{}; need(bool(input>>event.band>>event.block>>event.index>>event.value),"event parse"); c.events.push_back(event); }
            auto bytes=unhex(dense_hex); for(size_t at=0;at<bytes.size();at+=2) c.dense.push_back(int16_t(unsigned(bytes[at])|(unsigned(bytes[at+1])<<8)));
            cases.push_back(c);
        }
        need(!cases.empty(),"empty vectors"); Sim sim; const auto directed=sim.directed();
        uint64_t total=0,mask_cycles=0,serial_cycles=0;
        for(const auto& row:cases) for(bool stalls:{false,true}) for(bool serial:{false,true}) {
            const auto cycles=sim.run(row,stalls,serial); total+=cycles;
            if(!stalls) { if(serial) serial_cycles+=cycles; else mask_cycles+=cycles; }
        }
        need(serial_cycles>=mask_cycles,"clear comparison");
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"cases\":"<<cases.size()
                 <<",\"configurations\":4,\"directed\":"<<directed<<",\"cycles\":"<<total
                 <<",\"mask_ready_cycles\":"<<mask_cycles<<",\"serial_ready_cycles\":"<<serial_cycles
                 <<",\"request_stall_cycles\":"<<sim.req_wait<<",\"ack_wait_cycles\":"<<sim.ack_wait
                 <<",\"output_stall_cycles\":"<<sim.out_wait<<"}\n";
    } catch(const std::exception& error) { std::cerr<<"TEST_FAIL "<<error.what()<<"\n"; return 1; }
    return 0;
}
