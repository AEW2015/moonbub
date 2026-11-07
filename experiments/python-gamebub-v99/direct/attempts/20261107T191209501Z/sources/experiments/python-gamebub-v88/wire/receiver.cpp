// Compact CS88 research receiver, forked from frozen CS85: reconstructs
// native pixels, and verifies C2 content/HUD seals before publishing state.
// This is host C++, not synthesizable RTL or a cycle-accurate FPGA model.
#include "../../cu66-native-v69/decoder.hpp"
#include "../entropy/codec.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
using namespace cu66;
using Digest=std::array<uint8_t,32>;
static constexpr size_t MAX_WIRE=2*1024*1024;
struct BE {
  View view; size_t pos=0;
  explicit BE(View v):view(v) {}
  unsigned byte() { need(pos<view.n,"CS88 truncated field");return view[pos++]; }
  uint16_t u16() { unsigned a=byte();return uint16_t((a<<8)|byte()); }
  uint32_t u32() { uint32_t a=u16();return (a<<16)|u16(); }
  uint64_t u64() { uint64_t a=u32();return (a<<32)|u32(); }
  View take(size_t n) { auto out=view.sub(pos,n);pos+=n;return out; }
  Digest digest() { Digest out{};auto v=take(32);std::copy(v.p,v.p+32,out.begin());return out; }
  std::string magic() { auto v=take(4);return {reinterpret_cast<const char*>(v.p),4}; }
  void end() const { need(pos==view.n,"CS88 trailing fields"); }
};
static void be(Bytes &out,uint64_t value,unsigned bytes) {
  for(unsigned i=bytes;i;--i) out.push_back(uint8_t(value>>(8*(i-1))));
}
static void append(Bytes &out,View value) { out.insert(out.end(),value.p,value.p+value.n); }
static void append(Bytes &out,const Digest &value) { out.insert(out.end(),value.begin(),value.end()); }
static Digest context() {
  const std::string value=R"({"geometry":[720,480,5400,1350,1350],"granularity":16,"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"})";
  return sha256({reinterpret_cast<const uint8_t*>(value.data()),value.size()});
}
static Bytes hidden_profile() {
  Bytes mask;mask.reserve(8100);
  for(unsigned axis=0;axis<3;++axis) {
    auto safe=axis==0?SAFE0:axis==1?SAFE1:SAFE2;
    for(unsigned tile=0;tile<(axis?1350u:5400u);++tile) mask.push_back(safe[tile]!=0);
  }
  need(hex(sha256(mask))=="e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5","CS88 fixed mask");
  return mask;
}
static Bytes modes(View body,bool key,unsigned method) {
  need(body.n<=976&&method<=3,"CS88 mode bounds");
  Bytes visible;auto mask=hidden_profile();
  if(key) {need(method==0&&body.n==0,"CS88 implicit key map");visible.assign(7806,1);}
  else if(method==1) {
    need(body.n==976&&!(body[975]&3),"CS88 bitset padding");
    for(unsigned i=0;i<7806;++i) visible.push_back((body[i/8]>>(7-i%8))&1);
  } else if(method==2) {
    for(size_t i=0;i<body.n;++i) {
      unsigned count=(body[i]&127)+1;need(visible.size()+count<=7806,"CS88 run overrun");
      visible.insert(visible.end(),count,body[i]>>7);
    }
    need(visible.size()==7806,"CS88 run underrun");
  } else if(method==3) {
    Bytes result(8100,1);size_t bitpos=0;unsigned offset=0,covered=0;
    auto bit=[&]() {
      need(bitpos<body.n*8,"CS88 grouped truncation");
      unsigned value=(body[bitpos/8]>>(7-bitpos%8))&1;++bitpos;return value;
    };
    for(unsigned plane=0;plane<3;++plane) {
      unsigned count=plane?1350:5400;
      for(unsigned begin=0;begin<count;begin+=16) {
        unsigned high=bit();unsigned tag=high*2+bit();std::vector<unsigned> indices;
        for(unsigned t=begin;t<std::min(begin+16,count);++t) if(!mask[offset+t])indices.push_back(offset+t);
        if(indices.empty()) {need(tag==3,"CS88 grouped empty tag");continue;}
        need(tag!=3,"CS88 grouped invalid tag");covered+=unsigned(indices.size());
        if(tag<2) {for(auto t:indices) result[t]=tag?2:0;}
        else {
          unsigned ones=0;
          for(auto t:indices) {auto value=bit();ones+=value;result[t]=value?2:0;}
          need(ones>0&&ones<indices.size(),"CS88 grouped noncanonical mixed tag");
        }
      }
      offset+=count;
    }
    need(covered==7806&&(bitpos+7)/8==body.n,"CS88 grouped exact length");
    while(bitpos<body.n*8)need(bit()==0,"CS88 grouped padding");
    return result;
  } else need(false,"CS88 implicit map on delta");
  Bytes out;size_t at=0;
  for(auto hidden:mask)out.push_back(hidden?1:(visible[at++]?2:0));
  need(at==7806&&out.size()==8100,"CS88 complete map");return out;
}
// Independent native QM87 parser; provisional scales commit with accepted pixels.
static std::array<unsigned,1350> quantizers(View block,const Bytes &operations,
                                           const std::array<unsigned,1350> *previous) {
  need(block.n>=16&&block.n<=354,"QM87 block bound");
  BE crc(block.sub(block.n-4,4));need(crc32(block.sub(0,block.n-4))==crc.u32(),"QM87 CRC");
  BE head(block.sub(0,12));need(head.magic()=="QM87"&&head.byte()==1,"QM87 profile");
  unsigned method=head.byte();need(method<=6&&head.u16()==1350,"QM87 method/cells");
  unsigned length=head.u16(),required=head.u16();need(block.n==length+16,"QM87 exact length");
  std::array<bool,1350> active{};unsigned total=0;
  for(unsigned t=0;t<8100;++t) if(operations[t]==2) {
    unsigned cell=t<5400?((t/90)/2)*45+(t%90)/2:(t-5400)%1350;
    if(!active[cell]) {active[cell]=true;++total;}
  }
  need(required==total,"QM87 required cells");auto body=block.sub(12,length);
  if(method==6) {need(previous&&length==0,"QM87 missing inherited map");return *previous;}
  unsigned count=method>=3?required:1350;std::vector<unsigned> values;
  if(method==1||method==3) {
    need(count>0&&length==1&&body[0]<=2,"QM87 uniform");values.assign(count,body[0]);
  } else if(method==2||method==5) {
    for(size_t i=0;i<body.n;++i) {
      unsigned value=body[i]>>6,n=(body[i]&63)+1;
      need(value<=2&&values.size()+n<=count,"QM87 run code/overrun");values.insert(values.end(),n,value);
    }
    need(values.size()==count,"QM87 run underrun");
  } else {
    need(length==(count+3)/4,"QM87 packed length");
    for(unsigned i=0;i<length*4;++i) {
      unsigned value=(body[i/4]>>(6-2*(i%4)))&3;
      if(i<count) {need(value<=2,"QM87 quantizer code");values.push_back(value);}
      else need(value==0,"QM87 packed padding");
    }
  }
  std::array<unsigned,1350> result{};unsigned at=0;
  for(unsigned i=0;i<1350;++i) if(method<3||active[i]) result[i]=values[at++];
  need(at==count,"QM87 scale coverage");return result;
}
static Bytes message(char kind) {
  const uint8_t domain[]={'C','U','6','6','V','8','2','C','2',0};
  Bytes out(domain,domain+10);out.push_back(uint8_t(kind));out.push_back(0);return out;
}
static Digest content_root(const std::array<Bytes,3> &planes) {
  std::vector<Digest> nodes(1024);auto ctx=context();unsigned leaf=0;
  for(unsigned axis=0;axis<3;++axis) {
    unsigned width=axis?360:720,total=axis?1350:5400;
    for(unsigned start=0;start<total;start+=16) {
      unsigned count=std::min(16u,total-start);auto msg=message('L');append(msg,ctx);
      be(msg,axis,1);be(msg,start,4);be(msg,count,2);
      for(unsigned tile=start;tile<start+count;++tile) {
        unsigned by=tile/(width/8),bx=tile%(width/8);
        for(unsigned y=0;y<8;++y) for(unsigned x=0;x<8;++x)
          msg.push_back(planes[axis][(by*8+y)*width+bx*8+x]);
      }
      nodes[512+leaf++]=sha256(msg);
    }
  }
  need(leaf==508,"C2 leaf count");
  for(;leaf<512;++leaf) {auto msg=message('E');append(msg,ctx);be(msg,leaf,4);be(msg,512,4);nodes[512+leaf]=sha256(msg);}
  unsigned level=1;
  for(unsigned width=256;width;width/=2,++level) for(unsigned i=0;i<width;++i) {
    auto msg=message('N');be(msg,level,2);be(msg,i,4);append(msg,nodes[2*(width+i)]);append(msg,nodes[2*(width+i)+1]);nodes[width+i]=sha256(msg);
  }
  return nodes[1];
}
static Digest content_seal(uint32_t fid,uint32_t refid,uint64_t generation,bool key,
                           Digest previous,Digest hud,Digest root) {
  auto msg=message('S');append(msg,context());be(msg,fid,4);be(msg,refid,4);be(msg,key,1);be(msg,generation,8);
  append(msg,previous);append(msg,hud);append(msg,root);need(msg.size()==157,"C2 seal shape");return sha256(msg);
}
struct Result {
  std::shared_ptr<Frame> frame;
  uint64_t generation=0;
  Digest root{},seal{},coefficient_sha{},canonical_sha{},hud_sha{},display_sha{},packet_sha{};
  std::array<unsigned,1350> scales{};
  size_t wire_bytes=0;
};
class Receiver {
  std::shared_ptr<const Result> accepted_;
public:
  std::shared_ptr<const Result> state() const { return accepted_; }
  void reset() { accepted_.reset(); }
  std::shared_ptr<const Result> receive(const Bytes &packet) {
    need(packet.size()>=132&&packet.size()<=MAX_WIRE,"CS88 research packet bound");
    BE trailer(View(packet).sub(packet.size()-4,4));need(crc32(View(packet).sub(0,packet.size()-4))==trailer.u32(),"CS88 outer CRC");
    auto packet_sha=sha256(packet);
    if(accepted_&&packet_sha==accepted_->packet_sha) return accepted_;
    BE header(View(packet).sub(0,128));need(header.magic()=="CS88"&&header.byte()==1,"CS88 explicit profile/version");
    unsigned flags=header.byte();need(flags<=1&&header.byte()==16,"CS88 flags/group");bool key=flags;
    unsigned map_method=header.byte();need(map_method<=3,"CS88 mode method");
    uint32_t fid=header.u32(),refid=header.u32();uint64_t generation=header.u64();
    need(fid!=0xffffffffu&&generation>0,"CS88 identities");
    need(header.u16()==720&&header.u16()==480,"CS88 geometry");unsigned bs=header.u16();
    need((bs==16||bs==32)&&header.u16()==0,"CS88 block geometry/reserved");
    unsigned cap=header.u32(),map_bytes=header.u32(),q_bytes=header.u32(),hud_bytes=header.u32(),data_bytes=header.u32();
    need(cap==256||cap==65536,"CS88 chunk profile");
    need(map_bytes<=976&&q_bytes>=16&&q_bytes<=354&&hud_bytes>=110&&hud_bytes<=49152,"CS88 component bounds");
    need(uint64_t(128)+map_bytes+q_bytes+hud_bytes+data_bytes+4==packet.size(),"CS88 exact body length");
    auto expected_root=header.digest(),expected_seal=header.digest();
    for(unsigned i=0;i<12;++i)need(header.byte()==0,"CS88 reserved padding");
    header.end();
    if(accepted_)need(fid>accepted_->frame->id&&generation>accepted_->generation,"CS88 stale identity/generation");
    if(key)need(refid==0xffffffffu,"CS88 key reference");
    else need(accepted_&&refid==accepted_->frame->id,"CS88 accepted reference binding");
    auto prev=key?Digest{}:accepted_->root;
    BE body(View(packet).sub(128,packet.size()-132));auto operations=modes(body.take(map_bytes),key,map_method);auto qmap=body.take(q_bytes);
    auto scales=quantizers(qmap,operations,(!key&&accepted_)?&accepted_->scales:nullptr);
    BE residual(body.take(data_bytes));auto candidate=std::make_shared<Result>();candidate->frame=std::make_shared<Frame>();
    auto &frame=*candidate->frame;frame.id=fid;frame.reference_id=refid;frame.key=key;
    SHA256 coefficient_hash;unsigned global=0;
    for(unsigned axis=0;axis<3;++axis) {
      unsigned total=axis?1350:5400,width=axis?360:720,bw=width/8,needed=0;
      for(unsigned tile=0;tile<total;++tile) needed+=operations[global+tile]==2;
      unsigned chunks=residual.u32();need(chunks==(needed+cap-1)/cap,"CS88 chunk count");
      std::vector<int16_t> coefficients;coefficients.reserve(size_t(needed)*64);
      for(unsigned chunk=0;chunk<chunks;++chunk) {
        unsigned count=residual.u32(),length=residual.u32();
        need(count==std::min(cap,needed-chunk*cap)&&count>0&&length>=46&&length<=46+128*count,"CS88 chunk lengths");
        auto chunk_view=residual.take(length);
        bool plain=chunk_view.n>=4&&chunk_view[0]=='B'&&chunk_view[1]=='R'&&chunk_view[2]=='8'&&chunk_view[3]=='8';
        auto decoded=plain?cu88::decode_br88(chunk_view,count,1):decode_ab38(chunk_view,count,1);
        coefficients.insert(coefficients.end(),decoded.begin(),decoded.end());
      }
      frame.planes[axis].resize(size_t(width)*(axis?240:480));size_t cursor=0;
      for(unsigned tile=0;tile<total;++tile,++global) {
        unsigned mode=operations[global],by=tile/bw,bx=tile%bw;std::array<int16_t,64> c{};
        if(mode==2) {std::copy(coefficients.begin()+cursor,coefficients.begin()+cursor+64,c.begin());cursor+=64;}
        Bytes coefficient_bytes;coefficient_bytes.reserve(128);for(auto value:c) put16(coefficient_bytes,uint16_t(value));coefficient_hash.update(coefficient_bytes);
        if(mode!=2) {
          need(mode==1||(!key&&accepted_&&mode==0),"CS88 COPY/CONST state");
          for(unsigned y=0;y<8;++y) for(unsigned x=0;x<8;++x) {
            auto at=(by*8+y)*width+bx*8+x;
            frame.planes[axis][at]=mode==1?128:accepted_->frame->planes[axis][at];
          }
          continue;
        }
        unsigned scale=scales[(axis?by:by/2)*45+(axis?bx:bx/2)];const auto &table=QTABLES[axis?1:0][scale];
        int64_t a[8][8],mid[8][8];
        for(unsigned y=0;y<8;++y) for(unsigned x=0;x<8;++x) a[y][x]=int64_t(c[y*8+x])*table[y][x];
        for(unsigned y=0;y<8;++y) for(unsigned x=0;x<8;++x) {
          int64_t sum=0;for(unsigned k=0;k<8;++k) sum+=a[y][k]*DCT[k][x];mid[y][x]=floor_shift(sum+8192,14);
        }
        for(unsigned y=0;y<8;++y) for(unsigned x=0;x<8;++x) {
          int64_t sum=0;for(unsigned k=0;k<8;++k) sum+=DCT[k][y]*mid[k][x];auto at=(by*8+y)*width+bx*8+x;
          int prediction=key?128:accepted_->frame->planes[axis][at];
          frame.planes[axis][at]=uint8_t(std::max<int64_t>(0,std::min<int64_t>(255,floor_shift(sum+8192,14)+prediction)));
        }
      }
      need(cursor==coefficients.size(),"CS88 coefficient coverage");
    }
    residual.end();need(global==8100,"CS88 tile coverage");
    auto hud=body.take(hud_bytes);body.end();frame.hud=decode_hud(hud,key?nullptr:&accepted_->frame->hud,fid,refid);
    Bytes semantic_hud;for(const auto &patch:frame.hud) {auto raw=word_bytes(patch.words);append(semantic_hud,raw);}
    candidate->hud_sha=sha256(semantic_hud);
    candidate->root=content_root(frame.planes);need(candidate->root==expected_root,"CS88 reconstructed content root");
    candidate->seal=content_seal(fid,refid,generation,key,prev,candidate->hud_sha,candidate->root);
    need(candidate->seal==expected_seal,"CS88 reconstructed frame seal");
    SHA256 canonical;for(const auto &p:frame.planes) canonical.update(p);candidate->canonical_sha=canonical.finish();
    candidate->coefficient_sha=coefficient_hash.finish();frame.canonical_tag=canonical_tag(frame.planes);
    frame.display=render(frame.planes,frame.hud);candidate->display_sha=sha256(word_bytes(frame.display));
    candidate->scales=scales;candidate->generation=generation;candidate->wire_bytes=packet.size();candidate->packet_sha=packet_sha;accepted_=candidate;return accepted_;
  }
};
static bool read32(std::istream &in,uint32_t &out) {
  char raw[4];in.read(raw,4);if(in.gcount()==0) return false;need(in.gcount()==4,"transport length truncation");
  out=0;for(auto b:raw) out=(out<<8)|uint8_t(b);return true;
}
int main() {try {
  Receiver receiver;uint32_t cohort=0,last=0xffffffffu,length=0;
  while(read32(std::cin,cohort)) {
    need(cohort<4&&read32(std::cin,length)&&length<=MAX_WIRE,"transport framing");
    Bytes packet(length);std::cin.read(reinterpret_cast<char*>(packet.data()),length);need(size_t(std::cin.gcount())==length,"transport packet truncation");
    if(cohort!=last) {receiver.reset();last=cohort;}
    auto prior=receiver.state();
    try {
      auto result=receiver.receive(packet);
      std::cout<<"{\"accepted\":true,\"replayed\":"<<(prior==result?"true":"false")<<",\"fid\":"<<result->frame->id<<",\"generation\":"<<result->generation
               <<",\"canonical_sha256\":\""<<hex(result->canonical_sha)<<"\",\"hud_sha256\":\""<<hex(result->hud_sha)
               <<"\",\"display_sha256\":\""<<hex(result->display_sha)<<"\",\"coefficient_sha256\":\""<<hex(result->coefficient_sha)
               <<"\",\"root\":\""<<hex(result->root)<<"\",\"seal\":\""<<hex(result->seal)<<"\",\"wire_bytes\":"<<result->wire_bytes<<"}"<<std::endl;
    } catch(const std::exception &error) {
      need(receiver.state()==prior,"CS88 rejected state changed");
      // Receiver errors are fixed local diagnostic strings, never packet text.
      std::cout<<"{\"accepted\":false,\"error\":\""<<error.what()<<"\",\"retained_fid\":"
               <<(prior?std::to_string(prior->frame->id):"null")<<"}"<<std::endl;
    }
  }
  return 0;
} catch(const std::exception &error) {std::cerr<<"CS88_FATAL "<<error.what()<<std::endl;return 1;}}
