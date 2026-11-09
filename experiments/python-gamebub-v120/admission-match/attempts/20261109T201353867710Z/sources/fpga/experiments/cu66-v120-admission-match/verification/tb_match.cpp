#include "tb_owner_base.cpp"
#include <cstdio>

struct MatchStats {
    uint64_t edges=0,captures=0,full35_cases=0,random35_cases=0,owned_consumes=0;
    uint64_t true_cases=0,false_cases=0,high32_false=0,cancel_captures=0,idle_holds=0;
    uint64_t natural_cases=0,natural_retries=0;
};
static MatchStats match_stats;

static void match_tick(Vadmission_probe&d,Vadmission_probe___024root&r) {
    d.clk=0;d.eval();require(!d.mismatch,"match all-public preedge");
    const bool capture=QOLD(state)==4U;
    const bool before=QNEW(prepared_header_total_matches);
    const uint64_t total=QOLD(header_packet_total);
    const uint32_t size=QOLD(size_bytes);
    const bool expected=capture?(total==uint64_t(size)):before;
    const bool cancel=d.reset||d.start||d.abort_packet;
    if(capture){++match_stats.captures;match_stats.cancel_captures+=cancel;}
    if(!cancel&&QOLD(state)==5U)++match_stats.owned_consumes;
    d.clk=1;d.eval();require(!d.mismatch,"match all-public posedge");
    require(bool(QNEW(prepared_header_total_matches))==expected,"independent every-edge phase writer/hold");
    d.clk=0;d.eval();require(!d.mismatch,"match all-public falling edge");
    ++match_stats.edges;
}

static void full35_payload(unsigned seed) {
    Vadmission_probe d;auto&r=*d.rootp;std::mt19937 random(seed);
    d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=d.cache_write=d.lookup_req=d.replay_req=d.receipt_ready=0;
    d.packet_bytes=256;d.epoch=seed;match_tick(d,r);d.reset=0;
    auto one=[&](uint64_t total,uint32_t size,unsigned cancel){
        // Explicit synthetic private prestate: this tests the full35 predicate
        // capture, not a reachable packet or an arbitrary CHECK-state proof.
        QBOTH(state,4U);QBOTH(header_index,127U);QBOTH(byte_value,0U);
        QBOTH(header_packet_total,total);QBOTH(size_bytes,size);QBOTH(coord_valid,0U);
        d.reset=cancel&1U;d.start=(cancel&2U)!=0;d.abort_packet=(cancel&4U)!=0;
        match_tick(d,r);
        const bool eq=total==uint64_t(size);
        require(bool(QNEW(prepared_header_total_matches))==eq,"complete35 equality after real byte edge");
        ++match_stats.full35_cases;match_stats.true_cases+=eq;match_stats.false_cases+=!eq;
        match_stats.high32_false+=(uint32_t(total)==size && total>>32U);
        // Never consume an incoherent synthetic header. A real reset next
        // edge retires it; unreset payload must hold through reset and IDLE.
        d.reset=1;d.start=d.abort_packet=0;match_tick(d,r);d.reset=0;
        for(unsigned i=0;i<2;++i){match_tick(d,r);++match_stats.idle_holds;}
    };
    const std::array<uint64_t,19> totals{{0ULL,1ULL,127ULL,128ULL,131ULL,132ULL,258ULL,49152ULL,0x7fffffffULL,0x80000000ULL,0xffffffffULL,0x100000000ULL,0x100000001ULL,0x1ffffffffULL,0x200000000ULL,0x3ffffffffULL,0x400000080ULL,0x7fffffffeULL,0x7ffffffffULL}};
    const std::array<uint32_t,14> sizes{{0U,1U,127U,128U,131U,132U,258U,49152U,49153U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU,65536U}};
    for(uint64_t total:totals)for(uint32_t size:sizes)for(unsigned cancel=0;cancel<8;++cancel)one(total,size,cancel);
    for(unsigned i=0;i<65536;++i){
        const uint32_t size=random();uint64_t total=(uint64_t(random()&7U)<<32U)|random();
        if(i%4U==0)total=size;else if(i%4U==1)total=(uint64_t(1U+(random()%7U))<<32U)|size;
        one(total,size,i%8U);++match_stats.random35_cases;
    }
    d.final();
}

static void coherent_header_consumes(unsigned seed) {
    Vadmission_probe d;auto&r=*d.rootp;std::mt19937 random(seed);
    d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=d.cache_write=d.lookup_req=d.replay_req=d.receipt_ready=0;
    d.packet_bytes=258;d.epoch=seed;match_tick(d,r);d.reset=0;
    for(unsigned i=0;i<4096;++i){
        std::array<uint8_t,128> h{};
        auto put=[&](unsigned at,uint32_t v){for(unsigned j=0;j<4;++j)h[at+j]=uint8_t(v>>(24U-8U*j));};
        const bool key=i&1U;const uint32_t mode=i%5U?0U:random();
        const uint32_t qm=i%7U?16U:random(),hud=i%11U?110U:random(),data=i%13U?0U:random();
        put(0,0x43533838U);h[4]=1;h[5]=key;h[6]=16;h[7]=key?0:3;
        put(8,5);put(12,key?0xffffffffU:4U);put(20,5);h[24]=2;h[25]=0xd0;h[26]=1;h[27]=0xe0;h[29]=32;put(32,65536);
        put(36,mode);put(40,qm);put(44,hud);put(48,data);
        const uint64_t m=128ULL+mode,rs=m+qm,ht=4ULL+hud,re=rs+data,total=re+ht;
        const uint32_t size=i%3U?uint32_t(total):random();
        // Independent first-reason cases overlap the new predicate deliberately.
        const unsigned fault=i%6U;
        if(fault==1)h[0]^=255U;
        if(fault==2)h[127]=1;
        if(fault==3)put(8,0xffffffffU);
        if(fault==4)put(12,key?0U:3U);
        for(unsigned j=0;j<128;++j){QOLD(header)[j]=h[j];QNEW(header)[j]=h[j];}
        QBOTH(state,5U);QBOTH(coord_valid,0U);QBOTH(header_index,127U);QBOTH(size_bytes,size);
        QBOTH(receipt_epoch,seed+i);QBOTH(snapshot_valid,1U);QBOTH(snapshot_fid,4U);QBOTH(snapshot_generation,4ULL);
        QBOTH(header_mode_start,m);QBOTH(header_residual_start,rs);QBOTH(header_hud_tail,ht);QBOTH(header_residual_end,re);QBOTH(header_packet_total,total);
        prime_header_match(d,r);
        const bool invalid=mode>976U||qm<16U||qm>354U||hud<110U||hud>49152U||total!=uint64_t(size)||h[127]!=0;
        const unsigned error=fault==1?4U:invalid?5U:fault==3?6U:fault==4?7U:(key&&mode)?8U:0U;
        match_tick(d,r);
        require(d.error==error&&d.debug_state==(error?27U:key?6U:7U),"independent coherent header first-reason/continuation");
        d.reset=1;match_tick(d,r);d.reset=0;
    }
    d.final();
}

static void natural_header_requests(const std::string&path,unsigned seed) {
    const auto cases=read_cases(path);const Case*good=nullptr;
    for(const auto&c:cases)if(c.expected_error==0){good=&c;break;}
    require(good!=nullptr,"natural header retry reference");
    // Preserve the immutable inherited trace for its four existing independent
    // Python replay oracles. New natural cases have a separately named trace.
    require(std::rename("trace.jsonl","inherited-trace.jsonl")==0,"preserve inherited trace");
    {
    Bench b(seed);uint32_t epoch=seed;
    auto crc=[](const std::vector<uint8_t>&bytes){uint32_t value=0xffffffffU;for(size_t at=0;at+4<bytes.size();++at){value^=bytes[at];for(unsigned j=0;j<8;++j)value=(value>>1U)^((value&1U)?0xedb88320U:0U);}return ~value;};
    auto put=[](std::vector<uint8_t>&bytes,unsigned at,uint32_t v){for(unsigned j=0;j<4;++j)bytes[at+j]=uint8_t(v>>(24U-8U*j));};
    for(uint32_t huge:{0x7fffffffU,0x80000000U,0xffffffffU})for(unsigned at:{36U,40U,44U,48U})for(unsigned priority=0;priority<3;++priority){
        Case c=*good;c.id="v120-full32-header";c.expected_error=priority==1?4U:priority==2?3U:5U;
        put(c.packet,at,huge);if(priority==1)c.packet[0]^=255U;
        put(c.packet,unsigned(c.packet.size()-4U),crc(c.packet));if(priority==2)c.packet.back()^=1U;
        b.begin(c,++epoch);b.feed(c);b.finish(c,false);++match_stats.natural_cases;
        b.begin(*good,++epoch);b.feed(*good);b.finish(*good,false);++match_stats.natural_retries;
    }
    }
    require(std::rename("trace.jsonl","match-natural-trace.jsonl")==0,"retain new natural trace");
    require(std::rename("inherited-trace.jsonl","trace.jsonl")==0,"restore inherited replay input");
}

int main(int argc,char**argv) {
    try {
        require(inherited_owner_main(argc,argv)==0,"complete immutable V119 admission oracles");
        const unsigned seed=unsigned(std::stoul(argv[2]));
        full35_payload(seed);coherent_header_consumes(seed);natural_header_requests(argv[1],seed);
        require(match_stats.full35_cases==67664&&match_stats.random35_cases==65536,"full35 coverage count");
        require(match_stats.captures>0&&match_stats.owned_consumes==4096&&match_stats.true_cases>0&&match_stats.false_cases>0&&match_stats.high32_false>0&&match_stats.cancel_captures>0&&match_stats.idle_holds==135328,"all ownership and hold domains observed");
        require(header_match_priming_edges>0&&match_stats.natural_cases==36&&match_stats.natural_retries==36,"actual header/request and coherent fixture coverage");
        std::cout<<"{\"type\":\"v120_header_match_verdict\",\"status\":\"TEST_PASS\",\"writer_edges\":"<<match_stats.edges<<",\"captures\":"<<match_stats.captures<<",\"prepared_full35_cases\":"<<match_stats.full35_cases<<",\"random_full35\":"<<match_stats.random35_cases<<",\"owned_consumes\":"<<match_stats.owned_consumes<<",\"true_cases\":"<<match_stats.true_cases<<",\"false_cases\":"<<match_stats.false_cases<<",\"high32_alias_rejections\":"<<match_stats.high32_false<<",\"canceled_captures\":"<<match_stats.cancel_captures<<",\"idle_hold_edges\":"<<match_stats.idle_holds<<",\"fixture_priming_edges\":"<<header_match_priming_edges<<",\"natural_packets\":"<<match_stats.natural_cases<<",\"natural_nonreset_retries\":"<<match_stats.natural_retries<<",\"old_require_checks_removed\":0,\"added_natural_public_cycles\":0,\"prepared_predicate_contexts_are_natural_packets\":false}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"V120_HEADER_MATCH_FAIL "<<e.what()<<'\n';return 1;}
}
