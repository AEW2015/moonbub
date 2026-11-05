module tb;
reg clk=0; always #5 clk=~clk;
reg [3:0] state;
wire valid=state==9; wire ready=state==0;
wire [1:0] named_pair={valid,ready};
initial begin state=0; #12; $display("valid=%b ready=%b inline=%b named=%b single_v=%b single_r=%b",valid,ready,$isunknown({valid,ready}),$isunknown(named_pair),$isunknown(valid),$isunknown(ready));
if ($isunknown(named_pair)) $fatal(1,"NAMED_KNOWN_FAILED");
state=4'bxxxx; #1; if (!$isunknown(named_pair)) $fatal(1,"X_NOT_DETECTED");
state=4'bzzzz; #1; if (!$isunknown(named_pair)) $fatal(1,"Z_NOT_DETECTED");
$display("NAMED_CHECKER_XZ_PASS"); $finish;end
endmodule
