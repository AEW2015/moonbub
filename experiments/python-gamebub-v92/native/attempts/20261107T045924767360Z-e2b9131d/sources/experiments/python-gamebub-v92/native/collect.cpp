#include "codec.hpp"
#include <chrono>
#include <iostream>
using namespace cu66;
using Clock=std::chrono::steady_clock;
static bool read32(uint32_t &value) {
  char bytes[4];std::cin.read(bytes,4);if(std::cin.gcount()==0)return false;
  need(std::cin.gcount()==4,"EC92 helper framing");value=0;
  for(unsigned i=0;i<4;++i)value|=uint32_t(uint8_t(bytes[i]))<<(8*i);
  return true;
}
static void write32(uint32_t value) {for(unsigned i=0;i<4;++i)std::cout.put(char(value>>(8*i)));}
template<class T> static void array_json(const T &values) {
  std::cout<<'[';for(size_t i=0;i<values.size();++i) {if(i)std::cout<<',';std::cout<<values[i];}std::cout<<']';
}
static uint64_t elapsed(Clock::time_point start) {return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count());}
int main() {try {
  uint32_t blocks,length;
  while(read32(blocks)) {
    need(read32(length)&&blocks>=1&&blocks<=5400&&length>=46&&length<=46+128*blocks,"EC92 helper bounds");
    Bytes source(length);std::cin.read(reinterpret_cast<char*>(source.data()),length);need(size_t(std::cin.gcount())==length,"EC92 helper truncation");
    auto start=Clock::now();auto values=decode_ab38(source,blocks,1);uint64_t source_decode=elapsed(start);
    start=Clock::now();auto prepared=cu92::prepare(values);uint64_t preparation=elapsed(start);
    need(prepared.ab.packet==source,"EC92 exact frozen AB re-encoding");need(cu88::decode_br88(prepared.br.packet,blocks,1)==values,"EC92 frozen BR decode parity");
    std::array<Bytes,16> candidates;std::array<std::string,16> candidate_hashes;std::array<cu92::DecodeStats,16> decoded_stats;
    start=Clock::now();for(unsigned mask=0;mask<16;++mask)candidates[mask]=cu92::assemble(prepared,mask);uint64_t assembly=elapsed(start);
    start=Clock::now();for(unsigned mask=0;mask<16;++mask)candidate_hashes[mask]=hex(sha256(candidates[mask]));uint64_t hashing=elapsed(start);
    start=Clock::now();for(unsigned mask=0;mask<16;++mask) {
      need(cu92::decode_ec92(candidates[mask],blocks,1,&decoded_stats[mask])==values,"EC92 native mixed coefficient parity");
      if(!candidates[mask][5])for(unsigned context=0;context<4;++context) {
        need(decoded_stats[mask].ab_decisions[context]==((mask>>context)&1?0:prepared.ab.decisions[context]),"EC92 AB decision count parity");
        need(decoded_stats[mask].ab_renorm[context]==((mask>>context)&1?0:prepared.ab.renorm[context]),"EC92 AB renorm count parity");
        need(decoded_stats[mask].br_bits[context]==((mask>>context)&1?prepared.br.bits[context]:0),"EC92 BR bit count parity");
      }
    }
    uint64_t validation=elapsed(start);Bytes coefficients;for(auto value:values)cu85::put16(coefficients,uint16_t(value));
    std::array<size_t,4> ab_lengths{},br_lengths{};for(unsigned context=0;context<4;++context) {ab_lengths[context]=prepared.ab_streams[context].size();br_lengths[context]=prepared.br_streams[context].size();}
    std::cout<<"{\"blocks\":"<<blocks<<",\"old_bytes\":"<<source.size()<<",\"coefficient_sha256\":\""<<hex(sha256(coefficients))<<"\",\"source_raw_fallback\":"<<(prepared.source_raw_fallback?"true":"false")<<",\"source_decode_ns\":"<<source_decode<<",\"prepare_ns\":"<<preparation<<",\"assemble_ns\":"<<assembly<<",\"hash_ns\":"<<hashing<<",\"generation_ns\":"<<(source_decode+preparation+assembly+hashing)<<",\"validate_ns\":"<<validation;
    std::cout<<",\"ab_decisions\":";array_json(prepared.ab.decisions);std::cout<<",\"ab_renorm\":";array_json(prepared.ab.renorm);std::cout<<",\"br_bits\":";array_json(prepared.br.bits);
    std::cout<<",\"ab_stream_bytes\":";array_json(ab_lengths);std::cout<<",\"br_stream_bytes\":";array_json(br_lengths);std::cout<<",\"masks\":[";
    for(unsigned mask=0;mask<16;++mask) {
      const auto &candidate=candidates[mask];const auto &stats=decoded_stats[mask];if(mask)std::cout<<',';
      std::cout<<"{\"requested_mask\":"<<mask<<",\"wire_mask\":"<<unsigned(candidate[6])<<",\"raw\":"<<(candidate[5]?"true":"false")<<",\"bytes\":"<<candidate.size()<<",\"sha256\":\""<<candidate_hashes[mask]<<"\",\"ab_decisions\":";
      array_json(stats.ab_decisions);std::cout<<",\"ab_renorm\":";array_json(stats.ab_renorm);std::cout<<",\"br_bits\":";array_json(stats.br_bits);std::cout<<'}';
    }
    std::cout<<"]}"<<std::endl;
    for(const auto &candidate:candidates) {write32(uint32_t(candidate.size()));std::cout.write(reinterpret_cast<const char*>(candidate.data()),std::streamsize(candidate.size()));}
    std::cout.flush();
  }
  return 0;
} catch(const std::exception &error) {std::cerr<<"EC92_HELPER_FAIL "<<error.what()<<std::endl;return 1;}}
