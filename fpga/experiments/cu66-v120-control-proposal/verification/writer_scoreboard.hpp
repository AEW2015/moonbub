#pragma once
#include <map>

// Independent one-edge state-transition oracles. Neither oracle reads a DUT
// poststate to manufacture its expected payload. Initial unreset bits are
// observed before the first edge, then every write and hold is checked.
#define COLD(n) d.rootp->ingress_probe__DOT__reference_dut__DOT__##n
#define CNEW(n) d.rootp->ingress_probe__DOT__dut__DOT__##n
struct WriterSnapshot {
    uint32_t state,size,addr,next_addr,epoch,base,index,count,kind,continuation,band,tail;
    uint32_t received,cursor,length,remaining,position,offset,replay_bits,descriptor_length;
    bool bounds,descriptor_ready,cursor_bad,raw_valid,word_valid,replay_nonzero;
    bool context_active,context_done,context_failure,ctx_valid,ctx_ready;
};
struct WriterCoverage {
    uint64_t edges=0,old_writes=0,new_writes=0,spec_only=0,owned_tuples=0;
    uint64_t reset_spec=0,start_spec=0,abort_spec=0,bad_descriptor_spec=0;
    uint64_t context_fault_spec=0,context_done_spec=0,held_replay_spec=0;
    uint64_t cache_captures=0,owned_cache_wait_checks=0,unowned_cache_inputs=0;
    std::array<uint64_t,4> initial{};
};
static WriterCoverage writer_coverage;
static WriterSnapshot writer_snapshot_old(Vingress_probe&d) {
    return {COLD(state),COLD(size_bytes),COLD(prepared_request_addr),COLD(next_address_at_request),
        COLD(context_epoch),COLD(fetch_base),COLD(fetch_index),COLD(fetch_count),COLD(fetch_kind),
        COLD(fetch_return),COLD(band),COLD(descriptor_last_addr),COLD(received),COLD(cursor),
        COLD(active_length),COLD(active_remaining),COLD(raw_position),COLD(active_offset),COLD(replay_bits),COLD(lengths)[COLD(band)],
        bool(COLD(prepared_request_in_bounds)),bool(COLD(descriptor_ready)),bool(COLD(active_cursor_bad)),
        bool(COLD(raw_valid)),bool(COLD(word_valid)),bool(COLD(replay_nonzero)),bool(COLD(context_active)),
        bool(COLD(ctx_done)),bool(COLD(ctx_error)),bool(COLD(ctx_valid)),bool(COLD(ctx_ready))};
}
static WriterSnapshot writer_snapshot_new(Vingress_probe&d) {
    return {CNEW(state),CNEW(size_bytes),CNEW(prepared_request_addr),CNEW(next_address_at_request),
        CNEW(context_epoch),CNEW(fetch_base),CNEW(fetch_index),CNEW(fetch_count),CNEW(fetch_kind),
        CNEW(fetch_return),CNEW(band),CNEW(descriptor_last_addr),CNEW(received),CNEW(cursor),
        CNEW(active_length),CNEW(active_remaining),CNEW(raw_position),CNEW(active_offset),CNEW(replay_bits),CNEW(lengths)[CNEW(band)],
        bool(CNEW(prepared_request_in_bounds)),bool(CNEW(descriptor_ready)),bool(CNEW(active_cursor_bad)),
        bool(CNEW(raw_valid)),bool(CNEW(word_valid)),bool(CNEW(replay_nonzero)),bool(CNEW(context_active)),
        bool(CNEW(ctx_done)),bool(CNEW(ctx_error)),bool(CNEW(ctx_valid)),bool(CNEW(ctx_ready))};
}
static int writer_initial_kind(Vingress_probe&d,const WriterSnapshot&s) {
    if(d.reset||d.abort_packet||d.start||(s.context_active&&(s.context_failure||s.context_done)))return -1;
    switch(s.state){
        case 1:
            if(d.in_valid&&bool(d.in_last)==(uint32_t(s.received+1U)==s.size)&&
               uint32_t(s.received+1U)==s.size)return 0;
            break;
        case 3:
            if(!s.descriptor_ready&&s.length>=6U&&!s.cursor_bad&&s.length<=s.remaining)return 1;
            break;
        case 5:
            if(!(s.ctx_valid&&s.ctx_ready)&&!s.word_valid&&s.replay_nonzero)return 2;
            break;
        case 6: if(!s.raw_valid)return 3;break;
        default:break;
    }
    return -1;
}
static int writer_initial_kind(Vingress_probe&d) {
    return writer_initial_kind(d,writer_snapshot_old(d));
}
static uint32_t writer_initial_addr(const WriterSnapshot&s,unsigned kind) {
    switch(kind){
        case 0:return 0;
        case 1:return s.cursor;
        case 2:return uint32_t(s.offset+(s.replay_bits>>3));
        case 3:return uint32_t(42U+2U*s.position);
        default:throw std::runtime_error("initial payload kind domain");
    }
}
static bool writer_in_bounds(uint32_t a,uint32_t size) {return a<size&&a<49152U;}
struct AddressCacheOwner {bool valid=false;uint32_t old_next=0,new_next=0;};
static std::map<Vingress_probe*,AddressCacheOwner> address_cache_owners;
static uint32_t request_next_math(const WriterSnapshot&s){
    const uint32_t index=(s.index+1U)&63U;
    uint32_t address=uint32_t(s.base+index);
    if(s.kind==0&&index>=42U)address=uint32_t(s.size-4U+index-42U);
    if(s.kind==1&&index==6U)address=uint32_t(s.base+s.descriptor_length-1U);
    return address;
}
struct ControlPrivateStep {
    uint32_t old_addr,new_addr;
    uint32_t old_next=0,new_next=0;
    bool old_bounds,new_bounds,request=false,retire=false;
    explicit ControlPrivateStep(Vingress_probe&d) {
        const auto old=writer_snapshot_old(d),now=writer_snapshot_new(d);
        const auto owner=address_cache_owners[&d];
        request=d.stage_read_req;
        retire=d.reset||d.start||d.abort_packet||d.stage_read_rsp||
            (old.context_active&&(old.context_failure||old.context_done));
        if(request){old_next=request_next_math(old);new_next=request_next_math(now);}
        old_addr=old.addr;old_bounds=old.bounds;new_addr=now.addr;new_bounds=now.bounds;
        bool old_write=false,new_write=false;
        if(old.state==13){
            if(owner.valid){
                need(old.next_addr==owner.old_next&&now.next_addr==owner.new_next,
                     "owned future-address cache differs from independent preceding-request math");
                old_addr=owner.old_next;++writer_coverage.owned_cache_wait_checks;
            }else{
                need(retire,"live WAIT lacks a real independent cache owner");
                old_addr=old.next_addr;++writer_coverage.unowned_cache_inputs;
            }
            old_bounds=writer_in_bounds(old_addr,old.size);old_write=true;
        }
        const int initial=writer_initial_kind(d,old);
        if(initial>=0){old_addr=writer_initial_addr(old,unsigned(initial));old_bounds=writer_in_bounds(old_addr,old.size);old_write=true;++writer_coverage.initial[unsigned(initial)];}
        if(now.state==13){new_addr=owner.valid?owner.new_next:now.next_addr;new_write=true;}
        else if(now.state==1){new_addr=0;new_write=true;}
        else if(now.state==3){new_addr=now.cursor;new_write=true;}
        else if(now.state==5){new_addr=uint32_t(now.offset+(now.replay_bits>>3));new_write=true;}
        else if(now.state==6){new_addr=uint32_t(42U+2U*now.position);new_write=true;}
        if(new_write)new_bounds=writer_in_bounds(new_addr,now.size);
        writer_coverage.old_writes+=old_write;writer_coverage.new_writes+=new_write;
        if(new_write&&!old_write){
            ++writer_coverage.spec_only;
            writer_coverage.reset_spec+=bool(d.reset);writer_coverage.start_spec+=bool(d.start);
            writer_coverage.abort_spec+=bool(d.abort_packet);
            writer_coverage.bad_descriptor_spec+=now.state==3&&(!now.descriptor_ready)&&
                (now.length<6U||now.cursor_bad||now.length>now.remaining);
            writer_coverage.context_fault_spec+=now.context_active&&now.context_failure;
            writer_coverage.context_done_spec+=now.context_active&&now.context_done;
            writer_coverage.held_replay_spec+=now.state==5&&now.word_valid&&!(now.ctx_valid&&now.ctx_ready);
        }
    }
    void finish(Vingress_probe&d)const {
        need(COLD(prepared_request_addr)==old_addr&&bool(COLD(prepared_request_in_bounds))==old_bounds,
             "every-edge original writer oracle");
        need(CNEW(prepared_request_addr)==new_addr&&bool(CNEW(prepared_request_in_bounds))==new_bounds,
             "every-edge phase-local writer oracle");
        need(COLD(descriptor_last_addr)==CNEW(descriptor_last_addr),"unchanged descriptor-tail private pair");
        if(retire)address_cache_owners[&d].valid=false;
        if(request){
            need(COLD(next_address_at_request)==old_next&&CNEW(next_address_at_request)==new_next,
                 "actual request did not capture the independently computed wrapped next address");
            address_cache_owners[&d]={true,old_next,new_next};++writer_coverage.cache_captures;
        }
        if(CNEW(state)==12&&!d.reset&&!d.start&&!d.abort_packet){
            need(COLD(context_epoch)==CNEW(context_epoch)&&COLD(size_bytes)==CNEW(size_bytes)&&
                 COLD(fetch_kind)==CNEW(fetch_kind)&&COLD(fetch_count)==CNEW(fetch_count)&&
                 COLD(fetch_base)==CNEW(fetch_base)&&COLD(fetch_index)==CNEW(fetch_index)&&
                 COLD(fetch_return)==CNEW(fetch_return)&&COLD(band)==CNEW(band)&&
                 COLD(prepared_request_addr)==CNEW(prepared_request_addr)&&
                 COLD(prepared_request_in_bounds)==CNEW(prepared_request_in_bounds),
                 "complete owned request tuple remains exact");
            ++writer_coverage.owned_tuples;
        }
        ++writer_coverage.edges;
    }
};
