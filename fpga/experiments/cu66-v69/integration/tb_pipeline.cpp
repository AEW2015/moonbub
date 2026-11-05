#include "Vcu66_base_pipeline.h"
#include "verilated.h"
#include "../../../..//experiments/cu66-native-v69/decoder.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <random>
#include <sstream>

using cu66::Bytes;
static void need(bool b,const std::string &s){if(!b)throw std::runtime_error(s);}
static Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"open fixture");return {std::istreambuf_iterator<char>(f),{}};}
static uint32_t le(const Bytes&p,unsigned offset){return uint32_t(p.at(offset))|(uint32_t(p.at(offset+1))<<8)|(uint32_t(p.at(offset+2))<<16)|(uint32_t(p.at(offset+3))<<24);}
struct Inputs{std::array<Bytes,3> ab;std::array<unsigned,3> dispatch,blocks;std::array<uint8_t,1350> qmap;};
static Inputs parse(const Bytes&p){Inputs x;unsigned base=76,nv=le(p,base+44),at=base+60+338+nv;for(unsigned i=0;i<1350;i++)x.qmap[i]=(p.at(base+60+i/4)>>(6-2*(i%4)))&3;for(unsigned a=0;a<3;a++){unsigned n=le(p,base+48+a*4);x.dispatch[a]=p.at(at);x.blocks[a]=a==0?(x.dispatch[a]==6?5144:5400):(x.dispatch[a]==6?1331:1350);x.ab[a]=Bytes(p.begin()+at+1,p.begin()+at+n);at+=n;}return x;}
struct Event{bool started,configured,read_request,read_response,q_request,ref_request,ref_response,write,tag;};
struct Sim{
 Vcu66_base_pipeline d;std::mt19937 rng;uint64_t clocks=0;
 bool randomize,shared_bus;unsigned next_bus=0;uint64_t bus_beats=0,display_reserved=0,refresh_reserved=0;bool read_pending=false,q_pending=false,ref_pending=false,write_pending=false;
 unsigned read_delay=0,q_delay=0,ref_delay=0,write_delay=0,read_address=0,read_plane=0,q_address=0,ref_address=0;
 uint64_t reads=0,ref_reads=0,writes=0,read_stalls=0,write_stalls=0;
 Inputs input;std::shared_ptr<const cu66::Frame> reference,expected;
 std::array<Bytes,3> candidate;unsigned ordinal=0;unsigned fault=0;
 bool held_tile=false;std::array<uint32_t,16> held_pixels{};unsigned held_index=0,held_plane=0;
 explicit Sim(unsigned seed,bool shared=false):rng(seed),randomize(seed!=0),shared_bus(shared){d.clk=0;d.rst=1;d.abort_i=0;d.start_valid=0;d.plane_cfg_valid=0;d.rd_rsp_valid=0;d.q_rsp_valid=0;d.ref_rsp_valid=0;d.rd_req_ready=0;d.q_req_ready=0;d.ref_req_ready=0;d.tile_ready=0;d.tag_ready=0;d.write_done=0;d.write_error=0;tick(false);tick(false);d.rst=0;tick(false);}
 Event tick(bool check=true){d.clk=0;d.eval();
  Event e{bool(d.start_valid&&d.start_ready),bool(d.plane_cfg_valid&&d.plane_cfg_ready),bool(d.rd_req_valid&&d.rd_req_ready),bool(d.rd_rsp_valid&&d.rd_rsp_ready),bool(d.q_req_valid&&d.q_req_ready),bool(d.ref_req_valid&&d.ref_req_ready),bool(d.ref_rsp_valid&&d.ref_rsp_ready),bool(d.tile_valid&&d.tile_ready),bool(d.tag_valid&&d.tag_ready)};
  if(check&&held_tile&&!d.abort_i&&!d.error){need(d.tile_valid&&d.tile_index==held_index&&d.tile_plane==held_plane,"tile valid/metadata changed under memory stall");for(unsigned i=0;i<16;i++)need(d.tile_pixels[i]==held_pixels[i],"tile bytes changed under memory stall");}
  held_tile=check&&!d.abort_i&&!d.error&&d.tile_valid&&!d.tile_ready;
  if(held_tile){held_index=d.tile_index;held_plane=d.tile_plane;for(unsigned i=0;i<16;i++)held_pixels[i]=d.tile_pixels[i];}
  if(check&&e.write){need(expected!=nullptr,"expected frame missing");unsigned a=ordinal<5400?0:ordinal<6750?1:2,b=ordinal-(a==0?0:a==1?5400:6750),width=a==0?720:360;need(d.tile_frame_id==expected->id&&d.tile_plane==a&&d.tile_index==b&&bool(d.tile_last)==(ordinal==8099),"tile order/identity/last");for(unsigned i=0;i<64;i++){unsigned at=(b/(width/8)*8+i/8)*width+(b%(width/8))*8+i%8;uint8_t pixel=uint8_t(d.tile_pixels[i/4]>>(8*(i%4)));if(pixel!=expected->planes[a][at])throw std::runtime_error("canonical tile mismatch ordinal="+std::to_string(ordinal)+" pixel="+std::to_string(i)+" got="+std::to_string(pixel)+" expected="+std::to_string(expected->planes[a][at]));candidate[a][at]=pixel;}ordinal++;writes++;}
  d.clk=1;d.eval();clocks++;need(clocks<10000000000ull,"global watchdog");return e;
 }
 void drive(){
  d.rd_req_ready=!read_pending&&(!randomize||rng()%5!=0);d.rd_rsp_valid=read_pending&&read_delay==0;
  if(d.rd_rsp_valid)d.rd_rsp_data=input.ab.at(read_plane).at(read_address);
  d.q_req_ready=!q_pending&&(!randomize||rng()%4!=0);d.q_rsp_valid=q_pending&&q_delay==0;
  if(d.q_rsp_valid)d.q_rsp_code=fault==2?3:input.qmap.at(q_address);
  d.ref_req_ready=!ref_pending&&(!randomize||rng()%4!=0);d.ref_rsp_valid=ref_pending&&ref_delay==0;
  if(d.ref_rsp_valid){need(reference!=nullptr,"reference lease missing");unsigned a=ref_address>>17,b=ref_address&131071,width=a==0?720:360;d.ref_rsp_tile=fault==3?ref_address+1:ref_address;for(unsigned w=0;w<16;w++){uint32_t word=0;for(unsigned j=0;j<4;j++){unsigned i=w*4+j,at=(b/(width/8)*8+i/8)*width+(b%(width/8))*8+i%8;word|=uint32_t(reference->planes[a].at(at))<<(j*8);}d.ref_rsp_pixels[w]=word;}}
  d.clk=0;d.eval();
  d.tile_ready=!write_pending&&(!randomize||rng()%4!=0);
  d.write_done=write_pending&&write_delay==0;d.write_error=fault==7;d.tag_ready=0;
 }
 void service(const Event&e){
  if(q_pending&&q_delay)q_delay--;
  if(shared_bus){
   if(clocks%7800<16)refresh_reserved++;
   else if(clocks%2==0)display_reserved++;
   else if(!randomize||rng()%10!=0){
    for(unsigned i=0;i<3;i++){unsigned who=(next_bus+i)%3;
     if(who==0&&read_pending&&read_delay){read_delay--;bus_beats++;next_bus=1;break;}
     if(who==1&&ref_pending&&ref_delay){ref_delay--;bus_beats++;next_bus=2;break;}
     if(who==2&&write_pending&&write_delay){write_delay--;bus_beats++;next_bus=0;break;}
    }
   }
   if(write_pending&&write_delay)write_stalls++;
  }else{
   if(read_pending&&read_delay)read_delay--;if(ref_pending&&ref_delay)ref_delay--;
   if(write_pending&&write_delay){write_delay--;write_stalls++;}
  }
  if(e.read_request){need(!read_pending,"multiple compressed reads");read_pending=true;read_delay=shared_bus?1:(randomize?1+rng()%8:0);read_address=d.rd_req_addr;read_plane=d.rd_req_plane;reads++;}
  if(e.read_response)read_pending=false;
  if(e.q_request){need(!q_pending,"multiple qmap reads");q_pending=true;q_delay=0;q_address=d.q_req_index;}
  if(d.q_rsp_valid&&q_pending&&q_delay==0)q_pending=false;
  if(e.ref_request){need(!ref_pending,"multiple reference reads");ref_pending=true;ref_delay=shared_bus?32:(randomize?32+rng()%65:0);ref_address=d.ref_req_tile;ref_reads++;}
  if(e.ref_response)ref_pending=false;
  if(d.write_done&&write_pending)write_pending=false;
  if(e.write){need(!write_pending,"multiple accepted writes");write_pending=true;write_delay=shared_bus?32:(randomize?32+rng()%65:0);}
 }
 void settle(){for(unsigned i=0;i<4;i++){drive();auto e=tick(false);service(e);}}
 void run(const Bytes&p,std::shared_ptr<const cu66::Frame>gold,std::shared_ptr<const cu66::Frame>ref,unsigned mode=0){
  settle();need(d.start_ready,"frame start not ready");fault=mode;input=parse(p);expected=gold;reference=ref;ordinal=0;held_tile=false;write_pending=false;
  for(unsigned a=0;a<3;a++)candidate[a].assign(a==0?345600:86400,0);
  if(mode==1)input.ab[0][0]^=1;
  d.frame_id=gold->id;d.key=gold->key;
  for(unsigned w=0;w<4;w++){uint32_t word=0;for(unsigned j=0;j<4;j++)word=(word<<8)|gold->canonical_tag[w*4+j];d.expected_tag[3-w]=word;}
  if(mode==4)d.expected_tag[0]^=1;
  d.start_valid=1;need(tick().started,"frame start handshake");d.start_valid=0;
  uint64_t begun=clocks,r0=reads,f0=ref_reads,w0=writes,s0=write_stalls;unsigned next_plane=0;bool done=false,aborting=false;unsigned abort_wait=0;
  while(!done){need(clocks-begun<20000000,"frame watchdog");
   d.plane_cfg_valid=next_plane<3;
   if(next_plane<3){d.plane_cfg_plane=next_plane;d.plane_cfg_dispatch=input.dispatch[next_plane];d.plane_cfg_bytes=input.ab[next_plane].size();d.plane_cfg_blocks=input.blocks[next_plane];}
   drive();
   if(mode==5&&!aborting&&ref_pending&&ref_delay>4){d.abort_i=1;aborting=true;}
   if(mode==6&&!aborting&&read_pending&&read_delay>0){d.abort_i=1;aborting=true;}
   if(mode==8&&!aborting&&write_pending&&write_delay>4){d.abort_i=1;aborting=true;}
   if(aborting){need(!d.tag_valid,"aborted frame exposed tag");if((ref_pending||read_pending||q_pending||write_pending)&&!d.abort_i)need(!d.start_ready,"lease released before outstanding reads drained");}
   d.clk=0;d.eval();
   if(d.tag_valid){need(!write_pending,"tag exposed before write completion");need(mode==0,"invalid frame exposed successful tag");need(ordinal==8100&&d.accepted_tiles==8100,"frame tile coverage");need(cu66::canonical_tag(candidate)==gold->canonical_tag,"candidate canonical hash");std::ostringstream s;for(int i=7;i>=0;i--)s<<std::hex<<std::setw(8)<<std::setfill('0')<<d.digest[i];cu66::SHA256 h;const uint8_t geometry[]={0xd0,2,0xe0,1};h.update({geometry,4});for(auto&v:candidate)h.update(v);auto sha=h.finish();std::ostringstream want;for(auto x:sha)want<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(x);need(s.str()==want.str(),"full RTL SHA256 mismatch");if(abort_wait++>7)d.tag_ready=1;}
   auto e=tick(!d.abort_i);if(e.configured)next_plane++;service(e);
   d.abort_i=0;
   if(e.tag)done=true;
   if(d.error&&!d.busy){need((mode>=1&&mode<=4)||mode==7,"unexpected RTL error "+std::to_string(d.error_code));done=true;}
   if(aborting&&!d.busy){need(!read_pending&&!ref_pending&&!q_pending&&!write_pending,"abort completed with leased memory transaction");done=true;}
  }
  d.plane_cfg_valid=0;d.tag_ready=0;
  if(mode==0)need(!d.error,"valid frame error");else if(mode<=4||mode==7){need(d.error,"fault not rejected");const unsigned codes[]={0,0x12,0x31,0x33,0x50,0,0,0x61};need(d.error_code==codes[mode],"fault rejected for wrong reason mode="+std::to_string(mode)+" code="+std::to_string(d.error_code));}else need(aborting,"abort probe not reached");
  std::cout<<"FRAME_PASS id="<<gold->id<<" key="<<gold->key<<" mode="<<mode<<" clocks="<<clocks-begun<<" tiles="<<ordinal<<" byte_reads="<<reads-r0<<" reference_tiles="<<ref_reads-f0<<" writes="<<writes-w0<<" serialized_write_stalls="<<write_stalls-s0<<" error="<<unsigned(d.error_code)<<std::endl;
 }
};
int main(int argc,char**argv){try{need(argc>=4,"index.tsv seed per_chain");std::filesystem::path index=argv[1];unsigned seed=unsigned(std::stoul(argv[2])),limit=unsigned(std::stoul(argv[3]));Sim sim(seed,argc>4&&std::string(argv[4])=="--shared-bus");std::ifstream f(index);need(bool(f),"index open");std::string line;unsigned chain=~0u,count=0,frames=0;cu66::Decoder decoder;std::shared_ptr<const cu66::Frame> ref;Bytes first,second;std::shared_ptr<const cu66::Frame> first_gold,second_gold;
 while(std::getline(f,line)){std::stringstream s(line);std::string a,b,path;std::getline(s,a,'\t');std::getline(s,b,'\t');std::getline(s,path,'\t');unsigned c=unsigned(std::stoul(a));if(c!=chain){chain=c;count=0;decoder=cu66::Decoder();ref=nullptr;}if(count++>=limit)continue;auto p=load(index.parent_path()/path);auto gold=decoder.receive(p);sim.run(p,gold,ref);if(frames==0){first=p;first_gold=gold;}else if(frames==1){second=p;second_gold=gold;}ref=gold;frames++;}
 need(frames>1,"actual key/P coverage");for(unsigned mode=1;mode<=4;mode++)sim.run(mode==3?second:first,mode==3?second_gold:first_gold,mode==3?first_gold:nullptr,mode);sim.run(first,first_gold,nullptr,7);if(seed){sim.run(second,second_gold,first_gold,5);sim.run(first,first_gold,nullptr,6);sim.run(first,first_gold,nullptr,8);}sim.run(first,first_gold,nullptr);
 std::cout<<"PASS actual_frames="<<frames<<" faults=5 aborts="<<(seed?3:0)<<" recovery=1 seed="<<seed<<" clocks="<<sim.clocks<<" shared_bus="<<sim.shared_bus<<" bus_beats="<<sim.bus_beats<<" display_reserved="<<sim.display_reserved<<" refresh_reserved="<<sim.refresh_reserved<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
