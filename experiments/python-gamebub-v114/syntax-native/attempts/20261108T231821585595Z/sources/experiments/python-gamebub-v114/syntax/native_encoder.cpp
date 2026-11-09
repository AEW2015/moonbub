// Isolated native SR14 packetizer experiment; not a Sunshine capture hook.
// Keep the independently qualified native reader unchanged in this translation unit.
#define main sr14_reader_control_main
#include "native.cpp"
#undef main
static void put_be(Bytes &out,uint32_t value,unsigned width){for(int i=int(width)-1;i>=0;--i)out.push_back(uint8_t(value>>(8*i)));}
static Bytes packetize(View data){
  need(data.n>=132&&(data.n-4)%128==0,"SR14 encoder geometry");
  unsigned version=data[0],plane=data[1],quantum=be(data,2,2),blocks=unsigned((data.n-4)/128);
  need((version==1||version==2)&&plane<=2&&blocks<=5400&&
       (quantum==32||quantum==64||quantum==128||quantum==256),"SR14 encoder profile");
  Reader raw(data.sub(4,data.n-4));std::vector<int16_t> coefficients(size_t(blocks)*64);
  for(auto &value:coefficients){value=int16_t(signed16(raw.u16()));}
  raw.end();
  std::vector<Bytes> pieces;std::vector<unsigned> counts;
  for(unsigned first=0;first<blocks;first+=quantum){unsigned n=std::min(quantum,blocks-first);
    std::vector<int16_t>a(coefficients.begin()+size_t(first)*64,coefficients.begin()+size_t(first+n)*64);
    pieces.push_back(cu88::encode_br88(a).packet);counts.push_back(n);
  }
  need(pieces.size()<=512,"SR14 encoder descriptors");
  Bytes out{'S','R','1','4',uint8_t(version),uint8_t(plane)};put_be(out,uint32_t(pieces.size()),2);put_be(out,blocks,4);
  uint32_t first=0,offset=12+unsigned(pieces.size())*(version==1?16:6);
  for(size_t i=0;i<pieces.size();++i){const auto &packet=pieces[i];unsigned length=unsigned(packet.size())-(version==1?0:30);
    if(version==1){put_be(out,first,4);put_be(out,counts[i],4);put_be(out,offset,4);put_be(out,length,4);}
    else {need(length<=65535,"SR14 compact length");put_be(out,counts[i],2);out.push_back(packet[5]);out.push_back(0);put_be(out,length,2);}
    first+=counts[i];offset+=length;
  }
  for(const auto &packet:pieces)out.insert(out.end(),packet.begin()+(version==1?0:30),packet.end());
  put_be(out,crc32(out),4);return out;
}
int main(){while(true){int op=std::cin.get();if(op==EOF)return 0;try{uint32_t n=0;need(take32(n)&&n<=1048576,"request length");Bytes data(n);
    std::cin.read(reinterpret_cast<char*>(data.data()),n);need(size_t(std::cin.gcount())==n,"request body");Bytes out;
    if(op=='P')out=packetize(data);
    else if(op=='D')out=decode(data);
    else {need(op=='E'&&n&&n%128==0,"operation/dense geometry");Reader r(data);std::vector<int16_t>a(n/2);for(auto &value:a)value=int16_t(signed16(r.u16()));out=cu88::encode_br88(a).packet;need(cu88::decode_br88(out,n/128,1)==a,"native self parity");}
    answer(1,out);
  }catch(const std::exception &error){std::string s=error.what();answer(0,Bytes(s.begin(),s.end()));}}
}
