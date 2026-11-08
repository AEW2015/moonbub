// SHA-256 original-cycle successor: lookahead rolling schedule plus carry-save sums.
// Algorithm: NIST FIPS180-4; exactly64compression rounds, unchanged public FSM/counters.
// Private words are intentionally NOT reset; no initial-zero assumption is added.
// BUFFER_BLOCKS=1: input pauses during compression. =2: bounded ping-pong.
// This is an unkeyed content hash, not authentication or a bank controller.
module cu71_sha256_roundcsa_fanout_v003 #(
    parameter integer BUFFER_BLOCKS = 1
) (
    input logic clk, rst, abort_i,
    input logic start_valid,
    output logic start_ready,
    input logic [31:0] total_bytes,
    input logic data_valid,
    output logic data_ready,
    input logic [7:0] data,
    input logic data_last,
    output logic result_valid,
    input logic result_ready,
    output logic [255:0] digest,
    output logic busy, error, aborted,
    output logic [7:0] error_code,
    output logic [31:0] accepted_bytes,
    output logic [31:0] compressed_blocks,
    output logic [31:0] round_cycles,
    output logic [31:0] padding_bytes,
    output logic [31:0] input_stall_cycles,
    output logic [31:0] output_stall_cycles,
    output logic [2:0] debug_fill_state,
    output logic [1:0] debug_core_state
);
    typedef enum logic [2:0] {F_DATA,F_PAD_ONE,F_PAD_ZERO,F_LENGTH,F_DONE} fill_state_t;
    typedef enum logic [1:0] {C_IDLE,C_ROUND,C_ADD} core_state_t;
    fill_state_t fill_state;
    core_state_t core_state;
    logic active, result_pending;
    logic [31:0] message_bytes;
    logic [31:0] words [0:BUFFER_BLOCKS-1][0:15];
    logic [31:0] hash_state [0:7];
    logic [31:0] a,b,c,d,e,f,g,h;
    logic [BUFFER_BLOCKS-1:0] bank_full, bank_last;
    logic fill_bank, process_bank;
    logic [5:0] byte_position;
    (* MAX_FANOUT = 32 *) logic [5:0] round_index;
    logic [2:0] length_index;
    logic [63:0] bit_length;
    logic write_byte;
    logic [7:0] next_byte;
    logic accepting_data, bad_last;
    logic [31:0] schedule_word, future_word, round_e, round_a;
    logic [3:0] ring_index;
    integer i;
    function automatic [31:0] ror(input [31:0] x,input integer n);
        ror=(x>>n)|(x<<(32-n));
    endfunction
    function automatic [31:0] small0(input [31:0] x);small0=ror(x,7)^ror(x,18)^(x>>3);endfunction
    function automatic [31:0] small1(input [31:0] x);small1=ror(x,17)^ror(x,19)^(x>>10);endfunction
    function automatic [31:0] big0(input [31:0] x);big0=ror(x,2)^ror(x,13)^ror(x,22);endfunction
    function automatic [31:0] big1(input [31:0] x);big1=ror(x,6)^ror(x,11)^ror(x,25);endfunction
    function automatic [31:0] constant_k(input [5:0] t);
        case(t)
            6'd0:constant_k=32'h428a2f98;
            6'd1:constant_k=32'h71374491;
            6'd2:constant_k=32'hb5c0fbcf;
            6'd3:constant_k=32'he9b5dba5;
            6'd4:constant_k=32'h3956c25b;
            6'd5:constant_k=32'h59f111f1;
            6'd6:constant_k=32'h923f82a4;
            6'd7:constant_k=32'hab1c5ed5;
            6'd8:constant_k=32'hd807aa98;
            6'd9:constant_k=32'h12835b01;
            6'd10:constant_k=32'h243185be;
            6'd11:constant_k=32'h550c7dc3;
            6'd12:constant_k=32'h72be5d74;
            6'd13:constant_k=32'h80deb1fe;
            6'd14:constant_k=32'h9bdc06a7;
            6'd15:constant_k=32'hc19bf174;
            6'd16:constant_k=32'he49b69c1;
            6'd17:constant_k=32'hefbe4786;
            6'd18:constant_k=32'h0fc19dc6;
            6'd19:constant_k=32'h240ca1cc;
            6'd20:constant_k=32'h2de92c6f;
            6'd21:constant_k=32'h4a7484aa;
            6'd22:constant_k=32'h5cb0a9dc;
            6'd23:constant_k=32'h76f988da;
            6'd24:constant_k=32'h983e5152;
            6'd25:constant_k=32'ha831c66d;
            6'd26:constant_k=32'hb00327c8;
            6'd27:constant_k=32'hbf597fc7;
            6'd28:constant_k=32'hc6e00bf3;
            6'd29:constant_k=32'hd5a79147;
            6'd30:constant_k=32'h06ca6351;
            6'd31:constant_k=32'h14292967;
            6'd32:constant_k=32'h27b70a85;
            6'd33:constant_k=32'h2e1b2138;
            6'd34:constant_k=32'h4d2c6dfc;
            6'd35:constant_k=32'h53380d13;
            6'd36:constant_k=32'h650a7354;
            6'd37:constant_k=32'h766a0abb;
            6'd38:constant_k=32'h81c2c92e;
            6'd39:constant_k=32'h92722c85;
            6'd40:constant_k=32'ha2bfe8a1;
            6'd41:constant_k=32'ha81a664b;
            6'd42:constant_k=32'hc24b8b70;
            6'd43:constant_k=32'hc76c51a3;
            6'd44:constant_k=32'hd192e819;
            6'd45:constant_k=32'hd6990624;
            6'd46:constant_k=32'hf40e3585;
            6'd47:constant_k=32'h106aa070;
            6'd48:constant_k=32'h19a4c116;
            6'd49:constant_k=32'h1e376c08;
            6'd50:constant_k=32'h2748774c;
            6'd51:constant_k=32'h34b0bcb5;
            6'd52:constant_k=32'h391c0cb3;
            6'd53:constant_k=32'h4ed8aa4a;
            6'd54:constant_k=32'h5b9cca4f;
            6'd55:constant_k=32'h682e6ff3;
            6'd56:constant_k=32'h748f82ee;
            6'd57:constant_k=32'h78a5636f;
            6'd58:constant_k=32'h84c87814;
            6'd59:constant_k=32'h8cc70208;
            6'd60:constant_k=32'h90befffa;
            6'd61:constant_k=32'ha4506ceb;
            6'd62:constant_k=32'hbef9a3f7;
            6'd63:constant_k=32'hc67178f2;
            default:constant_k=0;
        endcase
    endfunction
    // Carry-save reduction keeps every operation explicitly modulo2^32.
    // Carries above bit31 are discarded exactly as in the original32-bit sums.
    function automatic logic [31:0] add4_mod(input logic [31:0] x,y,z,w);
        logic [31:0] s0,c0,s1,c1;
        begin
            s0=x^y^z;c0=((x&y)|(x&z)|(y&z))<<1;
            s1=s0^c0^w;c1=((s0&c0)|(s0&w)|(c0&w))<<1;
            add4_mod=s1+c1;
        end
    endfunction
    function automatic logic [31:0] add5_mod(input logic [31:0] x,y,z,w,v);
        logic [31:0] s0,c0,s1,c1,s2,c2;
        begin
            s0=x^y^z;c0=((x&y)|(x&z)|(y&z))<<1;
            s1=s0^c0^w;c1=((s0&c0)|(s0&w)|(c0&w))<<1;
            s2=s1^c1^v;c2=((s1&c1)|(s1&v)|(c1&v))<<1;
            add5_mod=s2+c2;
        end
    endfunction
    // Precompress fixed operands; schedule W enters only the final CSA.
    // Every vector and shifted carry is modulo2^32, including discarded MSB.
    function automatic logic [31:0] add6_wlast(input logic [31:0] op_h,op_s1,op_ch,op_k,op_d,op_w);
        logic [31:0] s0,c0,s1,c1,s2,c2,last_s,last_c;
        begin
            s0=op_h^op_s1^op_ch;c0=((op_h&op_s1)|(op_h&op_ch)|(op_s1&op_ch))<<1;
            s1=s0^c0^op_k;c1=((s0&c0)|(s0&op_k)|(c0&op_k))<<1;
            s2=s1^c1^op_d;c2=((s1&c1)|(s1&op_d)|(c1&op_d))<<1;
            last_s=s2^c2^op_w;last_c=((s2&c2)|(s2&op_w)|(c2&op_w))<<1;
            add6_wlast=last_s+last_c;
        end
    endfunction
    function automatic logic [31:0] add7_wlast(input logic [31:0] op_h,op_s1,op_ch,op_k,op_s0,op_maj,op_w);
        logic [31:0] s0,c0,s1,c1,s2,c2,s3,c3,last_s,last_c;
        begin
            s0=op_h^op_s1^op_ch;c0=((op_h&op_s1)|(op_h&op_ch)|(op_s1&op_ch))<<1;
            s1=op_k^op_s0^op_maj;c1=((op_k&op_s0)|(op_k&op_maj)|(op_s0&op_maj))<<1;
            s2=s0^c0^s1;c2=((s0&c0)|(s0&s1)|(c0&s1))<<1;
            s3=s2^c2^c1;c3=((s2&c2)|(s2&c1)|(c2&c1))<<1;
            last_s=s3^c3^op_w;last_c=((s3&c3)|(s3&op_w)|(c3&op_w))<<1;
            add7_wlast=last_s+last_c;
        end
    endfunction
    always_comb begin
        start_ready=!active&&!abort_i&&!rst;
        busy=active;
        data_ready=active&&fill_state==F_DATA&&!bank_full[fill_bank]&&accepted_bytes<message_bytes&&!abort_i&&!rst;
        accepting_data=data_valid&&data_ready;
        bad_last=accepting_data&&(data_last!=(accepted_bytes+1==message_bytes));
        result_valid=active&&result_pending&&!abort_i&&!rst;
        digest={hash_state[0],hash_state[1],hash_state[2],hash_state[3],hash_state[4],hash_state[5],hash_state[6],hash_state[7]};
        bit_length={29'd0,message_bytes,3'd0};
        write_byte=0;next_byte=0;
        if(active&&!bank_full[fill_bank])begin
            case(fill_state)
                F_DATA:begin write_byte=accepting_data;next_byte=data;end
                F_PAD_ONE:begin write_byte=1;next_byte=8'h80;end
                F_PAD_ZERO:begin write_byte=(byte_position!=56);next_byte=0;end
                F_LENGTH:begin write_byte=1;next_byte=bit_length[63-{length_index,3'd0}-:8];end
                default:begin end
            endcase
        end
        ring_index=round_index[3:0];
        schedule_word=words[process_bank][ring_index];
        // During round t, ring[i] is already the registered W[t].
        // Simultaneously prepare W[t+16] from still-live ring operands. The
        // first16words are fully byte-filled before bank_full admits C_ROUND.
        future_word=add4_mod(small1(words[process_bank][4'(ring_index+4'd14)]),
            words[process_bank][4'(ring_index+4'd9)],
            small0(words[process_bank][4'(ring_index+4'd1)]),
            words[process_bank][ring_index]);
        round_e=add6_wlast(h,big1(e),((e&f)^((~e)&g)),constant_k(round_index),d,schedule_word);
        round_a=add7_wlast(h,big1(e),((e&f)^((~e)&g)),constant_k(round_index),big0(a),((a&b)^(a&c)^(b&c)),schedule_word);
        debug_fill_state=fill_state;debug_core_state=core_state;
    end
    always_ff @(posedge clk)begin
        if(rst)begin
            active<=0;result_pending<=0;error<=0;aborted<=0;error_code<=0;
            message_bytes<=0;accepted_bytes<=0;compressed_blocks<=0;round_cycles<=0;padding_bytes<=0;input_stall_cycles<=0;output_stall_cycles<=0;
            bank_full<=0;bank_last<=0;fill_bank<=0;process_bank<=0;byte_position<=0;round_index<=0;length_index<=0;
            fill_state<=F_DONE;core_state<=C_IDLE;a<=0;b<=0;c<=0;d<=0;e<=0;f<=0;g<=0;h<=0;
            for(i=0;i<8;i=i+1)hash_state[i]<=0;
        end else begin
            aborted<=0;
            if(abort_i)begin
                active<=0;result_pending<=0;bank_full<=0;bank_last<=0;core_state<=C_IDLE;fill_state<=F_DONE;aborted<=1;
            end else if(start_valid&&start_ready)begin
                active<=1;result_pending<=0;error<=0;error_code<=0;
                message_bytes<=total_bytes;accepted_bytes<=0;compressed_blocks<=0;round_cycles<=0;padding_bytes<=0;input_stall_cycles<=0;output_stall_cycles<=0;
                bank_full<=0;bank_last<=0;fill_bank<=0;process_bank<=0;byte_position<=0;round_index<=0;length_index<=0;
                fill_state<=total_bytes==0?F_PAD_ONE:F_DATA;core_state<=C_IDLE;
                hash_state[0]<=32'h6a09e667;hash_state[1]<=32'hbb67ae85;hash_state[2]<=32'h3c6ef372;hash_state[3]<=32'ha54ff53a;
                hash_state[4]<=32'h510e527f;hash_state[5]<=32'h9b05688c;hash_state[6]<=32'h1f83d9ab;hash_state[7]<=32'h5be0cd19;
            end else if(bad_last)begin
                active<=0;result_pending<=0;bank_full<=0;core_state<=C_IDLE;fill_state<=F_DONE;error<=1;error_code<=8'h01;
            end else if(result_valid&&result_ready)begin
                active<=0;result_pending<=0;
            end else if(active)begin
                if(data_valid&&!data_ready&&fill_state==F_DATA)input_stall_cycles<=input_stall_cycles+1;
                if(result_valid&&!result_ready)output_stall_cycles<=output_stall_cycles+1;
                if(fill_state==F_PAD_ZERO&&!bank_full[fill_bank]&&byte_position==56)begin fill_state<=F_LENGTH;length_index<=0;end
                if(write_byte)begin
                    if(byte_position==63)begin
                        bank_full[fill_bank]<=1;bank_last[fill_bank]<=(fill_state==F_LENGTH&&length_index==7);byte_position<=0;
                        if(BUFFER_BLOCKS==2)fill_bank<=!fill_bank;
                    end else byte_position<=byte_position+1;
                    case(fill_state)
                        F_DATA:begin accepted_bytes<=accepted_bytes+1;if(data_last)fill_state<=F_PAD_ONE;end
                        F_PAD_ONE:begin padding_bytes<=padding_bytes+1;fill_state<=F_PAD_ZERO;end
                        F_PAD_ZERO:padding_bytes<=padding_bytes+1;
                        F_LENGTH:begin
                            padding_bytes<=padding_bytes+1;
                            if(length_index==7)fill_state<=F_DONE;else length_index<=length_index+1;
                        end
                        default:begin end
                    endcase
                end
                case(core_state)
                    C_IDLE:if(bank_full[process_bank]&&!result_pending)begin
                        a<=hash_state[0];b<=hash_state[1];c<=hash_state[2];d<=hash_state[3];
                        e<=hash_state[4];f<=hash_state[5];g<=hash_state[6];h<=hash_state[7];round_index<=0;core_state<=C_ROUND;
                    end
                    C_ROUND:begin
                        h<=g;g<=f;f<=e;e<=round_e;d<=c;c<=b;b<=a;a<=round_a;
                        round_cycles<=round_cycles+1;
                        if(round_index==63)core_state<=C_ADD;else round_index<=round_index+1;
                    end
                    C_ADD:begin
                        hash_state[0]<=hash_state[0]+a;hash_state[1]<=hash_state[1]+b;hash_state[2]<=hash_state[2]+c;hash_state[3]<=hash_state[3]+d;
                        hash_state[4]<=hash_state[4]+e;hash_state[5]<=hash_state[5]+f;hash_state[6]<=hash_state[6]+g;hash_state[7]<=hash_state[7]+h;
                        compressed_blocks<=compressed_blocks+1;bank_full[process_bank]<=0;core_state<=C_IDLE;
                        if(bank_last[process_bank])result_pending<=1;
                        else if(BUFFER_BLOCKS==2)process_bank<=!process_bank;
                    end
                    default:begin active<=0;error<=1;error_code<=8'hff;end
                endcase
            end
        end
    end
    // Same-edge private payload writer. Keep procedural if/else semantics,
    // including unknown-valued control fall-through. Local proved invariants
    // exclude result consumption whenever either private write can occur.
    always_ff @(posedge clk)begin
        if(rst)begin end
        else if(abort_i)begin end
        else if(start_valid&&start_ready)begin end
        else if(bad_last)begin end
        else if(active)begin
            if(write_byte)
                words[fill_bank][byte_position[5:2]][31-{byte_position[1:0],3'd0}-:8]<=next_byte;
            if(core_state==C_ROUND)begin
                if(round_index<48)words[process_bank][ring_index]<=future_word;
            end
        end
    end
endmodule
