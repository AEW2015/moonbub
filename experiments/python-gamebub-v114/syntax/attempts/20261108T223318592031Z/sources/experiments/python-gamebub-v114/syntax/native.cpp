// Experimental SR14 independent parser + unchanged native BR88 codec.
#include "experiments/python-gamebub-v88/entropy/codec.hpp"
#include <iostream>
using namespace cu66;
static uint32_t be(View v,size_t at,unsigned n){need(at+n<=v.n,"SR14 field bounds");uint32_t x=0;for(unsigned i=0;i<n;++i)x=(x<<8)|v[at+i];return x;}
static Bytes decode(View v){
  need(v.n>=78&&v.n<=1048576,"SR14 bounds");
  need(std::string(reinterpret_cast<const char*>(v.p),4)=="SR14"&&v[4]==1&&v[5]<=2,"SR14 profile");
  need(crc32(v.sub(0,v.n-4))==be(v,v.n-4,4),"SR14 CRC");
  uint32_t count=be(v,6,2),blocks=be(v,8,4);
  need(count>=1&&count<=512&&blocks>=1&&blocks<=5400,"SR14 geometry");
  size_t at=12+16*size_t(count);need(at<=v.n-4,"SR14 table");uint32_t first=0;Bytes out;
  for(unsigned i=0;i<count;++i){size_t t=12+16*size_t(i);auto start=be(v,t,4),n=be(v,t+4,4),off=be(v,t+8,4),len=be(v,t+12,4);
    need(start==first&&n>=1&&n<=256&&n<=blocks-first&&off==at&&len>=46&&len<=46+128*n&&uint64_t(off)+len<=v.n-4,"SR14 range/owner");
    auto a=cu88::decode_br88(v.sub(off,len),n,1);for(auto x:a){out.push_back(uint8_t(x));out.push_back(uint8_t(uint16_t(x)>>8));}first+=n;at+=len;
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
