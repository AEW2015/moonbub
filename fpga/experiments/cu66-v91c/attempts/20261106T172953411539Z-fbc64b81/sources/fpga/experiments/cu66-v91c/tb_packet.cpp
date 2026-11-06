#include "Vbr88_packet.h"
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
struct Case { std::string id; unsigned blocks=1,error=0,declared=0; std::vector<uint8_t> data; std::vector<Coef> expected; };
struct Result { uint64_t cycles=0,inputs=0,outputs=0,stall=0; };
struct Event { bool input,output; unsigned block,index,epoch; int value; };
static void require(bool b,const std::string& s){if(!b)throw std::runtime_error(s);}
static uint32_t crc32(const std::vector<uint8_t>& a,size_t size){uint32_t c=~0u;for(size_t i=0;i<size;++i){c^=a[i];for(unsigned j=0;j<8;++j)c=(c>>1)^((c&1)?0xedb88320u:0);}return ~c;}
static void put(std::vector<uint8_t>& a,unsigned at,uint32_t v){for(unsigned j=0;j<4;++j)a.at(at+j)=uint8_t(v>>(8*j));}
static void checksum(Case& c){put(c.data,unsigned(c.data.size()-4),crc32(c.data,c.data.size()-4));}
static Case simple(){Case c;c.id="directed-coded-zero";c.data.assign(71,0);c.data[0]='B';c.data[1]='R';c.data[2]='8';c.data[3]='8';c.data[4]=1;put(c.data,6,1);c.data[10]=1;
    put(c.data,14,7);for(unsigned j=1;j<4;++j)put(c.data,14+4*j,6);
    c.data[43]=255;put(c.data,44,1);c.data[48]=0x80;checksum(c);c.expected={{0,0,0}};return c;}
static Case raw(){Case c;c.id="directed-raw";c.data.assign(174,0);c.data[0]='B';c.data[1]='R';c.data[2]='8';c.data[3]='8';c.data[4]=1;c.data[5]=1;put(c.data,6,1);c.data[10]=1;put(c.data,14,128);
    for(unsigned i=0;i<64;++i){int v=i==0?-2048:i==63?2048:0;c.data[42+2*i]=uint8_t(v);c.data[43+2*i]=uint8_t(unsigned(v)>>8);c.expected.push_back({0,i,v});}checksum(c);return c;}
class Sim {
public:
    Vbr88_packet d; uint64_t rng,seed;bool held=false;Coef old{};unsigned old_epoch=0;
    explicit Sim(uint64_t s):rng(s),seed(s){d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=0;d.blocks=0;d.epoch=0;d.word16=0;d.serial_mode=0;d.in_valid=0;d.in_data=0;d.in_last=0;d.out_ready=0;step();d.reset=0;}
    uint32_t random(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint32_t(rng);}
    Event step(){d.clk=0;d.eval();bool cancel=d.reset||d.start||d.abort_packet;
        if(held&&!cancel){require(d.out_valid,"held output dropped");require(d.out_block==old.block&&d.out_index==old.index&&int16_t(d.out_coefficient)==old.value&&d.out_epoch==old_epoch,"held output changed");}
        if(cancel)require(!d.out_valid&&!d.in_ready,"cancel edge accepted stale transaction");
        Event e{bool(d.in_valid&&d.in_ready),bool(d.out_valid&&d.out_ready),d.out_block,d.out_index,d.out_epoch,int16_t(d.out_coefficient)};
        held=d.out_valid&&!d.out_ready&&!cancel;old={d.out_block,d.out_index,int16_t(d.out_coefficient)};old_epoch=d.out_epoch;
        d.clk=1;d.eval();d.clk=0;d.eval();return e;
    }
    void start(const Case& c,bool w16,bool serial,unsigned epoch=0xa5c391cU){d.in_valid=0;d.out_ready=0;d.packet_bytes=c.declared?c.declared:c.data.size();d.blocks=c.blocks;d.epoch=epoch;d.word16=w16;d.serial_mode=serial;d.start=1;step();d.start=0;
        require(!d.out_valid&&d.count_inputs==0&&d.count_outputs==0,"start flush");
        d.packet_bytes=0;d.blocks=0;d.epoch=0;d.word16=!w16;d.serial_mode=!serial;
    }
    Result run(const Case& c,bool w16,bool serial,bool stalls){rng=1469598103934665603ULL;for(unsigned char v:c.id){rng^=v;rng*=1099511628211ULL;}rng^=seed;if(!rng)rng=1;
        start(c,w16,serial);unsigned loaded=0,completed=0;bool pending=false;uint64_t cycles=0,stall=0;
        while(!d.done&&!d.error){require(++cycles<uint64_t(c.data.size())*300+10000,"watchdog "+c.id);
            // Exactly two cycle-indexed draws, shared across word widths and serial controls.
            bool offer=random()%4!=0,ready=random()%4!=0;
            if(!pending&&loaded<c.data.size()&&(!stalls||offer)){d.in_data=c.data[loaded];d.in_last=loaded+1==c.data.size();pending=true;}
            d.in_valid=pending;d.out_ready=!stalls||ready;d.eval();if(d.out_valid&&!d.out_ready)++stall;
            Event e=step();if(e.input){++loaded;pending=false;}
            if(e.output){require(completed<c.expected.size(),"unexpected output "+c.id);const auto&a=c.expected[completed];
                require(e.block==a.block&&e.index==a.index&&e.value==a.value&&e.epoch==0xa5c391cU,"coefficient mismatch "+c.id+" event "+std::to_string(completed));++completed;}
        }
        require(d.error==c.error,"error mismatch "+c.id+" got "+std::to_string(d.error)+" expected "+std::to_string(c.error));require(bool(d.done)==(c.error==0),"done/error "+c.id);require(completed==c.expected.size(),"output count "+c.id);
        require(d.count_cycles==cycles&&d.count_inputs==loaded&&d.count_outputs==completed&&d.count_output_stall==stall,"counter mismatch "+c.id);
        Result r{cycles,loaded,completed,stall};d.in_valid=0;d.out_ready=1;
        for(unsigned j=0;j<4;++j){step();require(!d.in_ready&&!d.out_valid&&d.error==c.error&&bool(d.done)==(c.error==0),"terminal state changed");}return r;
    }
    unsigned directed(){unsigned checks=0;for(bool serial:{false,true})for(bool w16:{false,true}){
        Case base=simple(),c;std::vector<Case> cases;cases.push_back(base);cases.push_back(raw());
        auto bad=[&](std::string id,unsigned at,uint32_t value,unsigned err,bool update=true){c=base;c.id=id;c.expected.clear();c.error=err;put(c.data,at,value);if(update)checksum(c);cases.push_back(c);};
        bad("bad-crc",44,2,3,false);bad("bad-magic",0,0,4);bad("bad-block-binding",6,2,4);bad("bad-reserved-binding",10,2,4);
        bad("bad-length-sum",14,8,4);bad("length-sum-overflow",14,0xffffffff,4);bad("short-stream",14,5,4);
        bad("bad-bit-size",44,8,7);bad("huge-bit-size",44,0xfffffff8,4);bad("bad-dc-k",42,0x0001ff0e,4);
        c=base;c.id="bad-version";c.data[4]=2;c.error=4;c.expected.clear();checksum(c);cases.push_back(c);
        c=base;c.id="bad-flags";c.data[5]=2;c.error=4;c.expected.clear();checksum(c);cases.push_back(c);
        c=base;c.id="bad-padding";c.data[48]|=1;c.error=7;c.expected.clear();checksum(c);cases.push_back(c);
        c=base;c.id="bad-ac-k";c.data[49]=20;c.error=4;c.expected.clear();checksum(c);cases.push_back(c);
        c=base;c.id="bad-ac-count";put(c.data,30,6);c.error=4;c.expected.clear();checksum(c);cases.push_back(c);
        c=base;c.id="truncated-input";c.data.pop_back();c.declared=71;c.error=2;c.expected.clear();cases.push_back(c);
        c=base;c.id="late-last";c.data.push_back(0);c.declared=71;c.error=2;c.expected.clear();cases.push_back(c);
        c=base;c.id="trailing-packet-byte";c.data.insert(c.data.end()-4,0);c.error=4;c.expected.clear();checksum(c);cases.push_back(c);
        c=base;c.id="bounds-zero-blocks";c.blocks=0;c.error=1;c.expected.clear();cases.push_back(c);
        c=base;c.id="bounds-many-blocks";c.blocks=65537;c.error=1;c.expected.clear();cases.push_back(c);
        c=base;c.id="bounds-cap";c.declared=49153;c.error=1;c.expected.clear();cases.push_back(c);
        c=base;c.id="bounds-raw";c.declared=175;c.error=1;c.expected.clear();cases.push_back(c);
        c=base;c.id="bounds-minimum";c.declared=45;c.error=1;c.expected.clear();cases.push_back(c);
        c=raw();c.id="raw-invalid-range-first";put(c.data,42,2049);c.error=5;c.expected.clear();checksum(c);cases.push_back(c);
        c=raw();c.id="raw-invalid-fields";put(c.data,30,1);c.error=4;c.expected.clear();checksum(c);cases.push_back(c);
        c=raw();c.id="raw-invalid-range-last";c.data[168]=1;c.data[169]=8;c.error=5;c.expected.pop_back();checksum(c);cases.push_back(c);
        for(const auto&t:cases){run(t,w16,serial,true);++checks;}
        // Final coefficient must remain held, and done must wait for acceptance.
        start(base,w16,serial);unsigned at=0;
        for(unsigned j=0;j<1000&&!d.out_valid;++j){d.in_valid=at<base.data.size();if(d.in_valid){d.in_data=base.data[at];d.in_last=at+1==base.data.size();}if(step().input)++at;}
        require(d.out_valid&&!d.done,"held final setup");for(unsigned j=0;j<20;++j){step();require(d.out_valid&&!d.done&&d.count_outputs==0,"final credit fence");}
        d.out_ready=1;require(step().output,"final accepted");for(unsigned j=0;j<20&&!d.done;++j)step();require(d.done,"all-context completion");++checks;
        // Cancel in ingress, post-CRC metadata, replay, and held-output phases.
        for(unsigned phase=0;phase<4;++phase)for(unsigned action=0;action<3;++action){start(base,w16,serial,11);at=0;bool reached=false;
            for(unsigned j=0;j<1000;++j){d.in_valid=at<base.data.size();if(d.in_valid){d.in_data=base.data[at];d.in_last=at+1==base.data.size();}if(step().input)++at;
                if((phase==0&&at==5)||(phase==1&&d.debug_state==3)||(phase==2&&d.debug_state==5)||(phase==3&&d.out_valid)){reached=true;break;}}
            require(reached,"cancel setup");d.out_ready=1;
            if(action==0)d.abort_packet=1;else if(action==1){d.reset=1;d.start=1;}else {d.start=1;d.packet_bytes=base.data.size();d.blocks=1;d.epoch=22;d.word16=w16;d.serial_mode=serial;}
            Event e=step();require(!e.input&&!e.output,"cancel stale edge");d.abort_packet=0;d.reset=0;d.start=0;require(!d.done&&!d.error&&!d.out_valid,"cancel flush");run(base,w16,serial,true);++checks;
        }
    }return checks;}
};
static void print(const Result&r){std::cout<<"\"cycles\":"<<r.cycles<<",\"input_accepted\":"<<r.inputs<<",\"outputs\":"<<r.outputs<<",\"output_stall\":"<<r.stall;}
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);try{require(argc==3,"usage: tb_packet vectors.txt seed");uint64_t seed=std::stoull(argv[2]);Sim sim(seed);unsigned directed=sim.directed(),cases=0;uint64_t outputs=0;std::array<Result,8>totals{};std::ifstream input(argv[1]);require(bool(input),"cannot open vectors");
    while(input){Case c;std::string hex;unsigned n=0;if(!(input>>c.id>>c.blocks>>hex>>c.error>>n))break;for(size_t i=0;i<hex.size();i+=2)c.data.push_back(uint8_t(std::stoul(hex.substr(i,2),nullptr,16)));for(unsigned i=0;i<n;++i){Coef a{};require(bool(input>>a.block>>a.index>>a.value),"truncated vector");c.expected.push_back(a);}
        for(unsigned cfg=0;cfg<8;++cfg){auto r=sim.run(c,cfg&2,cfg&1,cfg&4);auto&t=totals[cfg];t.cycles+=r.cycles;t.inputs+=r.inputs;t.outputs+=r.outputs;t.stall+=r.stall;std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"serial\":"<<bool(cfg&1)<<",\"word_bits\":"<<((cfg&2)?16:32)<<",\"stalls\":"<<bool(cfg&4)<<",";print(r);std::cout<<"}\n";}++cases;outputs+=n;}
    for(unsigned cfg=0;cfg<8;++cfg){std::cout<<"{\"type\":\"total\",\"serial\":"<<bool(cfg&1)<<",\"word_bits\":"<<((cfg&2)?16:32)<<",\"stalls\":"<<bool(cfg&4)<<",";print(totals[cfg]);std::cout<<"}\n";}
    std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"outputs_per_configuration\":"<<outputs<<",\"configurations\":8,\"directed_checks\":"<<directed<<",\"seed\":"<<seed<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
