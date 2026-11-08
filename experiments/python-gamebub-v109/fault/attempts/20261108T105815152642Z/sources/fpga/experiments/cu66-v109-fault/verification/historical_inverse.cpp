#include "Vlocality_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static void need(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
static std::vector<uint8_t> unhex(const std::string &text){if(text=="-")return {};need(text.size()%2==0,"hex width");std::vector<uint8_t> out;for(size_t i=0;i<text.size();i+=2)out.push_back(uint8_t(std::stoul(text.substr(i,2),nullptr,16)));return out;}
static int i32(const std::vector<uint8_t> &bytes,unsigned n){uint32_t value=0;for(unsigned j=0;j<4;++j){value|=uint32_t(bytes[4*n+j])<<(8*j);}return int(int32_t(value));}
static int signed_bits(uint32_t word,unsigned width){word&=(uint32_t(1)<<width)-1;return word&(uint32_t(1)<<(width-1))?int(int64_t(word)-(int64_t(1)<<width)):int(word);}
template<class Wide>static int packed(const Wide &bits,unsigned n,unsigned width){unsigned at=n*width,idx=at/32,shift=at%32;uint64_t value=bits[idx];if(shift+width>32)value|=uint64_t(bits[idx+1])<<32;return signed_bits(uint32_t(value>>shift),width);}
struct Case{std::string id;unsigned error=0,plane=0,scale=0;std::vector<uint8_t> coef,dq,resid;};
static std::vector<Case> load(const std::string &path){std::ifstream file(path);need(bool(file),"boundary file missing");std::vector<Case> rows;std::string line;while(std::getline(file,line)){if(line.empty())continue;std::istringstream in(line);Case c;std::string a,b,d;in>>c.id>>c.error>>c.plane>>c.scale>>a>>b>>d;need(!in.fail(),"boundary row");c.coef=unhex(a);c.dq=unhex(b);c.resid=unhex(d);need(c.coef.size()==128,"coefficient width");rows.push_back(std::move(c));}return rows;}
static bool has_ac(const Case &c){for(unsigned n=1;n<64;++n){if(c.coef[2*n]!=0||c.coef[2*n+1]!=0)return true;}return false;}
struct Held{unsigned epoch,child,token,plane,block,tile,cell,scale,index,value;bool operator==(const Held &b)const{return epoch==b.epoch&&child==b.child&&token==b.token&&plane==b.plane&&block==b.block&&tile==b.tile&&cell==b.cell&&scale==b.scale&&index==b.index&&value==b.value;}};
class Bench{
public:
    Vlocality_probe d;std::mt19937 rng;unsigned seed;uint64_t cycle=0,inputs=0,outputs=0,dq_samples=0,assembly_samples=0;uint32_t epoch=0;
    const Case *active=nullptr;std::optional<Held> held;bool force_hold=false,check_values=true;
    explicit Bench(unsigned s):rng(s),seed(s){d.clk=0;d.reset=1;d.start=0;d.cancel=0;d.input_done=0;d.in_valid=0;d.in_index=0;d.in_value=0;d.in_epoch=0;d.in_child_epoch=0;d.in_plane=0;d.in_qscale=0;d.in_block=0;d.in_tile=0;d.in_qcell=0;d.out_ready=0;tick();d.reset=0;tick();}
    Held tuple()const{return {d.out_epoch,d.out_child_epoch,d.out_token,unsigned(d.out_plane),unsigned(d.out_block),unsigned(d.out_tile),unsigned(d.out_qcell),unsigned(d.out_qscale),unsigned(d.out_index),unsigned(d.out_value)};}
    void tick(){d.clk=0;d.out_ready=!force_hold&&(rng()%4!=0);d.eval();const bool kill=d.reset||d.start||d.cancel||d.error!=0;
        if(kill)held.reset();else if(held)need(d.out_valid&&tuple()==*held,"held residual tuple changed");
        held=d.out_valid&&!d.out_ready?std::optional<Held>(tuple()):std::nullopt;
        need(d.owned_banks<=2&&d.max_owned_banks<=2,"bank bound");
        if(d.in_valid&&d.in_ready)++inputs;
        if(d.dbg_launch&&check_values){need(active&&active->error==0,"invalid tile launched");for(unsigned n=0;n<64;++n){int expected=int(int16_t(unsigned(active->coef[2*n])|(unsigned(active->coef[2*n+1])<<8)));need(packed(d.dbg_coefficients,n,16)==expected,"assembled bank data");++assembly_samples;}}
        if(d.dbg_dequant&&check_values){need(active&&active->dq.size()==256,"DQ golden missing");for(unsigned n=0;n<64;++n){need(packed(d.dbg_dequantized,n,20)==i32(active->dq,n),"dequant mismatch "+active->id);++dq_samples;}}
        if(d.out_valid&&d.out_ready){need(active,"residual without case");if(check_values){need(d.out_epoch==epoch&&d.out_child_epoch==epoch+100&&d.out_plane==active->plane&&d.out_tile==0&&d.out_qcell==0&&d.out_qscale==active->scale,"residual metadata");need(d.out_index==outputs%64,"residual index order");need(signed_bits(d.out_value,24)==i32(active->resid,d.out_index),"residual mismatch "+active->id);}++outputs;}
        locality_pre(d);d.clk=1;d.eval();locality_post(d);++cycle;}
    void begin(const Case &c){need(!d.busy,"new frame before local drain");active=&c;inputs=outputs=dq_samples=assembly_samples=0;++epoch;d.start=1;d.in_valid=0;d.input_done=0;d.in_epoch=epoch;d.in_child_epoch=epoch+100;d.in_plane=c.plane;d.in_qscale=c.scale;d.in_tile=0;d.in_qcell=0;d.in_block=0;tick();d.start=0;held.reset();}
    void feed(unsigned count=64){for(unsigned index=0;index<count&&!d.error;++index){d.in_valid=1;d.in_index=index;d.in_value=uint16_t(unsigned(active->coef[2*index])|(unsigned(active->coef[2*index+1])<<8));for(unsigned w=0;;++w){need(w<10000,"input watchdog");d.clk=0;d.eval();bool accept=d.in_ready;tick();if(accept||d.error)break;}}d.in_valid=0;}
    void finish(){d.input_done=1;for(unsigned w=0;w<10000&&!d.done&&!d.error;++w){tick();}d.input_done=0;need(d.error==active->error,"adapter error mismatch "+active->id);if(!active->error){need(d.done&&outputs==64&&dq_samples==64&&assembly_samples==64,"inverse boundary completion");need(d.count_inputs==64&&d.count_outputs==64&&d.count_launches==1&&d.count_dequant==1,"boundary counters");}else need(outputs==0&&!d.done,"invalid boundary emitted residual");need(d.owned_banks==0&&!d.busy,"boundary owner drain");}
    void cancel(bool reset=false){d.in_valid=0;d.input_done=0;if(reset)d.reset=1;else d.cancel=1;tick();d.reset=0;d.cancel=0;for(unsigned n=0;n<4;++n){tick();}need(!d.busy&&!d.done&&!d.out_valid&&d.owned_banks==0,"cancel late owner");}
};
int historical_inverse_main(int argc,char **argv){try{need(argc==3,"usage: Vlocality_probe boundary.tsv seed");auto cases=load(argv[1]);unsigned seed=unsigned(std::stoul(argv[2]));Bench b(seed);unsigned rows=0;uint64_t samples=0;const Case *good=nullptr;
    for(const auto &c:cases){b.begin(c);b.feed();b.finish();samples+=b.outputs;++rows;if(!good&&c.error==0&&c.dq.size()==256&&has_ac(c))good=&c;std::cout<<"{\"type\":\"case\",\"id\":\""<<c.id<<"\",\"status\":\"PASS\",\"error\":"<<unsigned(b.d.error)<<",\"residual_samples\":"<<b.outputs<<",\"dq_samples\":"<<b.dq_samples<<",\"assembly_samples\":"<<b.assembly_samples<<",\"max_owned_banks\":"<<unsigned(b.d.max_owned_banks)<<"}\n";}
    need(good,"no valid boundary");std::vector<std::string> directed;auto pass=[&](const std::string &name){directed.push_back(name);std::cout<<"{\"type\":\"directed\",\"name\":\""<<name<<"\",\"status\":\"PASS\"}\n";};
    b.begin(*good);b.feed(7);b.d.in_valid=1;b.d.in_index=9;b.tick();b.d.in_valid=0;need(b.d.error==1,"bad coefficient index");b.cancel();pass("coefficient_order_rejected");
    b.begin(*good);b.feed(7);b.d.in_valid=1;b.d.in_index=7;b.d.in_tile=1;b.tick();b.d.in_valid=0;need(b.d.error==2,"metadata mutation");b.cancel();pass("tile_metadata_immutable");
    b.begin(*good);b.feed(7);b.d.input_done=1;b.tick();b.d.input_done=0;need(b.d.error==4,"partial tile completion");b.cancel();pass("partial_tile_completion_rejected");
    for(bool reset:{false,true}){b.begin(*good);b.feed(5);b.cancel(reset);pass(reset?"reset_partial_tile":"abort_partial_tile");}
    for(unsigned state:{1u,2u,3u,4u})for(bool reset:{false,true}){
        b.begin(*good);b.force_hold=true;b.feed();b.d.input_done=1;
        for(unsigned w=0;w<10000&&b.d.math_state!=state;++w){b.tick();}
        need(b.d.math_state==state,"math cancellation state absent");
        if(state==2||state==3){for(unsigned n=0;n<(state==2?2u:3u);++n){b.tick();need(b.d.math_state==state,"multicycle arithmetic ended before cancel");}}
        if(state==4){for(unsigned n=0;n<11;++n){b.tick();}}
        b.cancel(reset);b.force_hold=false;pass(std::string(reset?"reset_math_state_":"abort_math_state_")+std::to_string(state));
    }
    b.begin(*good);b.force_hold=true;b.feed();b.feed();need(b.d.owned_banks==2&&!b.d.in_ready,"two banks did not block third tile");
    b.d.in_valid=1;b.d.in_index=0;b.d.in_value=0;for(unsigned n=0;n<11;++n){b.tick();need(!b.d.in_ready&&b.d.owned_banks==2,"full bank ownership changed");}
    b.cancel();b.force_hold=false;pass("two_bank_backpressure_and_cancel");
    b.begin(*good);b.feed();b.finish();pass("clean_retry_after_cancel_and_error");
    std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"boundary_cases\":"<<rows<<",\"residual_samples\":"<<samples<<",\"directed_checks\":"<<directed.size()<<",\"owner_bound\":2,\"directed_check_names\":[";for(size_t n=0;n<directed.size();++n){if(n)std::cout<<',';std::cout<<'"'<<directed[n]<<'"';}std::cout<<"]}\n";return 0;
}catch(const std::exception &e){std::cerr<<"V91J_INVERSE_TEST_FAIL "<<e.what()<<'\n';return 1;}}
