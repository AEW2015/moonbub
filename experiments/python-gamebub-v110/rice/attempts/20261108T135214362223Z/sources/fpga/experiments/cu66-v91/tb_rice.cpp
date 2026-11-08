#include "Vbr88_rice_elastic.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct Request { unsigned k, escape, value, position; };
struct Case { std::string id; unsigned bits; std::vector<uint8_t> data; std::vector<Request> requests; };
struct Result { uint64_t cycles=0, inputs=0, symbols=0, bits=0, input_wait=0, output_stall=0; };
struct Event {
    bool input, request, response;
    unsigned value, position, error;
};
static void require(bool ok,const std::string& message) { if (!ok) throw std::runtime_error(message); }

class Sim {
public:
    Vbr88_rice_elastic d;
    bool held=false;
    unsigned held_value=0, held_position=0, held_error=0;
    uint64_t rng;
    const uint64_t base_seed;
    explicit Sim(uint64_t seed): rng(seed),base_seed(seed) {
        d.clk=0; d.reset=1; d.stream_start=0; d.stream_bits=0;
        d.word16=0; d.serial_mode=0; d.in_valid=0; d.in_data=0;
        d.in_bits=0; d.in_last=0; d.req_valid=0; d.req_k=0;
        d.req_escape=0; d.out_ready=0; step(); d.reset=0;
    }
    uint32_t random() { rng^=rng<<13; rng^=rng>>7; rng^=rng<<17; return uint32_t(rng); }
    Event step() {
        d.clk=0; d.eval();
        if (held && !d.reset && !d.stream_start) {
            require(d.out_valid,"held output valid dropped");
            require(d.out_value==held_value && d.out_consumed==held_position && d.out_error==held_error,
                    "held output payload changed");
        }
        Event e{bool(d.in_valid&&d.in_ready),bool(d.req_valid&&d.req_ready),
                bool(d.out_valid&&d.out_ready),d.out_value,d.out_consumed,d.out_error};
        held=d.out_valid&&!d.out_ready&&!d.reset&&!d.stream_start;
        held_value=d.out_value; held_position=d.out_consumed; held_error=d.out_error;
        d.clk=1; d.eval(); d.clk=0; d.eval();
        require(d.reservoir_bits<=64,"reservoir exceeds64 bits");
        return e;
    }
    void start(unsigned bits,bool word16,bool serial) {
        d.in_valid=0; d.req_valid=0; d.out_ready=0;
        d.word16=word16; d.serial_mode=serial; d.stream_bits=bits;
        d.stream_start=1; step(); d.stream_start=0;
        require(!d.out_valid,"start did not abort old output");
        require(d.count_bits==0 && d.count_cycles==0,"start counters not cleared");
    }
    Result run(const Case& c,bool word16,bool serial,bool stalls) {
        // Matched fast/control pairs see the same cycle-indexed random offers
        // and output-ready schedule. Pending producers hold until handshake.
        rng=1469598103934665603ULL;
        for (unsigned char byte:c.id) {rng^=byte;rng*=1099511628211ULL;}
        rng^=base_seed^(word16?0x16161616ULL:0x32323232ULL);
        if (!rng) rng=1;
        start(c.bits,word16,serial);
        unsigned loaded=0, accepted=0, completed=0;
        bool pending_word=false, pending_request=false;
        uint64_t cycles=0, inputs=0, output_stalls=0;
        const uint64_t watchdog=uint64_t(c.bits)*24+c.requests.size()*80+1000;
        while (completed<c.requests.size()) {
            require(cycles++<watchdog,"watchdog "+c.id);
            const bool offer_word=random()%4!=0,offer_request=random()%4!=0,accept_output=random()%4!=0;
            if (!pending_word && loaded<c.bits && (!stalls || offer_word)) {
                unsigned n=std::min(word16?16u:32u,c.bits-loaded);
                uint32_t value=0;
                for (unsigned j=0;j<n;++j) value|=uint32_t((c.data[(loaded+j)/8]>>(7-(loaded+j)%8))&1)<<(31-j);
                d.in_data=value; d.in_bits=n; d.in_last=loaded+n==c.bits;
                pending_word=true;
            }
            if (!pending_request && accepted<c.requests.size() && (!stalls || offer_request)) {
                d.req_k=c.requests[accepted].k; d.req_escape=c.requests[accepted].escape;
                pending_request=true;
            }
            d.in_valid=pending_word; d.req_valid=pending_request;
            d.out_ready=!stalls || accept_output;
            d.eval();
            if (loaded==c.bits) require(!d.in_ready,"input overrun ready "+c.id);
            if (d.out_valid && !d.out_ready) ++output_stalls;
            Event e=step();
            if (e.input) { loaded+=d.in_bits; ++inputs; pending_word=false; }
            if (e.request) { ++accepted; pending_request=false; }
            if (e.response) {
                require(completed<accepted,"unrequested response "+c.id);
                const auto& expected=c.requests[completed];
                require(e.error==0 && e.value==expected.value && e.position==expected.position,
                    "symbol mismatch "+c.id+" request="+std::to_string(completed)+
                    " got="+std::to_string(e.value)+"/"+std::to_string(e.position)+"/"+std::to_string(e.error)+
                    " expected="+std::to_string(expected.value)+"/"+std::to_string(expected.position));
                ++completed;
            }
        }
        require(loaded==c.bits,"not all exact stream bits fetched "+c.id);
        require(d.count_cycles==cycles && d.count_inputs==inputs && d.count_symbols==completed,
                "handshake counters mismatch "+c.id);
        require(d.count_bits==c.bits && d.count_output_stall==output_stalls,
                "bit/stall counters mismatch "+c.id);
        require(d.count_input_wait<=cycles,"inputwait counter bound");
        return {d.count_cycles,d.count_inputs,d.count_symbols,d.count_bits,d.count_input_wait,d.count_output_stall};
    }
    void request(unsigned k,unsigned escape) {
        d.req_valid=1;d.req_k=k;d.req_escape=escape;d.out_ready=0;
        for (unsigned i=0;i<50;++i) if (step().request) {d.req_valid=0;return;}
        throw std::runtime_error("directed request watchdog");
    }
    void word(uint32_t data,unsigned bits,bool last) {
        d.in_valid=1;d.in_data=data;d.in_bits=bits;d.in_last=last;
        for (unsigned i=0;i<50;++i) if (step().input) {d.in_valid=0;return;}
        throw std::runtime_error("directed word watchdog");
    }
    void response(unsigned error,unsigned value,unsigned position) {
        d.out_ready=0;
        for (unsigned i=0;i<100;++i) {
            if (d.out_valid) {
                require(d.out_error==error && d.out_value==value && d.out_consumed==position,"directed response mismatch");
                for (unsigned hold=0;hold<7;++hold) step();
                d.out_ready=1;require(step().response,"directed response delivery missing");
                d.out_ready=0;return;
            }
            step();
        }
        throw std::runtime_error("directed response watchdog");
    }
    unsigned directed() {
        unsigned checks=0;
        for (bool serial:{false,true}) for (bool word16:{false,true}) {
            Case maximum{"directed:max39",39,{0x00,0x01,0xff,0xff,0xfe},{{19,24,0xffffff,39}}};
            run(maximum,word16,serial,false);++checks;
            start(15,word16,serial);request(19,0);word(0,15,true);response(0,0,15);++checks;
            start(1,word16,serial);request(0,24);word(0x80000000,1,true);response(0,0,1);++checks;
            for (unsigned i=0;i<7;++i) {d.in_valid=1; d.in_bits=1; require(!d.in_ready,"extra input allowed");step();}
            d.in_valid=0;
            start(7,word16,serial);request(0,24);word(0,7,true);response(2,0,7);++checks;
            start(3,word16,serial);request(4,24);word(0x80000000,3,true);response(2,0,1);++checks;
            start(0,word16,serial);request(0,24);response(2,0,0);++checks;
            start(1,word16,serial);request(20,24);response(1,0,0);++checks;
            start(1,word16,serial);request(31,24);response(1,0,0);++checks;
            start(1,word16,serial);request(0,25);response(1,0,0);++checks;
            start(1,word16,serial);request(0,31);response(1,0,0);++checks;
            // Every bad source word is accepted exactly once and poisons the stream.
            for (unsigned kind=0;kind<6;++kind) {
                unsigned size=kind==4 ? 40 : 9;
                start(size,word16,serial);request(0,24);
                unsigned n=kind==0?0:kind==1?33:kind==2?8:kind==4?(word16?16:32):9;
                uint32_t data=kind==3?0x80000001:0x80000000;
                bool last=kind!=5;
                word(data,n,last);response(3,0,0);++checks;
                require(!d.in_ready,"failed stream still accepts input");
                request(0,24);response(3,0,0);++checks;
            }
            // Restart aborts a pending request with no source bytes delivered.
            start(100,word16,serial);request(19,24);step();
            start(1,word16,serial);request(0,24);word(0x80000000,1,true);response(0,0,1);++checks;
            // Reset aborts a pending request, disables both input interfaces.
            start(100,word16,serial);request(19,24);d.reset=1;step();d.reset=0;
            require(!d.req_ready && !d.in_ready && !d.out_valid,"reset did not disable stream");
            start(1,word16,serial);request(0,24);word(0x80000000,1,true);response(0,0,1);++checks;
            // Restart and reset each discard a held response without publication.
            for (bool reset_abort:{false,true}) {
                start(1,word16,serial);request(0,24);word(0x80000000,1,true);
                for (unsigned i=0;i<100 && !d.out_valid;++i) step();
                require(d.out_valid,"held abort setup watchdog");step();
                if (reset_abort) {d.reset=1;step();d.reset=0;require(!d.out_valid,"reset output abort");}
                start(1,word16,serial);request(0,24);word(0x80000000,1,true);response(0,0,1);++checks;
            }
        }
        return checks;
    }
};

static void print_result(const Result& r) {
    std::cout<<"\"cycles\":"<<r.cycles<<",\"input_accepted\":"<<r.inputs
      <<",\"symbols\":"<<r.symbols<<",\"consumed_bits\":"<<r.bits
      <<",\"input_wait\":"<<r.input_wait<<",\"output_stall\":"<<r.output_stall;
}

int main(int argc,char** argv) {
    Verilated::commandArgs(argc,argv);
    try {
        require(argc==3,"usage: tb_rice vectors.txt seed");
        const uint64_t seed=std::stoull(argv[2]); Sim sim(seed);
        unsigned directed=sim.directed();
        std::ifstream input(argv[1]);require(bool(input),"cannot open vectors");
        unsigned cases=0; uint64_t symbols=0;
        std::array<Result,8> totals{};
        while (input) {
            Case c; std::string hex; unsigned count=0;
            if (!(input>>c.id>>c.bits>>hex>>count)) break;
            if (hex!="-") for (size_t i=0;i<hex.size();i+=2) c.data.push_back(uint8_t(std::stoul(hex.substr(i,2),nullptr,16)));
            require(c.data.size()==(c.bits+7)/8,"bad input byte geometry");
            for (unsigned i=0;i<count;++i) {Request r{};require(bool(input>>r.k>>r.escape>>r.value>>r.position),"truncated request file");c.requests.push_back(r);}
            require(!c.requests.empty() || c.bits==0,"unused bits in empty request vector");
            for (unsigned config=0;config<8;++config) {
                bool serial=config&1, word16=config&2, stalls=config&4;
                auto r=sim.run(c,word16,serial,stalls);auto& t=totals[config];
                t.cycles+=r.cycles;t.inputs+=r.inputs;t.symbols+=r.symbols;t.bits+=r.bits;
                t.input_wait+=r.input_wait;t.output_stall+=r.output_stall;
                std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"serial\":"<<serial
                    <<",\"word_bits\":"<<(word16?16:32)<<",\"stalls\":"<<stalls<<",";
                print_result(r);std::cout<<"}\n";
            }
            ++cases;symbols+=count;
        }
        for (unsigned config=0;config<8;++config) {
            std::cout<<"{\"type\":\"total\",\"serial\":"<<bool(config&1)<<",\"word_bits\":"<<((config&2)?16:32)
                <<",\"stalls\":"<<bool(config&4)<<",";print_result(totals[config]);std::cout<<"}\n";
        }
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"cases\":"<<cases
            <<",\"requests_per_configuration\":"<<symbols<<",\"configurations\":8,\"directed_checks\":"<<directed
            <<",\"seed\":"<<seed<<"}\n";
        return 0;
    } catch (const std::exception& e) {std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
