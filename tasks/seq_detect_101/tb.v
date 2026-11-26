`timescale 1ns/1ps
module tb;
    reg clk, rst, din;
    wire found;
    reg [2:0] hist;
    reg exp;
    integer i, errors, checks, nbits;
    seq_detect_101 dut (.clk(clk), .rst(rst), .din(din), .found(found));
    always #5 clk = ~clk;
    initial begin
        clk = 0; rst = 1; din = 0; hist = 0; nbits = 0; errors = 0; checks = 0;
        @(posedge clk); #1; rst = 0;
        for (i = 0; i < 400; i = i + 1) begin
            din = (i < 5) ? ((i % 2) == 0) : $random;
            @(posedge clk);
            hist = {hist[1:0], din};
            nbits = nbits + 1;
            exp = (nbits >= 3) && (hist == 3'b101);
            #1;
            checks = checks + 1;
            if (found !== exp) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
