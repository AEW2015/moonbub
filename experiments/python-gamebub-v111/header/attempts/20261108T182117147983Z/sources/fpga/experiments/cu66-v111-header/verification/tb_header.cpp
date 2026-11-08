#include "inherited_fetch.cpp"
#include <limits>
static void put32(std::vector<uint8_t>&p,unsigned a,uint32_t x){for(unsigned i=0;i<4;++i)p.at(a+i)=uint8_t(x>>(8*i));}
static uint32_t checksum(const std::vector<uint8_t>&p){uint32_t c=0xffffffffU;for(unsigned i=0;i<p.size()-4;++i){c^=p[i];for(unsigned b=0;b<8;++b)c=(c>>1)^((c&1)?0xedb88320U:0);}return c^0xffffffffU;}
static void seal(std::vector<uint8_t>&p){put32(p,unsigned(p.size()-4),checksum(p));}
struct Header:Whole{
 uint64_t synthetic=0,real_headers=0,partial_writes=0,priority_conflicts=0,extra_cancels=0,header_cancels=0;
 explicit Header(unsigned s):Whole(s){}
 void inspect_header(const std::vector<uint8_t>&p,uint32_t size,unsigned blocks,bool crcgood){
  const uint64_t sum=uint64_t(little(p,14))+little(p,18)+little(p,22)+little(p,26),target=(uint64_t(size)-(uint64_t)46)&0x3ffffffffULL;
  const bool basic=little(p,0)==0x38385242U&&p[4]==1&&p[5]<=1&&little(p,6)==blocks&&(unsigned(p[10])|(unsigned(p[11])<<8))==1&&(unsigned(p[12])|(unsigned(p[13])<<8))==0;
  const bool write=crcgood&&basic&&sum==target;
  const bool rawbad=p[5]==1&&(little(p,14)!=uint32_t(blocks*128U)||little(p,18)||little(p,22)||little(p,26)||little(p,30)||little(p,34)||little(p,38));
  const unsigned expected=!crcgood?3:!basic||sum!=target?4:rawbad?4:0;
  need(d.debug_state==2&&!d.meta_valid,"original HEADER consumer before edge");tick();need(d.error==expected,"independent HEADER CRC/basic/sum/raw error priority");
  need(d.meta_count1==(write?little(p,30):0U)&&d.meta_count2==(write?little(p,34):0U)&&d.meta_count3==(write?little(p,38):0U)&&bool(d.meta_raw)==(write&&p[5]==1),"invalid-cycle raw/count metadata partial-write priority");
  auto&r=*d.rootp;for(unsigned j=0;j<4;++j){need(OLD(lengths[j])==NEW(lengths[j]),"stored length equality on header result");need(NEW(lengths[j])==(write?little(p,14+j*4):0U),"stored length original write priority");}
  need(d.debug_state==(expected?8U:p[5]==1?9U:3U),"original HEADER transition edge");
  if(write&&expected)++partial_writes;if(!crcgood&&(!basic||sum!=target||rawbad))++priority_conflicts;
 }
 void direct(std::vector<uint8_t>p,uint32_t size,unsigned blocks,bool crcgood){
  clean();d.start=d.abort_packet=d.reset=d.in_valid=0;d.meta_ready=d.out_ready=d.band_end_ready=0;auto&r=*d.rootp;
  BOTH(state,0U);BOTH(context_active,0U);BOTH(size_bytes,size);BOTH(context_blocks,blocks);BOTH(received,0U);BOTH(ram_valid,0U);BOTH(crc,(little(p,42)^0xffffffffU)^(crcgood?0U:1U));
  for(unsigned i=0;i<46;++i)BOTH(fetch_bytes[i],p[i]);
  // Three real preceding stable edges model completed owned header preparation;
  // no candidate payload/predicate is injected and no expected value is read from it.
  for(unsigned e=0;e<3;++e)tick();BOTH(state,2U);d.eval();check();inspect_header(p,size,blocks,crcgood);++synthetic;
 }
 void packet_header(std::vector<uint8_t>p,bool crcgood,unsigned cancel=0){
  clean();d.start=1;d.packet_bytes=p.size();d.blocks=1;d.epoch=0x51000000U+unsigned(real_headers);d.word16=d.serial_mode=0;d.in_valid=0;d.meta_ready=d.out_ready=d.band_end_ready=0;tick();d.start=0;
  for(unsigned i=0;i<p.size();++i){d.in_valid=1;d.in_data=p[i];d.in_last=i+1==p.size();d.eval();need(d.in_ready,"header real packet receive");tick();}d.in_valid=0;d.in_last=0;
  for(unsigned n=0;d.debug_state!=2;++n){need(n<256&&!d.error,"real header fetch bounded");tick();}
  if(cancel){if(cancel==1)d.abort_packet=1;else if(cancel==2)d.reset=1;else{d.start=1;d.packet_bytes=p.size();d.blocks=1;d.epoch+=1;}d.eval();need(!d.meta_valid&&!d.stage_read_req&&!d.stage_read_rsp,"HEADER current-edge cancel fences");tick();d.start=d.reset=d.abort_packet=0;need(d.debug_state==(cancel==3?1U:0U)&&!d.error&&!d.meta_valid,"HEADER cancel/start priority");++header_cancels;return;}
  inspect_header(p,unsigned(p.size()),1,crcgood);++real_headers;
 }
 void suite(const PacketCase&good){
  for(unsigned idx:{21U,29U,30U,31U,45U})for(unsigned a=0;a<6;++a){need(!run(good,1,0,int(idx),a),"header preparation cancel target reached");++extra_cancels;run(good,1);}
  auto raw=Bench::packet();
  for(unsigned cancel=1;cancel<=3;++cancel){packet_header(raw,true,cancel);run(good,1);}
  packet_header(raw,true);
  for(unsigned which=0;which<8;++which){auto p=raw;
   if(which==0)p[0]^=1;
   if(which==1)put32(p,14,127);
   if(which==2){put32(p,14,127);put32(p,18,1);}
   if(which==3)put32(p,30,1);
   if(which==4)p[5]=2;
   if(which==5){p[0]^=1;put32(p,14,127);}
   if(which==6){put32(p,14,127);put32(p,18,1);put32(p,30,0x80000001U);}
   if(which==7)put32(p,6,2);
   seal(p);packet_header(p,true);p.back()^=1;packet_header(p,false);
  }
  const std::array<uint32_t,15>v={0,1,2,42,45,46,127,128,0x3fffffffU,0x40000000U,0x7fffffffU,0x80000000U,0xffffffd1U,0xfffffffeU,0xffffffffU};
  for(unsigned i=0;i<v.size();++i)for(unsigned j=0;j<v.size();++j)for(unsigned k=0;k<4;++k){auto p=raw;p[5]=uint8_t(k&1);put32(p,14,v[i]);put32(p,18,v[j]);put32(p,22,k>=2?0xffffffffU:0U);put32(p,26,k==3?0xffffffffU:0U);put32(p,30,rng());put32(p,34,rng());put32(p,38,rng());
   uint32_t size=k==0?uint32_t(uint64_t(v[i])+v[j]+46):v[(i+j)%v.size()];direct(p,size,1,true);direct(p,size,1,false);
  }
  for(unsigned i=0;i<4096;++i){auto p=raw;p[5]=uint8_t(rng()&1);for(unsigned at:{14U,18U,22U,26U,30U,34U,38U})put32(p,at,rng());const uint64_t sum=uint64_t(little(p,14))+little(p,18)+little(p,22)+little(p,26);uint32_t size=i%2?uint32_t(sum+46):rng();if(i%13==0)p[0]^=1;direct(p,size,1,i%7!=0);}
  need(partial_writes>0&&priority_conflicts>0&&extra_cancels==30&&header_cancels==3,"header extension complete coverage");
 }
};
int main(int argc,char**argv){if(argc!=2)return inherited_fetch_main(argc,argv);try{unsigned seed=std::stoul(argv[1]);Header h(seed);PacketCase good;good.id="independent-generated-raw";good.blocks=1;good.packet=Bench::packet();good.dense.resize(128);h.suite(good);std::cout<<"{\"type\":\"header_pipeline_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"synthetic_header_rows\":"<<h.synthetic<<",\"real_header_cases\":"<<h.real_headers<<",\"partial_metadata_failures\":"<<h.partial_writes<<",\"priority_conflicts\":"<<h.priority_conflicts<<",\"extra_boundary_cancels\":"<<h.extra_cancels<<",\"HEADER_cancels\":"<<h.header_cancels<<",\"edges\":"<<h.edges<<"}\n";return 0;}catch(const std::exception&e){std::cerr<<"HEADER_FOCUS_FAIL "<<e.what()<<'\n';return 1;}}
