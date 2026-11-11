#include "monitor.hpp"
#include <cassert>
#include <numeric>
#include <sstream>
int main() {
  using namespace v129_observe;
  Monitor m; Sample s;
  m.sample(s); // idle / no observed blockage
  s.coefficient={true,false};s.inverse={true,false};s.pending_ack=true;
  m.sample(s); // preserve all three simultaneous observations
  s.coefficient={true,true};s.inverse={true,true};s.canonical={true,false};
  s.hash={true,true};s.request={true,false};s.response={true,false};m.sample(s);
  s.canonical={true,true};s.request={true,true};s.response={true,true};s.pending_ack=false;m.sample(s);
  assert(m.cycles==4 && m.masks[0]==2 && m.masks[67]==1 && m.masks[104]==1);
  assert(m.priority[0]==1 && m.priority[3]==1 && m.priority[7]==2);
  assert(m.handshake[0][0]==1 && m.handshake[0][1]==1 && m.handshake[0][2]==2);
  assert(m.handshake[6][0]==2 && m.handshake[6][1]==1 && m.handshake[6][2]==1);
  assert(std::accumulate(m.masks.begin(),m.masks.end(),uint64_t(0))==m.cycles);
  assert(std::accumulate(m.priority.begin(),m.priority.end(),uint64_t(0))==m.cycles);
  for(const auto& row:m.handshake)assert(std::accumulate(row.begin(),row.end(),uint64_t(0))==m.cycles);
  std::ostringstream o;m.report(o,17,1,4);assert(o.str().find("\"cycles\":4")!=std::string::npos);
}
