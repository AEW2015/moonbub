from pathlib import Path
R=Path(__file__).resolve().parents[3];V=R/'fpga/experiments/cu66-v113-geometry/verification'
p=V/'context_probe.sv';s=p.read_text().replace('    output logic mismatch,','    output logic [7:0] min_success_gap,min_level_gap,min_error_gap,\n    output logic [31:0] geometry_consumes,\n    output logic mismatch,')
s=s.replace('\nendmodule','''
    logic [7:0] response_age;
    always_ff @(posedge clk) begin
        if(reset || start || abort_context) begin
            response_age<=0;min_success_gap<=255;min_level_gap<=255;
            min_error_gap<=255;geometry_consumes<=0;
        end else begin
            if(candidate.req_valid && candidate.req_ready)response_age<=0;
            else if(response_age!=255)response_age<=response_age+1'b1;
            if(candidate.parser_valid && candidate.parser_ready) begin
                if(candidate.parser_error==0)begin
                    if(response_age+8'd1<min_success_gap)min_success_gap<=response_age+8'd1;
                    assert(response_age>=2)else $fatal(1,"successful Rice consumption before E+3");
                    if(candidate.state==6)begin
                        geometry_consumes<=geometry_consumes+1'b1;
                        if(response_age+8'd1<min_level_gap)min_level_gap<=response_age+8'd1;
                    end
                end else if(response_age+8'd1<min_error_gap)min_error_gap<=response_age+8'd1;
            end
        end
    end
endmodule''')
p.write_text(s)
p=V/'tb_count_domain.cpp';s=p.read_text();s=s.replace('int main(','''static void timing_edges(unsigned seed) {
 Sim s(seed);unsigned checks=0;
 for(bool serial:{false,true})for(bool word16:{false,true}) {
  Case c;c.id="earliest-zero-suffix";c.band=1;c.k1=0;pack(c,{true,true});c.expected={{0,1,-1}};
  s.run(c,word16,serial,false);
  require(s.d.min_success_gap==3 && s.d.min_level_gap==3 && s.d.geometry_consumes==1,"earliest successful Rice edge is E+3");++checks;
  c=Case{};c.id="zero-stream-truncation";c.error=2;s.run(c,word16,serial,false);
  require(s.d.min_error_gap==2,"zero stream error consumed at E+2");++checks;
 }
 std::cout<<"{\\"type\\":\\"edge_verdict\\",\\"status\\":\\"TEST_PASS\\",\\"checks\\":"<<checks<<",\\"minimum_success_request_response_gap\\":3,\\"zero_stream_error_gap\\":2}\\n";
}
int main(''').replace('domain_starts(unsigned(std::stoul(argv[2])));','timing_edges(unsigned(std::stoul(argv[2])));domain_starts(unsigned(std::stoul(argv[2])));');p.write_text(s)
p=V/'geometry_stage_probe.sv';s=p.read_text().replace('input logic [31:0] position,emitted,','input logic [31:0] position,input logic [15:0] emitted,');p.write_text(s)
