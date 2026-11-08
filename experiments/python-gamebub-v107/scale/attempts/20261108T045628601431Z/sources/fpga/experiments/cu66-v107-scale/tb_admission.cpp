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
    std::array<uint8_t,1350> scale_expected_{};
    std::array<bool,1350> scale_known_{};
    bool previous_receipt_=false;
    bool exhaust_lookup_=false;
    uint32_t current_epoch_=0,current_size_=0;
public:
    uint64_t ticks=0,reads=0,responses=0,receipts=0,held_edges=0;
    unsigned seed;
    std::ofstream trace;
    uint64_t residual_marks=0, coordinate_rows=0, cache_noise_edges=0, lookup_response_edges=0;
    uint64_t q_run_edges=0,q_fill_edges=0,q_fill_writes=0,scale_lookup_checks=0;
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
        x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");
        if(x.verify_coord_valid || x.debug_state==13 || x.reset||x.start||x.abort_packet)trace<<"{\"clock\":"<<ticks<<",\"state\":"<<unsigned(x.debug_state)
             <<",\"kill\":"<<unsigned(x.reset||x.start||x.abort_packet)<<",\"valid\":"<<unsigned(x.verify_coord_valid)
             <<",\"plane\":"<<unsigned(x.verify_plane)<<",\"tile\":"<<x.verify_tile
             <<",\"cell\":"<<x.verify_cell<<",\"column\":"<<unsigned(x.verify_column)
             <<",\"odd\":"<<unsigned(x.verify_odd)<<",\"base\":"<<x.verify_pair_base
             <<",\"residual\":"<<unsigned(x.verify_residual)<<",\"active_index\":"<<x.verify_active_index
             <<",\"active\":"<<unsigned(x.verify_active_value)<<"}\n";
        if(x.debug_state==17||x.debug_state==32)trace<<"{\"quant\":true,\"clock\":"<<ticks
             <<",\"state\":"<<unsigned(x.debug_state)<<",\"kill\":"<<unsigned(x.reset||x.start||x.abort_packet)
             <<",\"index\":"<<x.verify_q_index<<",\"runs\":"<<x.verify_q_runs<<",\"remaining\":"<<unsigned(x.verify_q_remaining)
             <<",\"value\":"<<unsigned(x.verify_q_value)<<",\"selected\":"<<unsigned(x.verify_q_selected)
             <<",\"cached\":"<<unsigned(x.verify_q_cached)<<"}\n";
        q_run_edges+=x.debug_state==17;q_fill_edges+=x.debug_state==32;
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
        x.clk=0;x.eval();require(!x.mismatch,"full module public output mismatch low");
        const bool check_scale=x.lookup_req&&x.debug_state==26&&!cancelled&&scale_known_[x.lookup_cell];
        const unsigned expected_scale=scale_expected_[x.lookup_cell];
        if(x.cache_write&&!cancelled){scale_expected_[x.cache_index]=x.cache_data;scale_known_[x.cache_index]=true;}
        if(x.debug_state==32&&!cancelled){
            require(x.verify_q_runs<1350,"reachable quant fill address bound");
            scale_expected_[x.verify_q_runs]=x.verify_q_value;scale_known_[x.verify_q_runs]=true;++q_fill_writes;
        }
        x.clk=1;x.eval();require(!x.mismatch,"full module public output mismatch high");
        if(check_scale){require(x.lookup_rsp_valid&&x.lookup_scale==expected_scale,"independent scale table read-first/hold/priority oracle");++scale_lookup_checks;}
        ++ticks;
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
#define QOLD(n) r.admission_probe__DOT__original__DOT__##n
#define QNEW(n) r.admission_probe__DOT__candidate__DOT__##n
#define QBOTH(n,v) do {const auto z=(v);QOLD(n)=z;QNEW(n)=z;}while(0)
static uint64_t prepared_quant() {
 Vadmission_probe d;auto&r=*d.rootp;uint64_t edges=0;
 d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.in_valid=0;d.in_last=0;
 d.cache_write=0;d.lookup_req=0;d.replay_req=0;d.receipt_ready=0;
 auto tick=[&](){d.clk=0;d.eval();require(!d.mismatch,"prepared full module comparison low");d.clk=1;d.eval();require(!d.mismatch,"prepared full module comparison high");d.clk=0;d.eval();++edges;};
 tick();d.reset=0;
 for(unsigned i=0;i<354;++i){QOLD(qbuffer)[i]=0;QNEW(qbuffer)[i]=0;}
 for(uint32_t index:{0U,12U,349U,353U,524U,0x8000000cU,0xfffffe0cU,0xfffffffcU})
  for(uint32_t runs:{0U,1U,1285U,1286U,1287U,1349U,1350U,0x7fffffffU,0xffffffbfU,0xffffffffU})
   for(unsigned byte=0;byte<256;++byte)for(unsigned terminal=0;terminal<2;++terminal) {
    const unsigned at=index&511U;if(at>=354&&!terminal)continue;
    if(at<354){QOLD(qbuffer)[at]=byte;QNEW(qbuffer)[at]=byte;}
    QBOTH(coord_valid,0U);QBOTH(state,17U);QBOTH(q_index,index);QBOTH(q_runs,runs);
    QBOTH(q_remaining,7U);QBOTH(q_value,1U);QBOTH(qmap_bytes,index+(terminal?4U:5U));
    // Prepared Q_RUN explicitly binds the private cache to the selected byte.
    // It does not claim that arbitrary32 parser coordinates are reachable.
    QOLD(q_run_byte)=terminal?(byte^127U):byte;QNEW(q_run_byte)=terminal?(byte^255U):byte;
    d.clk=0;d.eval();const uint32_t next=runs+(byte&63U)+1U;
    const bool bad=(byte>>6)>2U||next>1350U;
    tick();
    require(d.debug_state==(terminal?(runs==1350U?18U:27U):(bad?27U:32U)),"independent prepared run state/priority");
    if(!terminal&&!bad)require(d.verify_q_remaining==(byte&63U)+1U&&d.verify_q_value==(byte>>6)&&d.verify_q_index==index+1U,"independent prepared byte decode");
    require(d.error==((terminal?runs!=1350U:bad)?10U:0U),"independent prepared error priority");
    // Reset error for the next isolated preparation; no output is reclassified.
    d.reset=1;tick();d.reset=0;
   }
 // Every in-range byte address and all byte encodings exercise actual Q_FILL
 // capture followed by actual Q_RUN use, including minimum one-cell runs.
 for(unsigned at=0;at<354;++at)for(unsigned byte=0;byte<256;++byte) {
  QOLD(qbuffer)[at]=byte;QNEW(qbuffer)[at]=byte;
  QBOTH(coord_valid,0U);QBOTH(state,32U);QBOTH(q_index,at);QBOTH(q_runs,0U);
  QBOTH(q_remaining,1U);QBOTH(q_value,2U);QBOTH(qmap_bytes,at+5U);QNEW(q_run_byte)=byte^255U;
  tick();require(d.debug_state==17U&&d.verify_q_cached==byte,"actual Q_FILL prefetch binding");
  tick();require(d.debug_state==((byte>>6)>2U?27U:32U),"captured run independently decoded");
  d.reset=1;tick();d.reset=0;
 }
 d.final();return edges;
}

static uint64_t prepared_header(unsigned seed) {
 Vadmission_probe d;auto&r=*d.rootp;uint64_t edges=0;std::mt19937 random(seed);
 d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.in_valid=0;d.in_last=0;
 d.cache_write=0;d.lookup_req=0;d.replay_req=0;d.receipt_ready=0;d.packet_bytes=132;
 auto tick=[&](){d.clk=0;d.eval();require(!d.mismatch,"prepared header full module low");d.clk=1;d.eval();require(!d.mismatch,"prepared header full module high");d.clk=0;d.eval();++edges;};
 tick();d.reset=0;
 using Header=std::array<uint8_t,128>;
 auto put=[](Header&h,unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)h[at+j]=uint8_t(value>>(24-8*j));};
 auto word=[](const Header&h,unsigned at){return uint32_t(h[at])<<24|uint32_t(h[at+1])<<16|uint32_t(h[at+2])<<8|uint32_t(h[at+3]);};
 auto make=[&](uint32_t mode,uint32_t qm,uint32_t hud,uint32_t data,unsigned faults,bool key){
  Header h{};put(h,0,0x43533838);h[4]=1;h[5]=key;h[6]=16;h[7]=key?0:3;
  put(h,8,5);put(h,12,key?0xffffffffU:4U);put(h,20,5);
  h[24]=2;h[25]=0xd0;h[26]=1;h[27]=0xe0;h[29]=32;put(h,32,65536);
  if(faults&16)mode=1;
  put(h,36,mode);put(h,40,qm);put(h,44,hud);put(h,48,data);
  if(faults&1){h[0]^=255;}if(faults&2){h[127]=1;}if(faults&4){put(h,8,0xffffffffU);}if(faults&8){put(h,12,key?0U:3U);}
  return h;
 };
 auto expected=[&](const Header&h,uint32_t size,bool snapshot,uint32_t priorfid,uint64_t priorgen){
  const auto half=[&](unsigned at){return unsigned(h[at])*256+h[at+1];};bool padding=true;for(unsigned at=116;at<128;++at)padding&=h[at]==0;
  const uint64_t total=132ULL+word(h,36)+word(h,40)+word(h,44)+word(h,48),generation=uint64_t(word(h,16))<<32|word(h,20);
  if(word(h,0)!=0x43533838U||h[4]!=1||h[6]!=16||half(28)!=32||word(h,32)!=65536||(h[5]==1?h[7]!=0:h[7]!=3))return 4U;
  if(h[5]>1||half(24)!=720||half(26)!=480||half(30)!=0||!padding||word(h,36)>976||word(h,40)<16||word(h,40)>354||word(h,44)<110||word(h,44)>49152||total!=size)return 5U;
  if(word(h,8)==0xffffffffU||generation==0||(snapshot&&(word(h,8)<=priorfid||generation<=priorgen)))return 6U;
  if(h[5]==1?word(h,12)!=0xffffffffU:(!snapshot||word(h,12)!=priorfid))return 7U;
  if(h[5]==1&&word(h,36)!=0){return 8U;}return 0U;
 };
 auto setup=[&](const Header&h,uint32_t size,bool snapshot,uint32_t priorfid,uint64_t priorgen){
  for(unsigned j=0;j<128;++j){QOLD(header)[j]=h[j];QNEW(header)[j]=h[j];}
  QBOTH(coord_valid,0U);QBOTH(state,5U);QBOTH(header_index,127U);QBOTH(size_bytes,size);QBOTH(snapshot_valid,snapshot);QBOTH(snapshot_fid,priorfid);QBOTH(snapshot_generation,priorgen);
  // Explicit prepared-state cache invariant; not an arbitrary-state proof.
  const uint64_t m=128ULL+word(h,36),rs=m+word(h,40),ht=4ULL+word(h,44),re=rs+word(h,48);
  QBOTH(header_mode_start,m);QBOTH(header_residual_start,rs);QBOTH(header_hud_tail,ht);QBOTH(header_residual_end,re);QBOTH(header_packet_total,re+ht);
 };
 auto check=[&](const Header&h,uint32_t size,bool snapshot,uint32_t priorfid,uint64_t priorgen){
  const auto error=expected(h,size,snapshot,priorfid,priorgen);tick();
  require(d.error==error&&d.debug_state==(error?27U:h[5]==1?6U:7U),"independent header error/success priority");
  if(!error){require(QNEW(q_start)==uint32_t(128ULL+word(h,36))&&QNEW(residual_start)==uint32_t(128ULL+word(h,36)+word(h,40))&&QNEW(residual_end)==uint32_t(128ULL+word(h,36)+word(h,40)+word(h,48)),"independent header modular addresses");
   require(d.mode_bytes==word(h,36)&&d.qmap_bytes==word(h,40)&&d.hud_bytes==word(h,44)&&d.data_bytes==word(h,48),"independent full32 header output fields");}
  d.reset=1;tick();d.reset=0;
 };
 const std::array<uint32_t,22> boundaries={0U,1U,15U,16U,31U,32U,109U,110U,127U,128U,354U,355U,976U,977U,49152U,49153U,0x7fffffffU,0x80000000U,0xffffff7fU,0xffffff80U,0xfffffffcU,0xffffffffU};
 for(auto mode:boundaries)for(auto qm:boundaries)for(auto hud:boundaries)for(auto data:boundaries){
  Header h=make(mode,qm,hud,data,0,false);const uint32_t size=uint32_t(132ULL+mode+qm+hud+data);
  setup(h,size,true,4,4);check(h,size,true,4,4);
 }
 for(unsigned faults=0;faults<32;++faults)for(bool key:{false,true})for(bool snapshot:{false,true})
  for(uint32_t priorfid:{0U,4U,5U,0xffffffffU})for(uint64_t priorgen:{0ULL,4ULL,5ULL,0xffffffffffffffffULL}){
   Header h=make(0,16,110,0,faults,key);const uint32_t size=uint32_t(132ULL+word(h,36)+word(h,40)+word(h,44)+word(h,48));
   setup(h,size,snapshot,priorfid,priorgen);check(h,size,snapshot,priorfid,priorgen);
  }
 // Actual HEADER_BYTE nonblocking captures over stale backing bytes. State
 // preparation drives byte-load edges; full public-interface corpus below
 // independently proves normal fetch/load reachability and cancellation.
 for(unsigned n=0;n<2048;++n){
  const bool key=n&1;Header h=make(n%2?0:unsigned(random()),n%3?16:unsigned(random()),n%5?110:unsigned(random()),n%7?0:unsigned(random()),n%32,key);
  const uint32_t size=uint32_t(132ULL+word(h,36)+word(h,40)+word(h,44)+word(h,48));
  QBOTH(size_bytes,size);QBOTH(snapshot_valid,true);QBOTH(snapshot_fid,4U);QBOTH(snapshot_generation,4ULL);QBOTH(coord_valid,0U);
  for(unsigned j=0;j<128;++j){const unsigned stale=random()&255U;QOLD(header)[j]=stale;QNEW(header)[j]=stale;}
  QBOTH(header_mode_start,1);QBOTH(header_residual_start,2);QBOTH(header_hud_tail,3);QBOTH(header_residual_end,4);QBOTH(header_packet_total,5);
  for(unsigned index=0;index<128;++index){QBOTH(state,4U);QBOTH(header_index,index);QBOTH(byte_value,h[index]);tick();}
  require(d.debug_state==5,"header final byte transition");check(h,size,true,4,4);
 }
 // All reset/start/abort combinations at a prepared but invariant-consistent
 // HEADER_CHECK retain original cancellation priority and never consume data.
 for(unsigned flags=1;flags<8;++flags){Header h=make(0,16,110,0,0,true);setup(h,258,false,0,0);d.reset=flags&1;d.start=(flags&2)!=0;d.abort_packet=(flags&4)!=0;tick();
  require(d.debug_state==((flags==2)?31U:0U),"header cancellation/start priority");d.reset=1;d.start=0;d.abort_packet=0;tick();d.reset=0;}
 for(unsigned index:{39U,43U,47U,51U,55U})for(unsigned flags=1;flags<8;++flags){
  Header h=make(0,16,110,0,0,true);setup(h,258,false,0,0);QBOTH(state,4U);QBOTH(header_index,index);QBOTH(byte_value,255U);
  QBOTH(header_mode_start,1);QBOTH(header_residual_start,2);QBOTH(header_hud_tail,3);QBOTH(header_residual_end,4);QBOTH(header_packet_total,5);
  d.reset=flags&1;d.start=(flags&2)!=0;d.abort_packet=(flags&4)!=0;tick();
  require(QBOTH(header_mode_start,=1&&QBOTH(header_residual_start,=2&&QBOTH(header_hud_tail,=3&&QBOTH(header_residual_end,=4&&QBOTH(header_packet_total,=5,"header cache capture occurred on cancelled byte edge"))))));
  d.reset=1;d.start=0;d.abort_packet=0;tick();d.reset=0;
 }
 d.final();return edges;
}

static uint64_t prepared_scale_ports() {
 Vadmission_probe d;auto&r=*d.rootp;uint64_t edges=0;std::array<unsigned,1350> words{};unsigned held=0;bool known=false;
 std::ofstream trace("scale-ports.csv");require(bool(trace),"scale-port trace open");
 d.clk=0;d.reset=0;d.start=0;d.abort_packet=0;d.in_valid=0;d.in_last=0;d.replay_req=0;d.lookup_req=0;d.receipt_ready=0;d.cache_write=0;d.packet_bytes=258;
 auto edge=[&](unsigned state,unsigned a,unsigned av,bool aw,unsigned b,unsigned bv,bool bw,bool br,unsigned kills){
  d.reset=kills&1;d.start=(kills&2)!=0;d.abort_packet=(kills&4)!=0;
  d.cache_write=aw;d.cache_index=a;d.cache_data=av;d.lookup_req=br;d.lookup_cell=b;d.lookup_tile=0;
  QBOTH(coord_valid,0U);QBOTH(state,state);QBOTH(q_runs,uint32_t(b)|(bw?0x80000000U:0U));QBOTH(q_value,bv);QBOTH(q_remaining,2U);
  d.clk=0;d.eval();require(!d.mismatch,"prepared scale public comparison low");
  const bool read=br&&state==26U&&!kills;const unsigned expected=read?words[b]:held;
  d.clk=1;d.eval();require(!d.mismatch,"prepared scale public comparison high");
  if(read||known)require(d.lookup_scale==expected,"independent prepared scale OLD/HOLD oracle");
  if(read){held=expected;known=true;}
  trace<<edges<<','<<state<<','<<aw<<','<<a<<','<<av<<','<<bw<<','<<b<<','<<bv<<','<<br<<','<<kills<<','<<unsigned(d.lookup_scale)<<'\n';
  if(!kills&&aw)words[a]=av;
  if(!kills&&bw)words[b]=bv;
  d.clk=0;d.eval();++edges;
 };
 // Every valid word is initialized by a real external write, not backdoor RAM.
 for(unsigned i=0;i<1350;++i)edge(0,i,i%4,true,0,0,false,false,0);
 edge(26,0,0,false,0,0,false,true,0);
 for(unsigned value=0;value<4;++value)for(unsigned i=0;i<1350;++i){
  edge(26,i,value,true,i,0,false,true,0);edge(26,0,0,false,i,0,false,true,0);
 }
 for(unsigned value=0;value<4;++value)for(unsigned i=0;i<1350;++i){
  edge(32,(i+1)%1350,(value+1)%4,true,i,value,true,false,0);
  edge(26,0,0,false,i,0,false,true,0);edge(26,0,0,false,(i+1)%1350,0,false,true,0);
  edge(32,i,(value+1)%4,true,i,value,true,false,0);edge(26,0,0,false,i,0,false,true,0);
 }
 for(unsigned kills=1;kills<8;++kills)for(unsigned i:{0U,674U,1349U}){
  edge(32,i,3,true,i,2,true,true,kills);edge(26,0,0,false,i,0,false,true,0);
  edge(26,i,3,true,i,2,false,true,kills);edge(26,0,0,false,i,0,false,true,0);
 }
 for(unsigned i=0;i<1350;++i)edge(26,0,0,false,i,0,false,true,0);
 trace.close();require(bool(trace),"scale trace close");d.final();return edges;
}
int main(int argc,char **argv) {
    try {
        require(argc==3,"usage: Vadmission_probe vectors.txt seed");
        const auto cases=read_cases(argv[1]);const unsigned seed=unsigned(std::stoul(argv[2]));const auto scale_prepared_edges=prepared_scale_ports();const auto header_prepared_edges=prepared_header(seed);const auto prepared_edges=prepared_quant();Bench b(seed);
        unsigned positives=0,negatives=0;uint64_t descriptor_comparisons=0;uint32_t epoch=100;
        const Case *good=nullptr;
        for(const auto &c:cases) {
            b.begin(c,++epoch);b.feed(c);b.finish(c,true);
            if(c.expected_error){++negatives;}else {++positives;descriptor_comparisons+=3;if(!good)good=&c;}
        }
        require(good!=nullptr,"no positive fixture for directed checks");
        std::vector<std::string> directed;
        auto record=[&](const std::string &name){directed.push_back(name);std::cout<<"{\"type\":\"directed\",\"name\":"<<quoted(name)<<",\"status\":\"PASS\"}\n";};
        // Extend the retained coverage floor with complete public-interface
        // mode2 transactions. Each rewrites all1350 scale cells amid external
        // cache writes, then exhaustively checks registered lookup values.
        for(unsigned replay=0;replay<32;++replay){
            b.begin(*good,++epoch);b.feed(*good);b.finish(*good,false);
        }
        record("mode2_scale_collision_recovery_32_packets");
        for(unsigned state:{3u,4u,5u,6u,12u,13u,15u,16u,17u,32u,28u,29u,25u})for(unsigned kind=0;kind<2;++kind) {
            b.begin(*good,++epoch);b.until(*good,state);
            if(state==25)for(unsigned k=0;k<3;++k)b.tick();
            b.cancel(kind);
            record(std::string(kind?"reset_":"abort_")+"state_"+std::to_string(state));
            b.begin(*good,++epoch);b.feed(*good);b.finish(*good,false);
        }
        for(unsigned state:{3u,4u,5u,6u,12u,15u,16u,17u,32u,29u,25u}) {
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
            <<",\"scale_prepared_edges\":"<<scale_prepared_edges<<",\"header_prepared_edges\":"<<header_prepared_edges<<",\"prepared_edges\":"<<prepared_edges<<",\"q_run_edges\":"<<b.q_run_edges<<",\"q_fill_edges\":"<<b.q_fill_edges<<",\"q_fill_writes\":"<<b.q_fill_writes<<",\"scale_lookup_checks\":"<<b.scale_lookup_checks<<",\"lookup_response_edges\":"<<b.lookup_response_edges<<",\"cache_noise_edges\":"<<b.cache_noise_edges<<",\"clock_edges\":"<<b.ticks<<",\"coordinate_rows\":"<<b.coordinate_rows<<",\"residual_marks\":"<<b.residual_marks<<",\"descriptor_comparisons\":"<<descriptor_comparisons<<",\"directed_check_names\":[";
        for(size_t i=0;i<directed.size();++i){if(i)std::cout<<',';std::cout<<quoted(directed[i]);}
        std::cout<<"]}\n";return 0;
    } catch(const std::exception &e) {std::cerr<<"ADMISSION_TEST_FAIL "<<e.what()<<'\n';return 1;}
}
