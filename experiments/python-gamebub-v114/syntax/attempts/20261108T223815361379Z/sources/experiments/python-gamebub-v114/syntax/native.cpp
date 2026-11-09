// Experimental SR14 independent parser + unchanged native BR88 codec.
#include "experiments/python-gamebub-v88/entropy/codec.hpp"
#include <iostream>
using namespace cu66;
static uint32_t be(View v,size_t at,unsigned n){need(at+n<=v.n,"SR14 field bounds");uint32_t x=0;for(unsigned i=0;i<n;++i)x=(x<<8)|v[at+i];return x;}
static Bytes decode(View v){
  need(v.n>=38&&v.n<=1048576,"SR14 bounds");
  need(std::string(reinterpret_cast<const char*>(v.p),4)=="SR14"&&(v[4]==1||v[4]==2)&&v[5]<=2,"SR14 profile");
  need(crc32(v.sub(0,v.n-4))==be(v,v.n-4,4),"SR14 CRC");
  uint32_t count=be(v,6,2),blocks=be(v,8,4);
  need(count>=1&&count<=512&&blocks>=1&&blocks<=5400,"SR14 geometry");
  const bool compact=v[4]==2;const size_t stride=compact?6:16;
  size_t at=12+stride*size_t(count);need(at<=v.n-4,"SR14 table");uint32_t first=0;Bytes out;
  for(unsigned i=0;i<count;++i){size_t t=12+stride*size_t(i);uint32_t start=first,n=0,off=uint32_t(at),len=0,flags=0;
    if(compact){n=be(v,t,2);flags=be(v,t+2,1);need(flags<=1&&be(v,t+3,1)==0,"SR14 compact flags");len=be(v,t+4,2);}
    else {start=be(v,t,4);n=be(v,t+4,4);off=be(v,t+8,4);len=be(v,t+12,4);}
    const unsigned saved=compact?30:0;
    need(start==first&&n>=1&&n<=256&&n<=blocks-first&&off==at&&len>=46-saved&&len<=46+128*n-saved&&uint64_t(off)+len<=v.n-4,"SR14 range/owner");
    auto payload=v.sub(off,len);Bytes restored;
    if(compact){std::array<uint32_t,4> lengths{};
      if(flags)lengths={128*n,0,0,0};
      else {size_t cursor=12;for(auto &length:lengths){need(cursor+6<=payload.n-4,"SR14 compact stream");auto bits=uint32_t(payload[cursor+2])|(uint32_t(payload[cursor+3])<<8)|(uint32_t(payload[cursor+4])<<16)|(uint32_t(payload[cursor+5])<<24);uint64_t size=6+(uint64_t(bits)+7)/8;need(size<=payload.n-4-cursor,"SR14 compact bit length");length=uint32_t(size);cursor+=size;}need(cursor==payload.n-4,"SR14 compact closure");}
      restored={'B','R','8','8',1,uint8_t(flags)};cu85::put32(restored,n);cu85::put16(restored,1);cu85::put16(restored,0);for(auto length:lengths)cu85::put32(restored,length);restored.insert(restored.end(),payload.p,payload.p+payload.n);payload=View(restored);
    }
    auto a=cu88::decode_br88(payload,n,1);for(auto x:a){out.push_back(uint8_t(x));out.push_back(uint8_t(uint16_t(x)>>8));}first+=n;at+=len;
  }
  need(first==blocks&&at==v.n-4,"SR14 closure");return out;
}
static bool take32(uint32_t &v){char b[4];std::cin.read(b,4);if(!std::cin.gcount())return false;need(std::cin.gcount()==4,"request header");v=0;for(unsigned i=0;i<4;++i)v|=uint32_t(uint8_t(b[i]))<<(8*i);return true;}
static void answer(unsigned ok,const Bytes &v){std::cout.put(char(ok));for(unsigned i=0;i<4;++i)std::cout.put(char(uint32_t(v.size())>>(8*i)));std::cout.write(reinterpret_cast<const char*>(v.data()),v.size());std::cout.flush();}
int main(){while(true){int op=std::cin.get();if(op==EOF)return 0;try{uint32_t n=0;need(take32(n)&&n<=1048576,"request length");Bytes data(n);std::cin.read(reinterpret_cast<char*>(data.data()),n);need(size_t(std::cin.gcount())==n,"request body");Bytes out;
    if(op=='E'){need(n&&n%128==0,"dense geometry");Reader r(data);std::vector<int16_t>a(n/2);for(auto &v:a)v=int16_t(signed16(r.u16()));out=cu88::encode_br88(a).packet;need(cu88::decode_br88(out,n/128,1)==a,"native self parity");}
    else {need(op=='D',"operation");out=decode(data);}answer(1,out);
  }catch(const std::exception &e){std::string s=e.what();answer(0,Bytes(s.begin(),s.end()));}}
}
