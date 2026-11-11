#pragma once
#include <array>
#include <cstdint>
#include <ostream>

// Simulation-only pre-edge accounting. No category assigns causal blame.
namespace v129_observe {
struct Pair { bool valid=false, ready=false; };
struct Sample {
  Pair coefficient, inverse, residual, canonical, hash, request, response;
  bool pending_ack=false;
};
struct Monitor {
  static constexpr unsigned channels=7, bits=7;
  // [channel][0=no valid, 1=valid&&!ready, 2=accepted]
  std::array<std::array<uint64_t,3>,channels> handshake{};
  std::array<uint64_t,1U<<bits> masks{};
  std::array<uint64_t,bits+1> priority{};
  uint64_t cycles=0;
  void sample(const Sample& s) {
    const std::array<Pair,channels> p{{s.coefficient,s.inverse,s.residual,s.canonical,s.hash,s.request,s.response}};
    unsigned mask=0;
    for(unsigned i=0;i<channels;++i) {
      ++handshake[i][!p[i].valid?0:!p[i].ready?1:2];
      // bit 6 is pending debt; a response hold remains visible separately
      // through response's handshake counters.
      if(i<6 && p[i].valid && !p[i].ready)mask|=1U<<i;
    }
    if(s.pending_ack)mask|=1U<<6;
    ++masks[mask];unsigned category=0;
    while(category<bits && !(mask&(1U<<category)))++category;
    ++priority[category];++cycles;
  }
  void report(std::ostream& o, unsigned seed, unsigned profile, uint64_t epoch)const {
    o<<"{\"type\":\"v129_latency_monitor\",\"simulation_only\":true,\"primary_is_priority_not_cause\":true,\"cycles\":"<<cycles
     <<",\"seed\":"<<seed<<",\"profile\":"<<profile<<",\"epoch\":"<<epoch
     <<",\"channels\":[\"coefficient\",\"inverse\",\"residual\",\"canonical\",\"hash_delivery\",\"physical_request\",\"physical_response\"],\"handshake_no_valid_stalled_accepted\":[";
    for(unsigned i=0;i<channels;++i){if(i)o<<',';o<<'['<<handshake[i][0]<<','<<handshake[i][1]<<','<<handshake[i][2]<<']';}
    o<<"],\"mask_bit_order\":[\"coefficient_stalled\",\"inverse_stalled\",\"residual_stalled\",\"canonical_stalled\",\"hash_delivery_stalled\",\"physical_request_stalled\",\"external_pending_ack\"],\"mask_counts\":[";
    for(unsigned i=0;i<masks.size();++i){if(i)o<<',';o<<masks[i];}o<<"],\"priority_counts\":[";
    for(unsigned i=0;i<priority.size();++i){if(i)o<<',';o<<priority[i];}o<<"]}\n";
  }
};
}
