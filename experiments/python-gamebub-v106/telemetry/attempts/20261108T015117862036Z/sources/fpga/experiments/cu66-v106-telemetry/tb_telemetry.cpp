#include "Vtelemetry_probe.h"
#include "Vtelemetry_probe___024root.h"
#include "Vtelemetry_probe_br88_packet_ingress_v91h.h"
#include "Vtelemetry_probe_packed_scratch_v91g2.h"
#include <random>
static void telemetry_pre(Vtelemetry_probe&);
static void telemetry_post(Vtelemetry_probe&);
#include "historical_pipeline.cpp"
#define OLD(n) r.telemetry_probe__DOT__old_dut__DOT__##n
#define NEW(n) r.telemetry_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do{const auto x=(v);OLD(n)=x;NEW(n)=x;}while(0)
#define PKTBOTH(n,v) do{const auto x=(v);r.__PVT__telemetry_probe__DOT__old_dut__DOT__packet_decoder->synchronous__DOT__ingress__DOT__##n=x;r.__PVT__telemetry_probe__DOT__new_dut__DOT__packet_decoder->synchronous__DOT__ingress__DOT__##n=x;}while(0)
#define SCRBOTH(n,v) do{const auto x=(v);r.__PVT__telemetry_probe__DOT__old_dut__DOT__scratch->n=x;r.__PVT__telemetry_probe__DOT__new_dut__DOT__scratch->n=x;}while(0)
struct CounterOracle {
    std::array<uint64_t,52> values{};
    uint64_t clocks=0,logged=0;unsigned guards=0,e=0,p=0,s=0;bool running=false;
    std::string phase="prepared";std::ofstream*trace=nullptr;
} oracle;
static uint64_t observed(const Vtelemetry_probe&d,unsigned i){return i<4?d.count_emitter_state[i]:i<20?d.count_packet_state[i-4]:d.count_scratch_state[i-20];}
static void telemetry_pre(Vtelemetry_probe&d){
    require(d.probe_outputs_equal,"whole production preedge outputs differ");
    for(unsigned i=0;i<52;++i)require(observed(d,i)==oracle.values[i],"independent preedge52word oracle");
    oracle.guards=unsigned(d.reset)|unsigned(d.start)*2|unsigned(d.abort_packet)*4;
    oracle.running=d.dbg_running;oracle.e=d.dbg_emitter_state;oracle.p=d.packet_state;oracle.s=d.dbg_scratch_state;
    require(oracle.e<4&&oracle.p<16&&oracle.s<32,"counter selector bounds");
    if(oracle.guards)oracle.values.fill(0);
    else if(oracle.running){++oracle.values[oracle.e];++oracle.values[4+oracle.p];++oracle.values[20+oracle.s];}
}
static void telemetry_post(Vtelemetry_probe&d){
    require(d.probe_outputs_equal,"whole production postedge outputs differ");
    for(unsigned i=0;i<52;++i)require(observed(d,i)==oracle.values[i],"independent postedge52word oracle");
    if(oracle.trace&&(oracle.phase=="prepared"||oracle.clocks%256==0||oracle.guards)){
        *oracle.trace<<"{\"clock\":"<<oracle.clocks<<",\"phase\":\""<<oracle.phase<<"\",\"guards\":"<<oracle.guards<<",\"running\":"<<oracle.running<<",\"emitter\":"<<oracle.e<<",\"packet\":"<<oracle.p<<",\"scratch\":"<<oracle.s<<",\"counts\":[";
        for(unsigned i=0;i<52;++i){if(i)*oracle.trace<<',';*oracle.trace<<observed(d,i);}*oracle.trace<<"]}\n";++oracle.logged;
    }
    ++oracle.clocks;require(oracle.clocks<100000000,"finite clock watchdog");
}
int main(int argc,char**argv){try{
    require(argc==4,"usage: seed trace vectors");const unsigned seed=unsigned(std::stoul(argv[1]));std::ofstream trace(argv[2]);require(bool(trace),"trace open");oracle.trace=&trace;
    Vtelemetry_probe d;auto&r=*d.rootp;
    d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=46;d.blocks=1;d.epoch=17;
    d.serial_clear=0;d.write_overlap=0;d.read_prefetch=0;d.tile_overlap=0;d.in_valid=0;d.in_data=0;d.in_last=0;d.out_ready=0;
    d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=0;
    auto tick=[&](){d.clk=0;d.eval();telemetry_pre(d);d.clk=1;d.eval();telemetry_post(d);d.clk=0;d.eval();};tick();d.reset=0;
    uint64_t prepared=0;std::array<std::array<bool,64>,52> covered{};std::array<bool,16> guard_coverage{};
    for(unsigned kind=0;kind<3;++kind)for(unsigned word=0;word<(kind==0?4U:kind==1?16U:32U);++word)for(unsigned carry=1;carry<=64;++carry)for(unsigned action=0;action<16;++action){
        // A real reset edge separates prepared owners and satisfies pending SVA release conditions.
        d.reset=1;d.start=0;d.abort_packet=0;d.in_valid=0;tick();d.reset=0;
        const unsigned packet=kind==1?word:0,scratch=kind==2?word:1,emitter=kind==0?word:3;
        BOTH(running,(action&8)!=0);BOTH(allocation,1U);BOTH(seal_sent,1U);BOTH(error,0U);BOTH(done,0U);
        PKTBOTH(state,packet);
        PKTBOTH(error,0U);PKTBOTH(done,0U);
        PKTBOTH(context_active,0U);PKTBOTH(raw_valid,0U);PKTBOTH(word_valid,0U);
        PKTBOTH(context_blocks,1U);PKTBOTH(size_bytes,46U);PKTBOTH(received,46U);
        SCRBOTH(state,scratch);SCRBOTH(error,0U);SCRBOTH(done,0U);SCRBOTH(sealed,1U);SCRBOTH(blocks,1U);
        SCRBOTH(outstanding,0U);SCRBOTH(write_slot_valid,0U);SCRBOTH(prefetch_offer,0U);SCRBOTH(raw_mode,0U);
        SCRBOTH(tile_overlap_mode,emitter!=3);SCRBOTH(bank_ready,emitter==1||emitter==2?1U:0U);SCRBOTH(emit_bank,0U);SCRBOTH(prep_bank,1U);SCRBOTH(tile_preparing,0U);SCRBOTH(tile_emit_index,0U);
        SCRBOTH(output_block,0U);SCRBOTH(output_index,0U);SCRBOTH(used_bytes,262144U);SCRBOTH(transfer_address,0U);
        d.out_ready=emitter==1;d.reset=(action&1)!=0;d.start=(action&2)!=0;d.abort_packet=(action&4)!=0;
        for(unsigned i=0;i<52;++i){
            const uint64_t base=carry==64?~uint64_t(0):(uint64_t(1)<<carry)-1;
            const uint64_t upper=carry>=63?0:((0x9e3779b97f4a7c15ULL*(i+1)^seed)>>(carry+1))<<(carry+1);
            const uint64_t value=base|upper;oracle.values[i]=value;
            if(i<4){BOTH(count_emitter_state[i],value);}else if(i<20){BOTH(count_packet_state[i-4],value);}else{BOTH(count_scratch_state[i-20],value);}
        }
        trace<<"{\"prepare\":true,\"kind\":"<<kind<<",\"word\":"<<word<<",\"carry\":"<<carry<<",\"action\":"<<action<<",\"counts\":[";
        for(unsigned i=0;i<52;++i){if(i)trace<<',';trace<<oracle.values[i];}trace<<"]}\n";
        d.clk=0;d.eval();
        if(action==8){require((kind==0?unsigned(d.dbg_emitter_state):kind==1?unsigned(d.packet_state):unsigned(d.dbg_scratch_state))==word,"prepared target selector not reached");covered[(kind==0?0:kind==1?4:20)+word][carry-1]=true;}
        tick();++prepared;guard_coverage[action]=true;
    }
    for(const auto&v:covered){for(bool b:v)require(b,"counter/carry coverage hole");}
    for(bool b:guard_coverage)require(b,"guard/running coverage hole");
    const auto prepared_edges=oracle.clocks,prepared_logs=oracle.logged;d.final();trace<<"{\"model_start\":\"historical-public-pipeline\"}\n";
    oracle=CounterOracle{};oracle.trace=&trace;oracle.phase="historical";char* args[]={argv[0],argv[3],argv[1]};require(historical_pipeline_main(3,args)==0,"retained historical pipeline failed");
    std::cout<<"{\"type\":\"telemetry_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"prepared_cases\":"<<prepared<<",\"prepared_edges\":"<<prepared_edges<<",\"prepared_trace_rows\":"<<prepared_logs<<",\"historical_edges\":"<<oracle.clocks<<",\"historical_trace_rows\":"<<oracle.logged<<",\"counter_words\":52,\"carry_positions\":64,\"guard_running_combinations\":16}\n";
    return 0;
}catch(const std::exception&e){std::cerr<<"TELEMETRY_FAIL "<<e.what()<<'\n';return 1;}}
