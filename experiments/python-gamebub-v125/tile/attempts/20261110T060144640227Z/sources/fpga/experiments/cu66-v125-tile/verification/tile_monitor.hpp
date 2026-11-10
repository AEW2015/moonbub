#pragma once
#include <array>
static const std::array<const char*,9> tile_writer_names{{"header","key_step","key_terminal","tag_commit","hidden_jump","mixed_step","group_step","plane_clear","group_begin"}};
struct TileMonitor {
    std::array<uint64_t,9> natural_writers{},prepared_writers{},first_consumes{};
    std::array<uint64_t,9> overwritten_before_consume{};
    std::array<uint64_t,8> cancels{};
    std::array<std::array<uint64_t,8>,33> cancel_state_counts{};
    uint64_t edges=0,natural_edges=0,prepared_edges=0,holds=0,consume_edges=0,natural_starts=0;
    unsigned last_tile=0,last_group=0;bool first_tile=false,first_group=false;
};
static TileMonitor tile_monitor;
static bool tile_hidden_oracle(unsigned p,uint32_t t){
    if(p)return t>=1046U&&t<=1064U;
    constexpr uint32_t lo[]={633,723,993,1083,4071,4161,4251,4431,4521};
    constexpr uint32_t hi[]={651,741,1011,1101,4110,4200,4290,4460,4550};
    for(unsigned i=0;i<9;++i)if(t>=lo[i]&&t<=hi[i])return true;
    return false;
}
struct TileBefore {
    unsigned state,p,tag,bits,mixed,second,first,bit,flags;uint32_t t,g,visible,epoch;
    bool h,terminal,group,tile_valid;
};
#define TM(n) r.admission_probe__DOT__candidate__DOT__##n
static TileBefore tile_before(Vadmission_probe&d,bool natural){
    auto&r=*d.rootp;TileBefore b{TM(state),TM(plane),TM(group_tag),TM(bits_left),TM(mixed_bit),TM(tag_second),TM(first_tag_bit),unsigned(TM(bit_cache)>>7),unsigned(bool(d.reset))|unsigned(bool(d.start))*2U|unsigned(bool(d.abort_packet))*4U,TM(tile),TM(group_end),TM(group_visible),TM(receipt_epoch),bool(TM(prepared_tile_hidden)),bool(TM(prepared_tile_terminal)),bool(TM(prepared_group_terminal)),bool(TM(tile_pred_owner_valid))};
    ++tile_monitor.edges;if(natural)++tile_monitor.natural_edges;else ++tile_monitor.prepared_edges;
    if(b.flags)return b;
    if(b.state==6U||b.state==10U||b.state==11U){
        require(TM(tile_pred_owner_valid)&&TM(tile_pred_owner_tile)==b.t&&TM(tile_pred_owner_plane)==b.p&&TM(tile_pred_owner_epoch)==b.epoch,"monitor independent complete tile owner at consume");
        require(b.h==tile_hidden_oracle(b.p,b.t)&&b.terminal==(b.t==(b.p?1350U:5400U)),"monitor independent full32 current tile predicates");
        if(!tile_monitor.first_tile){++tile_monitor.first_consumes[tile_monitor.last_tile];tile_monitor.first_tile=true;}
        if(b.state==10U){
            require(TM(group_pred_owner_valid)&&TM(group_pred_owner_tile)==b.t&&TM(group_pred_owner_plane)==b.p&&TM(group_pred_owner_epoch)==b.epoch&&TM(group_pred_owner_end)==b.g&&b.group==(b.t==b.g),"monitor independent complete group owner at first/held consume");
            if(!tile_monitor.first_group){++tile_monitor.first_consumes[tile_monitor.last_group];tile_monitor.first_group=true;}
        }
        ++tile_monitor.consume_edges;
    }
    return b;
}
static void tile_after(Vadmission_probe&d,const TileBefore&b,bool natural){
    auto&r=*d.rootp;
    if(b.flags){
        require(!TM(tile_pred_owner_valid)&&!TM(group_pred_owner_valid),"monitor reset/start/abort invalidates both owners");
        require(bool(TM(prepared_tile_hidden))==b.h&&bool(TM(prepared_tile_terminal))==b.terminal&&bool(TM(prepared_group_terminal))==b.group,"monitor cancel leaves payload unreset");
        ++tile_monitor.cancels[b.flags];tile_monitor.first_tile=tile_monitor.first_group=false;
        require(b.state<33U,"cancel monitor original state domain");++tile_monitor.cancel_state_counts[b.state][b.flags];
        if(natural&&b.flags==2U)++tile_monitor.natural_starts;
        return;
    }
    int writer=-1;bool group=false;
    if(b.state==5U&&(TM(state)==6U||TM(state)==7U))writer=0;
    else if(b.state==6U)writer=b.t==(b.p?1350U:5400U)?2:1;
    else if(b.state==8U&&b.bits){
        if(b.mixed){writer=5;group=true;}
        else if(b.second){writer=b.visible==0U&&((b.first<<1U)|b.bit)==3U?4:3;group=true;}
    }else if(b.state==10U&&b.t!=b.g&&(tile_hidden_oracle(b.p,b.t)||b.tag==0U||b.tag==1U)){writer=6;group=true;}
    else if(b.state==11U&&b.t==(b.p?1350U:5400U)&&b.p!=2U)writer=7;
    if(writer>=0){
        if(b.tile_valid&&!tile_monitor.first_tile)++tile_monitor.overwritten_before_consume[tile_monitor.last_tile];
        (natural?tile_monitor.natural_writers:tile_monitor.prepared_writers)[unsigned(writer)]++;
        const unsigned p=TM(plane);const uint32_t t=TM(tile);
        require(bool(TM(prepared_tile_hidden))==tile_hidden_oracle(p,t)&&bool(TM(prepared_tile_terminal))==(t==(p?1350U:5400U)),"monitor successor scalar key after real writer");
        require(TM(tile_pred_owner_valid)&&TM(tile_pred_owner_tile)==t&&TM(tile_pred_owner_plane)==p&&TM(tile_pred_owner_epoch)==TM(receipt_epoch),"monitor successor full tile owner");
        require(bool(TM(group_pred_owner_valid))==group,"monitor exact group-domain ownership writer");
        tile_monitor.last_tile=unsigned(writer);tile_monitor.first_tile=false;
        if(group){require(bool(TM(prepared_group_terminal))==(t==TM(group_end))&&TM(group_pred_owner_end)==TM(group_end)&&TM(group_pred_owner_tile)==t,"monitor successor full group key and equality");tile_monitor.last_group=unsigned(writer);tile_monitor.first_group=false;}
    }else{
        require(bool(TM(prepared_tile_hidden))==b.h&&bool(TM(prepared_tile_terminal))==b.terminal&&bool(TM(prepared_group_terminal))==b.group,"monitor nonwriter holds all private payload");++tile_monitor.holds;
    }
    if(b.state==7U){require(!TM(group_pred_owner_valid),"monitor new group end invalid until real tag commit");(natural?tile_monitor.natural_writers:tile_monitor.prepared_writers)[8]++;}
}
#undef TM
