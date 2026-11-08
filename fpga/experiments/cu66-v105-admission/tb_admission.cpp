#include "Vadmission_probe.h"
#include "verilated.h"
#include "Vadmission_probe___024root.h"
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
#include <utility>
#include <vector>

static void require(bool test,const std::string &message) {
    if(!test)throw std::runtime_error(message);
}
static std::string quoted(const std::string &s) {
    std::string out="\"";
    for(char c:s) {if(c=='"'||c=='\\')out+='\\';out+=c;}
    return out+'"';
}
struct Plane {uint32_t blocks=0,offset=0,length=0,type=0;};
struct Case {
    std::string id;unsigned expected_error=0;
    std::vector<uint8_t> packet;
    unsigned ref_valid=0,cache_valid=0;
    uint32_t prior_fid=0,fid=0,refid=0;
    uint64_t prior_generation=0,generation=0;
    unsigned key=0;
    uint32_t mode_bytes=0,qmap_bytes=0,hud_bytes=0,data_bytes=0,required_cells=0;
    std::array<Plane,3> plane{};
};
static std::vector<uint8_t> unhex(const std::string &s) {
    require(s.size()%2==0,"odd packet hex");std::vector<uint8_t> out;
    auto nibble=[](char c)->unsigned {
        if(c>='0'&&c<='9')return unsigned(c-'0');
        if(c>='a'&&c<='f')return unsigned(c-'a')+10;
        if(c>='A'&&c<='F')return unsigned(c-'A')+10;
        throw std::runtime_error("invalid packet hex");
    };
    for(size_t i=0;i<s.size();i+=2)out.push_back(uint8_t(16*nibble(s[i])+nibble(s[i+1])));
    return out;
}
static std::vector<Case> read_cases(const std::string &path) {
    std::ifstream in(path);require(bool(in),"cannot open vectors");std::string line;std::vector<Case> out;
    while(std::getline(in,line)) {
        if(line.empty())continue;
        Case c;std::string hex;std::istringstream row(line);
        row>>c.id>>c.expected_error>>hex>>c.ref_valid>>c.prior_fid>>c.prior_generation>>c.cache_valid
            >>c.fid>>c.refid>>c.generation>>c.key>>c.mode_bytes>>c.qmap_bytes>>c.hud_bytes>>c.data_bytes;
        for(auto &p:c.plane)row>>p.blocks>>p.offset>>p.length>>p.type;
        row>>c.required_cells;
        require(!row.fail(),"bad vector row: "+c.id);std::string extra;require(!(row>>extra),"extra vector column");
        c.packet=unhex(hex);out.push_back(std::move(c));
    }
    require(!out.empty(),"empty vectors");return out;
}
struct Receipt {
    uint32_t epoch=0,fid=0,refid=0;uint64_t generation=0;unsigned key=0;
    uint32_t mode_bytes=0,qmap_bytes=0,hud_bytes=0,data_bytes=0,required_cells=0;
    std::array<Plane,3> plane{};
    bool operator==(const Receipt &b)const {
        if(epoch!=b.epoch||fid!=b.fid||refid!=b.refid||generation!=b.generation||key!=b.key||
           mode_bytes!=b.mode_bytes||qmap_bytes!=b.qmap_bytes||hud_bytes!=b.hud_bytes||
           data_bytes!=b.data_bytes||required_cells!=b.required_cells)return false;
        for(unsigned i=0;i<3;++i)if(plane[i].blocks!=b.plane[i].blocks||plane[i].offset!=b.plane[i].offset||
            plane[i].length!=b.plane[i].length||plane[i].type!=b.plane[i].type)return false;
        return true;
    }
};
class Bench {
    struct Pending {uint32_t address,epoch;uint8_t data;};
    std::unique_ptr<Vadmission_probe> dut_=std::make_unique<Vadmission_probe>();
    std::mt19937 rng_;
    std::optional<Pending> pending_;
    std::optional<Receipt> held_;
    std::optional<std::pair<uint8_t,bool>> held_input_;
    std::vector<uint8_t> written_;
    bool previous_receipt_=false;
    bool exhaust_lookup_=false;
    uint32_t current_epoch_=0,current_size_=0;
public:
    uint64_t ticks=0,reads=0,responses=0,receipts=0,held_edges=0;
    unsigned seed;
    std::ofstream trace;
    uint64_t residual_marks=0, coordinate_rows=0, cache_noise_edges=0, lookup_response_edges=0;
    explicit Bench(unsigned s):rng_(s),seed(s),trace("trace.jsonl") {
        dut_->clk=0;dut_->reset=1;dut_->start=0;dut_->abort_packet=0;
        dut_->in_valid=0;dut_->in_last=0;dut_->receipt_ready=0;
        tick();dut_->reset=0;tick();
    }
    Vadmission_probe &d(){return *dut_;}
    unsigned random(unsigned n){return rng_()%n;}
    Receipt receipt()const {
        Receipt r;r.epoch=dut_->receipt_epoch;r.fid=dut_->fid;r.refid=dut_->refid;
        r.generation=dut_->generation;r.key=dut_->key_frame;r.mode_bytes=dut_->mode_bytes;
        r.qmap_bytes=dut_->qmap_bytes;r.hud_bytes=dut_->hud_bytes;r.data_bytes=dut_->data_bytes;
        r.required_cells=dut_->required_cells;
        for(unsigned p=0;p<3;++p)r.plane[p]={dut_->plane_blocks[p],dut_->plane_offset[p],dut_->plane_length[p],dut_->plane_entropy[p]};
        return r;
    }
    void tick() {
        auto &x=*dut_;
        if(!x.verify_coord_valid && ticks>0) {
            // Deliberately perturb only dead coordinate storage; owner-valid remains untouched.
            auto &r=*x.rootp;
            r.admission_probe__DOT__candidate__DOT__coord_cell=(ticks*19)&2047;
            r.admission_probe__DOT__candidate__DOT__coord_pair_base=(ticks*23)&2047;
            r.admission_probe__DOT__candidate__DOT__coord_y_column=(ticks*7)&127;
            r.admission_probe__DOT__candidate__DOT__coord_y_odd=ticks&1;
            ++cache_noise_edges;
        }
        x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");
        if(x.verify_coord_valid || x.debug_state==13 || x.reset||x.start||x.abort_packet)trace<<"{\"clock\":"<<ticks<<",\"state\":"<<unsigned(x.debug_state)
             <<",\"kill\":"<<unsigned(x.reset||x.start||x.abort_packet)<<",\"valid\":"<<unsigned(x.verify_coord_valid)
             <<",\"plane\":"<<unsigned(x.verify_plane)<<",\"tile\":"<<x.verify_tile
             <<",\"cell\":"<<x.verify_cell<<",\"column\":"<<unsigned(x.verify_column)
             <<",\"odd\":"<<unsigned(x.verify_odd)<<",\"base\":"<<x.verify_pair_base
             <<",\"residual\":"<<unsigned(x.verify_residual)<<",\"active_index\":"<<x.verify_active_index
             <<",\"active\":"<<unsigned(x.verify_active_value)<<"}\n";
        lookup_response_edges+=x.lookup_rsp_valid;
        residual_marks+=x.verify_residual&&!x.reset&&!x.start&&!x.abort_packet;
        coordinate_rows+=x.verify_coord_valid&&!x.reset&&!x.start&&!x.abort_packet;
        const bool cancelled=x.reset||x.start||x.abort_packet;
        if(cancelled) {
            require(!x.stage_read_req&&!x.stage_read_rsp&&!x.in_ready&&!x.receipt_valid,"cancel leaked valid traffic");
            pending_.reset();held_.reset();held_input_.reset();previous_receipt_=false;
        } else {
            if(held_input_)require(x.in_valid&&x.in_data==held_input_->first&&bool(x.in_last)==held_input_->second,
                "sender changed a backpressured input tuple");
            if(x.in_valid&&!x.in_ready)held_input_=std::make_pair(uint8_t(x.in_data),bool(x.in_last));
            else held_input_.reset();
            if(pending_) {
                require(x.stage_pending,"pending scoreboard/read-state mismatch");
                require(x.stage_read_rsp,"missing registered response");
                require(x.stage_rsp_addr==pending_->address&&x.stage_rsp_epoch==pending_->epoch&&
                        x.stage_read_data==pending_->data,"registered response binding/data mismatch");
                pending_.reset();++responses;
            } else require(!x.stage_read_rsp&&!x.stage_pending,"unsolicited or late response");
            if(x.stage_read_req) {
                require(!pending_,"multiple pending local reads");
                require(x.stage_read_addr<current_size_&&x.stage_read_addr<49152&&x.stage_read_addr<written_.size(),"unwritten/out-of-range stage read");
                require(x.stage_req_epoch==current_epoch_,"request stale epoch");
                pending_=Pending{x.stage_read_addr,x.stage_req_epoch,written_[x.stage_read_addr]};++reads;
            }
            if(x.stage_write) {
                require(x.in_valid&&x.in_ready,"stage write without input handshake");
                require(written_.size()<current_size_&&written_.size()<49152,"write exceeds packet backing");
                written_.push_back(x.in_data);
            }
            require(bool(x.stage_write)==bool(x.in_valid&&x.in_ready),"input/write conservation");
            if(held_)require(x.receipt_valid&&receipt()==*held_,"held receipt changed or vanished");
            if(x.receipt_valid) {
                require(x.error==0&&written_.size()==current_size_,"receipt before complete accepted packet");
                require(!pending_,"receipt with local read pending");
                if(!previous_receipt_)++receipts;
                if(!x.receipt_ready){held_=receipt();++held_edges;}else held_.reset();
            } else held_.reset();
            previous_receipt_=x.receipt_valid;
        }
        x.cache_write=(!cancelled && ticks%97==0);x.cache_index=ticks%1350;x.cache_data=ticks%4;
        x.lookup_req=(!cancelled && (exhaust_lookup_ || ticks%19==0));x.lookup_tile=ticks%8100;x.lookup_cell=ticks%1350;
        x.replay_req=(!cancelled && ticks%23==0);x.replay_addr=current_size_?ticks%current_size_:0;
        x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");x.clk=1;x.eval();require(!x.mismatch,"full module public output mismatch high");++ticks;
    }
    void begin(const Case &c,uint32_t e,std::optional<uint32_t> declared={}) {
        trace<<"{\"begin\":"<<quoted(c.id)<<",\"epoch\":"<<e<<"}\n";
        auto &x=*dut_;x.in_valid=0;x.in_last=0;x.receipt_ready=0;
        current_size_=declared.value_or(uint32_t(c.packet.size()));current_epoch_=e;
        x.packet_bytes=current_size_;x.epoch=e;x.accepted_ref_valid=c.ref_valid;
        x.accepted_ref_fid=c.prior_fid;x.accepted_ref_generation=c.prior_generation;x.accepted_qcache_valid=c.cache_valid;
        x.start=1;written_.clear();reads=0;responses=0;receipts=0;held_edges=0;tick();x.start=0;
        // Deliberately corrupt the external snapshot inputs immediately after
        // start. Parsing must use its latched snapshot, including on keys.
        x.accepted_ref_valid=!c.ref_valid;x.accepted_qcache_valid=!c.cache_valid;
        x.accepted_ref_fid=~c.prior_fid;x.accepted_ref_generation=~c.prior_generation;
    }
    void feed(const Case &c,bool bad_early=false,bool bad_final=false) {
        auto &x=*dut_;size_t at=0;bool offered=false;
        for(unsigned watchdog=0;watchdog<1000000;++watchdog) {
            if(x.error||x.receipt_valid){x.in_valid=0;x.in_last=0;return;}
            if(!offered&&at<c.packet.size()&&random(8)!=0)offered=true;
            x.in_valid=offered;
            x.in_data=at<c.packet.size()?c.packet[at]:0;
            x.in_last=(at+1==c.packet.size()&&!bad_final)||(bad_early&&at==0);
            x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");const bool accept=x.in_valid&&x.in_ready;
            tick();if(accept){++at;offered=false;}
            if(x.error||x.receipt_valid){x.in_valid=0;x.in_last=0;return;}
        }
        throw std::runtime_error("feed/parser watchdog");
    }
    void until(const Case &c,unsigned target) {
        auto &x=*dut_;size_t at=0;
        for(unsigned watchdog=0;watchdog<1000000;++watchdog) {
            x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");if(x.debug_state==target){x.in_valid=0;return;}
            x.in_valid=at<c.packet.size();x.in_data=at<c.packet.size()?c.packet[at]:0;x.in_last=at+1==c.packet.size();
            x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");const bool accept=x.in_valid&&x.in_ready;tick();if(accept)++at;
            require(x.error==0,"unexpected failure before directed cancellation state");
        }
        throw std::runtime_error("directed state watchdog");
    }
    void idle_check(unsigned n) {
        auto &x=*dut_;x.in_valid=0;x.in_last=0;x.receipt_ready=0;
        for(unsigned i=0;i<n;++i){tick();require(!x.receipt_valid&&!x.stage_read_req&&!x.stage_read_rsp,"late traffic after cancellation/finish");}
    }
    void cancel(unsigned kind) {
        if(kind==0)dut_->abort_packet=1;else dut_->reset=1;
        tick();dut_->abort_packet=0;dut_->reset=0;idle_check(7);
    }
    Receipt finish(const Case &c,bool output) {
        auto &x=*dut_;
        require(x.error==c.expected_error,"error mismatch for "+c.id+": got "+std::to_string(x.error)+", expected "+std::to_string(c.expected_error));
        Receipt r;
        if(c.expected_error==0) {
            require(x.receipt_valid,"positive has no held receipt");r=receipt();
            require(r.epoch==current_epoch_&&r.fid==c.fid&&r.refid==c.refid&&r.generation==c.generation&&r.key==c.key&&
                r.mode_bytes==c.mode_bytes&&r.qmap_bytes==c.qmap_bytes&&r.hud_bytes==c.hud_bytes&&r.data_bytes==c.data_bytes&&
                r.required_cells==c.required_cells,"receipt metadata mismatch");
            for(unsigned p=0;p<3;++p)require(r.plane[p].blocks==c.plane[p].blocks&&r.plane[p].offset==c.plane[p].offset&&
                r.plane[p].length==c.plane[p].length&&r.plane[p].type==c.plane[p].type,"descriptor mismatch");
            for(unsigned i=0,n=7+random(17);i<n;++i)tick();
            require(receipts==1,"duplicate receipt");x.receipt_ready=1;tick();x.receipt_ready=0;idle_check(3);
            exhaust_lookup_=true;for(unsigned k=0;k<8100;++k)tick();exhaust_lookup_=false;
            require(reads==responses,"successful local read conservation");
        } else {idle_check(3);require(receipts==0,"rejected packet emitted a receipt");}
        require(x.count_inputs==written_.size(),"input counter mismatch");
        require(x.count_stage_reads==reads&&x.count_stage_responses==responses,"stage counter mismatch");
        if(output) {
            std::cout<<"{\"type\":\"case\",\"id\":"<<quoted(c.id)<<",\"status\":\"PASS\",\"error\":"<<unsigned(x.error)
                <<",\"seed\":"<<seed<<",\"cycles\":"<<x.count_cycles<<",\"input_bytes\":"<<x.count_inputs
                <<",\"stage_reads\":"<<reads<<",\"stage_responses\":"<<responses<<",\"receipt_count\":"<<receipts
                <<",\"receipt_hold_cycles\":"<<held_edges<<",\"receipt\":";
            if(c.expected_error)std::cout<<"null";
            else {
                std::cout<<"{\"epoch\":"<<r.epoch<<",\"fid\":"<<r.fid<<",\"refid\":"<<r.refid<<",\"generation\":"<<r.generation
                    <<",\"key\":"<<r.key<<",\"mode_bytes\":"<<r.mode_bytes<<",\"qmap_bytes\":"<<r.qmap_bytes
                    <<",\"hud_bytes\":"<<r.hud_bytes<<",\"data_bytes\":"<<r.data_bytes<<",\"required_cells\":"<<r.required_cells<<",\"plane\":[";
                for(unsigned p=0;p<3;++p) {
                    if(p)std::cout<<',';
                    std::cout<<"{\"blocks\":"<<r.plane[p].blocks<<",\"offset\":"<<r.plane[p].offset
                        <<",\"length\":"<<r.plane[p].length<<",\"entropy_type\":"<<r.plane[p].type<<'}';
                }
                std::cout<<"]}";
            }
            std::cout<<"}\n";
        }
        return r;
    }
};
int main(int argc,char **argv) {
    try {
        require(argc==3,"usage: Vadmission_probe vectors.txt seed");
        const auto cases=read_cases(argv[1]);const unsigned seed=unsigned(std::stoul(argv[2]));Bench b(seed);
        unsigned positives=0,negatives=0;uint64_t descriptor_comparisons=0;uint32_t epoch=100;
        const Case *good=nullptr;
        for(const auto &c:cases) {
            b.begin(c,++epoch);b.feed(c);b.finish(c,true);
            if(c.expected_error){++negatives;}else {++positives;descriptor_comparisons+=3;if(!good)good=&c;}
        }
        require(good!=nullptr,"no positive fixture for directed checks");
        std::vector<std::string> directed;
        auto record=[&](const std::string &name){directed.push_back(name);std::cout<<"{\"type\":\"directed\",\"name\":"<<quoted(name)<<",\"status\":\"PASS\"}\n";};
        for(unsigned state:{6u,12u,13u,28u,29u,25u})for(unsigned kind=0;kind<2;++kind) {
            b.begin(*good,++epoch);b.until(*good,state);
            if(state==25)for(unsigned k=0;k<3;++k)b.tick();
            b.cancel(kind);
            record(std::string(kind?"reset_":"abort_")+"state_"+std::to_string(state));
            b.begin(*good,++epoch);b.feed(*good);b.finish(*good,false);
        }
        for(unsigned state:{6u,12u,29u,25u}) {
            b.begin(*good,++epoch);b.until(*good,state);
            if(state==25)for(unsigned k=0;k<3;++k)b.tick();
            b.begin(*good,++epoch);b.feed(*good);b.finish(*good,false);
            record("replacement_start_state_"+std::to_string(state));
        }
        {
            auto bad=*good;bad.expected_error=2;b.begin(bad,++epoch);b.feed(bad,true,false);b.finish(bad,false);record("early_input_last");
            b.begin(bad,++epoch);b.feed(bad,false,true);b.finish(bad,false);record("missing_input_last");
        }
        {
            auto bad=*good;bad.expected_error=1;b.begin(bad,++epoch,49153);b.finish(bad,false);record("oversize_start_before_input");
            b.begin(bad,++epoch,131);b.finish(bad,false);record("undersize_start_before_input");
        }
        record("reference_snapshot_latched_every_case");
        record("receipt_ready_backpressure_every_positive");
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases.size()
            <<",\"positive_cases\":"<<positives<<",\"negative_cases\":"<<negatives<<",\"directed_checks\":"<<directed.size()
            <<",\"lookup_response_edges\":"<<b.lookup_response_edges<<",\"cache_noise_edges\":"<<b.cache_noise_edges<<",\"clock_edges\":"<<b.ticks<<",\"coordinate_rows\":"<<b.coordinate_rows<<",\"residual_marks\":"<<b.residual_marks<<",\"descriptor_comparisons\":"<<descriptor_comparisons<<",\"directed_check_names\":[";
        for(size_t i=0;i<directed.size();++i){if(i)std::cout<<',';std::cout<<quoted(directed[i]);}
        std::cout<<"]}\n";return 0;
    } catch(const std::exception &e) {std::cerr<<"ADMISSION_TEST_FAIL "<<e.what()<<'\n';return 1;}
}
