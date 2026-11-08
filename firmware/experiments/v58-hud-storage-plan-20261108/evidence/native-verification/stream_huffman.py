from pathlib import Path
p=Path('C:/moon/dev/experiments/v58-hud-storage-plan-20261108/native/hud.hpp');s=p.read_text();a=s.index('inline cu66_port::Vector<uint8_t> huffman(');z=s.index('inline uint32_t plain_rice(',a)
s=s[:a]+r'''// Fixed canonical tables and borrowed bitstream only: no count-sized scratch.
struct HuffmanSymbols {
  unsigned count=0,consumed=0,constant=0;bool singleton=false;
  std::array<uint16_t,17> counts{};std::array<uint32_t,17> first_code{};
  std::array<uint16_t,17> first_symbol{};std::array<uint8_t,256> symbols{};
  Bits bits{View{},0};
  void init(Reader&r,unsigned wanted,unsigned maximum){
    need(wanted&&wanted<=21120&&maximum<=255,"HUD symbol count");
    count=wanted;consumed=0;singleton=false;counts.fill(0);first_code.fill(0);first_symbol.fill(0);symbols.fill(0);
    unsigned ns=r.u16(),nb=r.u32();need(ns&&ns<=std::min(count,maximum+1)&&nb<=16*count,"HUD Huffman bounds");
    std::array<uint8_t,256> lengths{};int last=-1;
    for(unsigned i=0;i<ns;++i){unsigned value=r.u8(),length=r.u8();need(value<=maximum&&int(value)>last&&length>=1&&length<=16,"HUD Huffman table");last=value;lengths[value]=uint8_t(length);++counts[length];}
    bits=Bits(r.take((nb+7)/8),nb);
    if(ns==1){need(lengths[unsigned(last)]==1&&nb==0,"HUD constant syntax");singleton=true;constant=unsigned(last);return;}
    unsigned code=0,offset=0;
    for(unsigned n=1;n<=16;++n){code=(code+counts[n-1])<<1;first_code[n]=code;first_symbol[n]=uint16_t(offset);need(code+counts[n]<=(1u<<n),"HUD oversubscribed Huffman");for(unsigned v=0;v<=maximum;++v)if(lengths[v]==n)symbols[offset++]=uint8_t(v);}
    need(code+counts[16]==(1u<<16)&&nb>=count,"HUD Huffman complete");
  }
  uint8_t next(){
    need(consumed<count,"HUD symbol count");if(singleton){++consumed;return uint8_t(constant);}
    unsigned code=0;for(unsigned n=1;n<=16;++n){code=code*2+bits.bit();const unsigned first=first_code[n];if(code>=first&&code-first<counts[n]){++consumed;return symbols[first_symbol[n]+code-first];}}
    need(false,"HUD unknown Huffman code");return 0;
  }
  void end(){need(consumed==count,"HUD symbol coverage");bits.end();}
};
template<class Emit>inline void huffman_emit(Reader&r,unsigned count,unsigned maximum,Emit emit){HuffmanSymbols symbols;symbols.init(r,count,maximum);for(unsigned i=0;i<count;++i)emit(symbols.next());symbols.end();}
inline cu66_port::Vector<uint8_t> huffman(Reader&r,unsigned count,unsigned maximum){cu66_port::Vector<uint8_t> out;out.reserve(count);huffman_emit(r,count,maximum,[&](uint8_t value){out.push_back(value);});return out;}
''' + s[z:]
s=s.replace('  cu66_port::Vector<uint8_t> symbols;\n  if(events){Reader h(r.take(size));symbols=huffman(h,events,maximum);h.end();}', '  HuffmanSymbols symbols;\n  if(events){Reader h(r.take(size));symbols.init(h,events,maximum);h.end();}')
s=s.replace('for(auto v:symbols)put(v);','for(unsigned i=0;i<events;++i)put(symbols.next());')
s=s.replace('for(auto v:symbols){need(v!=0,','for(unsigned i=0;i<events;++i){auto v=symbols.next();need(v!=0,')
s=s.replace('for(auto v:symbols){need(v!=last','for(unsigned i=0;i<events;++i){auto v=symbols.next();need(v!=last')
s=s.replace('  need(produced==count,"HS33 exact expansion");bits.end();','  need(produced==count,"HS33 exact expansion");if(events)symbols.end();bits.end();')
s=s.replace('      else{auto mapped=huffman(a,w*hh,(mode&8)?4*maximum:2*maximum);for(auto value:mapped)emit(value);}','      else huffman_emit(a,w*hh,(mode&8)?4*maximum:2*maximum,emit);')
p.write_text(s);print('V58_ALL_CHANNEL_SCRATCH_STREAMED')
