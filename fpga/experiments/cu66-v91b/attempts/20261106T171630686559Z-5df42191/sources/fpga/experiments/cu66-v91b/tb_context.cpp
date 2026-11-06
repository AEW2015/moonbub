#include "Vbr88_context.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
struct Coef { unsigned block,index; int value; };
struct Case {
    std::string id; unsigned blocks=1,band=0,k0=0,k1=255,events=1,bits=0,error=0;
    std::vector<uint8_t> data; std::vector<Coef> expected;
};
struct Result { uint64_t cycles=0,inputs=0,symbols=0,bits=0,outputs=0,input_wait=0,output_stall=0; };
struct Event { bool input,output; unsigned block,index,epoch; int value; };
static void require(bool b,const std::string& s) { if(!b) throw std::runtime_error(s); }
static void rice(std::vector<bool>& b,unsigned value,unsigned k,unsigned escape,bool force=false) {
    unsigned q=force?15:value>>k;
    if(q>=15) {b.insert(b.end(),15,false);for(int j=int(escape)-1;j>=0;--j)b.push_back((value>>j)&1);}
    else {b.insert(b.end(),q,false);b.push_back(true);for(int j=int(k)-1;j>=0;--j)b.push_back((value>>j)&1);}
}
static void pack(Case& c,const std::vector<bool>& b) {
    c.bits=b.size();c.data.assign((b.size()+7)/8,0);
    for(unsigned i=0;i<b.size();++i)c.data[i/8]|=unsigned(b[i])<<(7-i%8);
}
class Sim {
public:
    Vbr88_context d; uint64_t rng,seed; bool held=false; Coef previous{}; unsigned previous_epoch=0;
    explicit Sim(uint64_t s):rng(s),seed(s) {
        d.clk=0;d.reset=1;d.start=0;d.abort_context=0;d.blocks=1;d.band=0;d.k0=0;d.k1=255;
        d.event_count=1;d.stream_bits=0;d.epoch=0;d.word16=0;d.serial_mode=0;
        d.in_valid=0;d.in_data=0;d.in_bits=0;d.in_last=0;d.out_ready=0;step();d.reset=0;
    }
    uint32_t random(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint32_t(rng);}
    Event step() {
        d.clk=0;d.eval();
        if(held&&!d.reset&&!d.abort_context&&!d.start) {
            require(d.out_valid,"held valid dropped");
            require(d.out_block==previous.block&&d.out_index==previous.index&&int16_t(d.out_coefficient)==previous.value&&d.out_epoch==previous_epoch,"held payload changed");
        }
        Event e{bool(d.in_valid&&d.in_ready),bool(d.out_valid&&d.out_ready),d.out_block,d.out_index,d.out_epoch,int16_t(d.out_coefficient)};
        held=d.out_valid&&!d.out_ready&&!d.reset&&!d.abort_context&&!d.start;
        previous={d.out_block,d.out_index,int16_t(d.out_coefficient)};previous_epoch=d.out_epoch;
        d.clk=1;d.eval();d.clk=0;d.eval();
        require(d.reservoir_bits<=64,"reservoir overflow");return e;
    }
    void start(const Case& c,bool word16,bool serial,unsigned epoch=0xa5c391bU) {
        d.in_valid=0;d.out_ready=0;d.word16=word16;d.serial_mode=serial;d.blocks=c.blocks;d.band=c.band;
        d.k0=c.k0;d.k1=c.k1;d.event_count=c.events;d.stream_bits=c.bits;d.epoch=epoch;
        d.start=1;step();d.start=0;require(!d.out_valid,"start output flush");
        require(d.count_cycles==0&&d.count_outputs==0&&d.consumed_bits==0,"start counters");
        // All metadata are caller-owned wires after the start edge.
        d.blocks=0;d.band=255;d.k0=255;d.k1=0;d.event_count=0;d.stream_bits=0;d.epoch=0;d.word16=!word16;d.serial_mode=!serial;
    }
    Result run(const Case& c,bool word16,bool serial,bool stalls) {
        rng=1469598103934665603ULL;for(unsigned char v:c.id){rng^=v;rng*=1099511628211ULL;}
        rng^=seed^(word16?0x16161616ULL:0x32323232ULL);if(!rng)rng=1;
        const unsigned epoch=0xa5c391bU;start(c,word16,serial,epoch);
        unsigned loaded=0,completed=0;bool pending=false;uint64_t cycles=0,inputs=0,stalled=0;
        while(!d.done&&!d.error) {
            require(++cycles<uint64_t(c.bits)*24+uint64_t(c.events)*100+2000,"watchdog "+c.id);
            bool offer=random()%4!=0,ready=random()%4!=0;
            if(!pending&&loaded<c.bits&&(!stalls||offer)) {
                unsigned n=std::min(word16?16u:32u,c.bits-loaded);uint32_t v=0;
                for(unsigned j=0;j<n;++j)v|=uint32_t((c.data[(loaded+j)/8]>>(7-(loaded+j)%8))&1)<<(31-j);
                d.in_data=v;d.in_bits=n;d.in_last=loaded+n==c.bits;pending=true;
            }
            d.in_valid=pending;d.out_ready=!stalls||ready;d.eval();
            if(d.out_valid&&!d.out_ready)++stalled;
            Event e=step();
            if(e.input){loaded+=d.in_bits;++inputs;pending=false;}
            if(e.output){
                require(completed<c.expected.size(),"unexpected output "+c.id);
                const auto& a=c.expected[completed];
                require(e.block==a.block&&e.index==a.index&&e.value==a.value&&e.epoch==epoch,"coefficient mismatch "+c.id+" event "+std::to_string(completed)+" got "+std::to_string(e.block)+":"+std::to_string(e.index)+":"+std::to_string(e.value));
                ++completed;
            }
        }
        require(d.error==c.error,"error mismatch "+c.id+" got "+std::to_string(d.error)+" expected "+std::to_string(c.error));
        require(bool(d.done)==(c.error==0),"done/error "+c.id);
        require(completed==c.expected.size(),"output count "+c.id);
        require(d.count_cycles==cycles&&d.count_inputs==inputs&&d.count_outputs==completed&&d.count_output_stall==stalled,"counter mismatch "+c.id);
        if(!c.error)require(d.consumed_bits==c.bits&&loaded==c.bits,"exact end "+c.id);
        Result result{cycles,inputs,d.count_symbols,d.consumed_bits,completed,d.count_input_wait,stalled};
        d.in_valid=0;d.out_ready=1;
        for(unsigned i=0;i<4;++i){step();require(!d.out_valid&&!d.in_ready,"terminal context leaked "+c.id);require(d.error==c.error,"sticky error changed");}
        require(d.count_cycles==cycles,"terminal cycles changed");return result;
    }
    unsigned directed() {
        unsigned checks=0;
        for(bool serial:{false,true})for(bool word16:{false,true}) {
            std::vector<Case> tests;
            Case c;c.id="bad-blocks-zero";c.blocks=0;c.events=0;c.error=4;tests.push_back(c);
            c.id="bad-blocks-large";c.blocks=65537;c.events=65537;tests.push_back(c);
            c=Case{};c.id="bad-band";c.band=4;c.error=4;tests.push_back(c);
            c=Case{};c.id="bad-dc-count";c.events=0;c.error=4;tests.push_back(c);
            c=Case{};c.id="bad-dc-k0";c.k0=14;c.error=4;tests.push_back(c);
            c.id="bad-dc-k0-255";c.k0=255;tests.push_back(c);
            c=Case{};c.id="bad-dc-k1";c.k1=31;c.error=4;tests.push_back(c);
            c=Case{};c.id="bad-ac-k0";c.band=1;c.k0=20;c.k1=0;c.error=4;tests.push_back(c);
            c.id="bad-ac-k1";c.k0=0;c.k1=12;tests.push_back(c);
            c.id="bad-ac-count";c.k1=0;c.events=6;tests.push_back(c);
            c=Case{};c.id="dc-eof-prefix";c.error=2;tests.push_back(c);
            c.id="dc-eof-zeros";pack(c,std::vector<bool>(7,false));tests.push_back(c);
            c.id="dc-eof-suffix";c.k0=13;pack(c,{true});tests.push_back(c);
            c=Case{};c.id="dc-overflow";c.error=5;std::vector<bool>b;rice(b,4097,0,14,true);pack(c,b);tests.push_back(c);
            c=Case{};c.id="dc-exact-extra";c.error=7;pack(c,{true,false});tests.push_back(c);
            c=Case{};c.id="ac-empty-extra";c.band=1;c.k1=0;c.events=0;c.error=7;pack(c,{false});tests.push_back(c);
            c=Case{};c.id="ac-run-overflow";c.band=1;c.k1=0;c.error=6;b.clear();rice(b,5,0,24);pack(c,b);tests.push_back(c);
            c.id="ac-run-max";b.clear();rice(b,0xffffff,0,24,true);pack(c,b);tests.push_back(c);
            c=Case{};c.id="ac-level-overflow";c.band=1;c.k1=0;c.error=5;// A normal k11 suffix can represent4096, beyond the signed range.
            c.k1=11;b.clear();rice(b,0,0,24);rice(b,4096,11,12);pack(c,b);tests.push_back(c);
            c=Case{};c.id="ac-second-run-overflow";c.band=1;c.k1=0;c.events=2;c.error=6;b.clear();rice(b,4,0,24);rice(b,0,0,12);rice(b,0,0,24);pack(c,b);c.expected={{0,2,-1}};tests.push_back(c);
            for(const auto& t:tests){run(t,word16,serial,true);++checks;}
            c=Case{};c.id="ac-eof-level";c.band=1;c.k1=0;c.error=2;pack(c,{true});run(c,word16,serial,true);++checks;
            c=Case{};c.id="ac-maximum-position";c.blocks=65536;c.band=3;c.k1=0;
            b.clear();rice(b,65536u*43u-1u,0,24,true);rice(b,0,0,12);pack(c,b);c.expected={{65535,63,-1}};run(c,word16,serial,true);++checks;
            // Hold the final slot for20 edges: no done, no next symbols, stable
            // output, and publication only on the eventual acceptance edge.
            c=Case{};pack(c,{true});start(c,word16,serial);d.in_valid=1;d.in_data=0x80000000;d.in_bits=1;d.in_last=1;
            for(unsigned j=0;j<100&&!d.out_valid;++j){if(step().input)d.in_valid=0;}
            require(d.out_valid&&!d.done,"final held setup");
            uint64_t completed_symbols=d.count_symbols;
            for(unsigned j=0;j<20;++j){step();require(d.out_valid&&!d.done&&d.count_outputs==0&&d.count_symbols==completed_symbols,"finite output credit");}
            d.out_ready=1;require(step().output&&d.done&&!d.out_valid,"done final acceptance fence");++checks;
            // Bad source-word metadata reaches and poisons the outstanding DC.
            for(unsigned kind=0;kind<4;++kind){
                c=Case{};c.bits=9;start(c,word16,serial);d.in_valid=1;d.in_data=kind==2?0x80000001:0x80000000;
                d.in_bits=kind==0?8:kind==1?0:9;d.in_last=kind!=3;
                bool accepted=false;for(unsigned j=0;j<30;++j){if(step().input){accepted=true;d.in_valid=0;break;}}
                require(accepted,"bad word acceptance");for(unsigned j=0;j<100&&!d.error;++j)step();
                require(d.error==3&&!d.out_valid&&!d.done,"bad word error");++checks;
            }
            // Abort/reset/restart at an outstanding run, a retained run before
            // its level, and a held coefficient; the new epoch must own output.
            for(unsigned phase=0;phase<3;++phase)for(unsigned action=0;action<3;++action){
                c=Case{};c.band=1;c.k1=0;c.bits=2;start(c,word16,serial,11);
                unsigned loaded=0;
                for(unsigned j=0;j<150;++j){
                    if(phase>0&&loaded==0){d.in_valid=1;d.in_data=0xc0000000;d.in_bits=2;d.in_last=1;}
                    if(step().input){loaded=2;d.in_valid=0;}
                    if((phase==0&&d.debug_state==4)||(phase==1&&d.debug_state==5)||(phase==2&&d.out_valid))break;
                }
                require((phase==0&&d.debug_state==4)||(phase==1&&d.debug_state==5)||(phase==2&&d.out_valid),"abort setup");
                if(action==0){d.abort_context=1;step();d.abort_context=0;}
                if(action==1){d.reset=1;d.start=1;step();d.reset=0;d.start=0;}
                if(action<2)require(!d.out_valid&&!d.in_ready&&!d.done&&d.error==0,"flush priority");
                Case fresh;fresh.id="fresh-epoch";pack(fresh,{true});fresh.expected={{0,0,0}};run(fresh,word16,serial,true);++checks;
            }
        }return checks;
    }
};
static void print(const Result& r){std::cout<<"\"cycles\":"<<r.cycles<<",\"input_accepted\":"<<r.inputs<<",\"symbols\":"<<r.symbols<<",\"consumed_bits\":"<<r.bits<<",\"outputs\":"<<r.outputs<<",\"input_wait\":"<<r.input_wait<<",\"output_stall\":"<<r.output_stall;}
int main(int argc,char**argv){
    Verilated::commandArgs(argc,argv);
    try{
        require(argc==3,"usage: tb_context vectors.txt seed");uint64_t seed=std::stoull(argv[2]);Sim sim(seed);
        unsigned directed=sim.directed(),cases=0;uint64_t outputs=0;std::array<Result,8> totals{};
        std::ifstream input(argv[1]);require(bool(input),"cannot open vectors");
        while(input){Case c;std::string hex;unsigned n=0;
            if(!(input>>c.id>>c.blocks>>c.band>>c.k0>>c.k1>>c.events>>c.bits>>hex>>c.error>>n))break;
            if(hex!="-")for(size_t i=0;i<hex.size();i+=2)c.data.push_back(uint8_t(std::stoul(hex.substr(i,2),nullptr,16)));
            require(c.data.size()==(c.bits+7)/8,"vector byte geometry");
            for(unsigned i=0;i<n;++i){Coef a{};require(bool(input>>a.block>>a.index>>a.value),"truncated coefficient vector");c.expected.push_back(a);}
            for(unsigned cfg=0;cfg<8;++cfg){bool serial=cfg&1,w16=cfg&2,stalls=cfg&4;auto r=sim.run(c,w16,serial,stalls);auto&t=totals[cfg];
                t.cycles+=r.cycles;t.inputs+=r.inputs;t.symbols+=r.symbols;t.bits+=r.bits;t.outputs+=r.outputs;t.input_wait+=r.input_wait;t.output_stall+=r.output_stall;
                std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"serial\":"<<serial<<",\"word_bits\":"<<(w16?16:32)<<",\"stalls\":"<<stalls<<",";print(r);std::cout<<"}\n";
            }++cases;outputs+=n;
        }
        for(unsigned cfg=0;cfg<8;++cfg){std::cout<<"{\"type\":\"total\",\"serial\":"<<bool(cfg&1)<<",\"word_bits\":"<<((cfg&2)?16:32)<<",\"stalls\":"<<bool(cfg&4)<<",";print(totals[cfg]);std::cout<<"}\n";}
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"outputs_per_configuration\":"<<outputs<<",\"configurations\":8,\"directed_checks\":"<<directed<<",\"seed\":"<<seed<<"}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
