#include "Vbr88_pipeline.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool value,const std::string& message) { if(!value) throw std::runtime_error(message); }
static std::vector<uint8_t> hexbytes(const std::string& s) {
    require(s.size()%2==0,"odd hex length"); std::vector<uint8_t> data;
    for(size_t i=0;i<s.size();i+=2) data.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));
    return data;
}
struct Case {std::string id;unsigned blocks=0;std::vector<uint8_t> packet,dense,packed;};
struct Counts {uint64_t cycles=0,input=0,dense=0,reads=0,writes=0,stalls=0,metadata_wait=0,memory_wait=0;};
struct Edge {bool input,output,request,response;unsigned block,index,epoch;int value;};

class Sim {
public:
    Vbr88_pipeline d;
    std::array<uint8_t,262144> ram{};
    std::array<uint32_t,16384> line_epoch{};
    struct Request {bool valid=false,write=false;unsigned address=0,epoch=0;std::array<uint32_t,4> data{};uint64_t due=0,accepted=0;} pending;
    uint64_t cycle=0,rng=1,seed;
    uint32_t next_epoch=0,current_epoch=0;
    bool slow=false,req_held=false,out_held=false;
    std::array<uint32_t,4> old_req_data{};
    unsigned old_req_address=0,old_req_epoch=0;bool old_req_write=false;
    unsigned old_block=0,old_index=0,old_epoch=0;int old_value=0;
    uint64_t min_response_delay=~uint64_t(0),max_response_delay=0;
    unsigned injected_error=0;

    explicit Sim(uint64_t s):seed(s) {
        ram.fill(0xa5);line_epoch.fill(0xffffffffU);
        d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=0;d.blocks=0;d.epoch=0;
        d.serial_clear=0;d.in_valid=0;d.in_data=0;d.in_last=0;d.out_ready=0;
        d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;
        for(unsigned j=0;j<4;++j)d.mem_rsp_data[j]=0;
        step(true);d.reset=0;
    }
    uint32_t random(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint32_t(rng);}

    Edge step(bool offer=true) {
        d.mem_req_ready=!pending.valid&&(!slow||offer);
        d.mem_rsp_valid=pending.valid&&cycle>=pending.due;
        d.mem_rsp_epoch=pending.epoch;d.mem_rsp_error=d.mem_rsp_valid&&injected_error;
        for(unsigned j=0;j<4;++j) {
            uint32_t value=0;
            if(pending.valid&&!pending.write)for(unsigned b=0;b<4;++b)value|=uint32_t(ram[pending.address+4*j+b])<<(8*b);
            d.mem_rsp_data[j]=value;
        }
        d.clk=0;d.eval();bool cancel=d.reset||d.start||d.abort_packet;
        if(cancel)require(!d.out_valid&&!d.in_ready,"cancel edge accepted output/input");
        if(req_held&&!cancel) {
            require(d.mem_req_valid,"held memory request dropped");
            require(d.mem_req_write==old_req_write&&d.mem_req_addr==old_req_address&&d.mem_req_epoch==old_req_epoch,"held memory request fields changed");
            for(unsigned j=0;j<4;++j)require(d.mem_req_data[j]==old_req_data[j],"held memory request data changed");
        }
        if(out_held&&!cancel)require(d.out_valid&&d.out_block==old_block&&d.out_index==old_index&&
            int16_t(d.out_value)==old_value&&d.out_epoch==old_epoch,"held dense output changed");
        req_held=d.mem_req_valid&&!d.mem_req_ready&&!cancel;
        old_req_address=d.mem_req_addr;old_req_epoch=d.mem_req_epoch;old_req_write=d.mem_req_write;
        for(unsigned j=0;j<4;++j)old_req_data[j]=d.mem_req_data[j];
        out_held=d.out_valid&&!d.out_ready&&!cancel;
        old_block=d.out_block;old_index=d.out_index;old_epoch=d.out_epoch;old_value=int16_t(d.out_value);
        Edge e{bool(d.in_valid&&d.in_ready),bool(d.out_valid&&d.out_ready),
            bool(d.mem_req_valid&&d.mem_req_ready),bool(d.mem_rsp_valid&&d.mem_rsp_ready),
            d.out_block,d.out_index,d.out_epoch,int16_t(d.out_value)};
        Request accepted;
        if(e.request) {
            require(!pending.valid,"more than one outstanding memory request");
            require((d.mem_req_addr&15)==0&&d.mem_req_addr+16<=d.used_bytes,"memory address bound");
            accepted.valid=true;accepted.write=d.mem_req_write;accepted.address=d.mem_req_addr;accepted.epoch=d.mem_req_epoch;
            for(unsigned j=0;j<4;++j)accepted.data[j]=d.mem_req_data[j];
            unsigned latency=slow?(accepted.write?16:18)+unsigned(((accepted.address>>4)^accepted.epoch^seed)&3):1;
            accepted.due=cycle+latency;accepted.accepted=cycle;
            if(!accepted.write)require(line_epoch[accepted.address/16]==accepted.epoch,"read from unwritten/stale memory line");
        }
        d.clk=1;d.eval();d.clk=0;d.eval();
        if(e.response) {
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
        ++cycle;return e;
    }

    void start(const Case& c,bool clear) {
        current_epoch=++next_epoch;
        d.in_valid=0;d.out_ready=0;d.packet_bytes=c.packet.size();d.blocks=c.blocks;d.epoch=current_epoch;d.serial_clear=clear;
        d.start=1;step();d.start=0;
        require(!d.done&&!d.error&&d.count_cycles==0,"start status/counter flush");
        d.packet_bytes=0;d.blocks=0;d.epoch=0;d.serial_clear=!clear;
    }

    Counts run(const Case& c,bool clear,bool delayed,unsigned expected_error=0,bool check_image=true) {
        slow=delayed;rng=1469598103934665603ULL;
        for(unsigned char ch:c.id){rng^=ch;rng*=1099511628211ULL;}rng^=seed;if(!rng)rng=1;
        start(c,clear);Counts n;size_t supplied=0,produced=0;bool held=false;
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
                produced+=2;++n.dense;
            }
        }
        require(d.error==expected_error,"pipeline error "+c.id+" got "+std::to_string(d.error)+" expected "+std::to_string(expected_error));
        require(bool(d.done)==(expected_error==0),"pipeline completion status "+c.id);
        if(!expected_error) {
            require(produced==c.dense.size()&&supplied==c.packet.size(),"packet/dense completion counts");
            require(d.used_bytes==c.packed.size()&&!pending.valid,"used bytes or final memory ACK");
            require(n.reads==n.writes&&n.writes==c.packed.size()/16,"packed burst accounting "+c.id);
            if(check_image)require(std::equal(c.packed.begin(),c.packed.end(),ram.begin()),"packed memory image mismatch "+c.id);
        }
        require(d.count_cycles==n.cycles&&d.count_input_bytes==n.input&&d.count_dense==n.dense&&
            d.count_reads==n.reads&&d.count_writes==n.writes&&d.count_dense_stall==n.stalls,"integrated counters "+c.id);
        d.in_valid=0;d.out_ready=1;
        for(unsigned j=0;j<4;++j){step();require(!d.out_valid&&!d.in_ready,"terminal data leaked");}
        return n;
    }

    unsigned directed(const Case& simple) {
        unsigned checks=0;
        Case bad=simple;bad.id="crc-corruption";bad.packet.back()^=1;
        run(bad,false,true,0x13,false);++checks;
        bad=simple;bad.id="invalid-block-bound";bad.blocks=0;
        run(bad,false,true,0x11,false);++checks;
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
        return checks;
    }
};

static void print(const Counts& n) {
    std::cout<<"\"cycles\":"<<n.cycles<<",\"input_bytes\":"<<n.input<<",\"dense_coefficients\":"<<n.dense
        <<",\"read_requests\":"<<n.reads<<",\"write_requests\":"<<n.writes<<",\"output_stalls\":"<<n.stalls
        <<",\"metadata_wait\":"<<n.metadata_wait<<",\"memory_pending_edges\":"<<n.memory_wait;
}
int main(int argc,char** argv) {
    Verilated::commandArgs(argc,argv);
    try {
        require(argc==3,"usage: tb_pipeline vectors.txt seed");Sim sim(std::stoull(argv[2]));
        std::ifstream stream(argv[1]);require(bool(stream),"cannot open vector text");
        std::vector<Case> cases;std::string packet,dense,packed;
        for(Case c;stream>>c.id>>c.blocks>>packet>>dense>>packed;) {
            c.packet=hexbytes(packet);c.dense=hexbytes(dense);c.packed=hexbytes(packed);cases.push_back(c);
        }
        require(cases.size()==17,"vector count");
        auto simple=std::find_if(cases.begin(),cases.end(),[](const Case& c){return c.blocks==1&&c.packet.size()<100;});
        require(simple!=cases.end(),"no simple packet for cancellation checks");
        unsigned checks=sim.directed(*simple);uint64_t dense_count=0;
        for(const auto& c:cases)for(unsigned profile=0;profile<2;++profile)for(unsigned clear=0;clear<2;++clear) {
            Counts n=sim.run(c,clear,profile);dense_count+=n.dense;
            std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"serial_clear\":"<<clear
                <<",\"memory_profile\":"<<profile<<",\"used_bytes\":"<<c.packed.size()<<",";print(n);std::cout<<"}\n";
        }
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<sim.seed
            <<",\"packets\":"<<cases.size()<<",\"configurations\":4,\"case_rows\":"<<cases.size()*4
            <<",\"dense_comparisons\":"<<dense_count<<",\"directed_checks\":"<<checks
            <<",\"minimum_memory_response_delay\":"<<sim.min_response_delay
            <<",\"maximum_memory_response_delay\":"<<sim.max_response_delay<<"}\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
