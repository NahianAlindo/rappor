`timescale 1ns/1ps
module tb;
    reg clk, rst, d;
    wire pulse;
    reg prev;
    integer i, errors, checks;
    edge_detect dut (.clk(clk), .rst(rst), .d(d), .pulse(pulse));
    always #5 clk = ~clk;
    initial begin
        clk = 0; rst = 1; d = 0; prev = 0; errors = 0; checks = 0;
        @(posedge clk); #1; rst = 0;
        for (i = 0; i < 300; i = i + 1) begin
            d = $random;
            #1;
            checks = checks + 1;
            if (pulse !== (d & ~prev)) errors = errors + 1;
            @(posedge clk);
            prev = d;
            #1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
