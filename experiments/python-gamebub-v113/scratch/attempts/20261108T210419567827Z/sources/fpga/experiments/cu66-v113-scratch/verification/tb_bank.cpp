// Additive boundary cases. The complete inherited bench remains byte-identical
// and executes first, including every original oracle and its PASS gates.
#define main inherited_scratch_main
#include "tb_scratch.cpp"
#undef main
int main(int argc,char**argv){try{
 need(inherited_scratch_main(argc,argv)==0,"unchanged full scratch/hazard suite");
 const unsigned seed=unsigned(std::stoul(argv[1]));
 std::ofstream trace(std::string(argv[2])+"-boundary.jsonl");need(bool(trace),"boundary trace open");
 unsigned boundary_transactions=0;uint64_t noise_edges=0;
 for(unsigned blocks:{9U,17U})for(unsigned raw=0;raw<2;++raw)for(unsigned profile=0;profile<16;++profile){
  if(raw&&(profile&8))continue;
  auto p=packet(blocks,raw!=0,seed+profile);ProbeBench b(seed+boundary_transactions+900,trace);b.ingest(p,profile);
  for(unsigned n=0;!b.d.done&&!b.d.error;++n){
   need(n<100000,"boundary completion watchdog");b.d.dense_ready=b.rng()%4!=0;
   // Inputs have no owner without begin_valid. Existing dense/memory/position
   // checks remain active while all allocation sidebands change every cycle.
   b.d.begin_blocks=b.rng()&0x1ffffU;b.d.begin_raw=b.rng()&1U;
   b.d.begin_count1=b.rng();b.d.begin_count2=b.rng();b.d.begin_count3=b.rng();b.d.begin_epoch=b.rng();
   b.tick();++noise_edges;
  }
  need(b.d.done&&!b.d.error&&!b.pending,"DC line boundary transaction failed/drained");
  need(b.outputs==p.blocks*64,"DC line boundary dense output count");++boundary_transactions;
 }
 need(boundary_transactions==48&&noise_edges>10000,"DC line crossing and live sideband noise coverage");
 std::cout<<"{\"type\":\"bank_complete_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed
 <<",\"full_transactions\":72,\"corrupt_response_cases\":128,\"read_owner_cases\":4,\"bank_mask\":"<<totals.bankmask
 <<",\"offset_mask\":"<<totals.offsetmask<<",\"dc_line_boundary_transactions\":"<<boundary_transactions
 <<",\"begin_input_noise_edges\":"<<noise_edges<<",\"total_clock_edges\":"<<totals.edges<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"BANK_BOUNDARY_FAIL "<<e.what()<<'\n';return 1;}}
