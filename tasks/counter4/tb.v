`timescale 1ns/1ps
module tb;
    reg clk, rst, en;
    wire [3:0] q;
    reg  [3:0] model;
    integer i, errors, checks;
    counter4 dut (.clk(clk), .rst(rst), .en(en), .q(q));
    always #5 clk = ~clk;
    initial begin
        clk = 0; rst = 1; en = 0; errors = 0; checks = 0; model = 0;
        @(posedge clk); #1;
        for (i = 0; i < 300; i = i + 1) begin
            rst = ($random % 20 == 0);
            en  = ($random % 4 != 0);
            @(posedge clk);
            if (rst) model = 0; else if (en) model = model + 1;
            #1;
            checks = checks + 1;
            if (q !== model) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
