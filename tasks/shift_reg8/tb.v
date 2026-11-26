`timescale 1ns/1ps
module tb;
    reg clk, rst, load, sin;
    reg [7:0] din, model;
    wire [7:0] q;
    integer i, errors, checks;
    shift_reg8 dut (.clk(clk), .rst(rst), .load(load), .din(din), .sin(sin), .q(q));
    always #5 clk = ~clk;
    initial begin
        clk = 0; rst = 1; load = 0; din = 0; sin = 0; model = 0;
        errors = 0; checks = 0;
        @(posedge clk); #1;
        for (i = 0; i < 300; i = i + 1) begin
            rst  = ($random % 25 == 0);
            load = ($random % 8 == 0);
            din  = $random;
            sin  = $random;
            @(posedge clk);
            if (rst) model = 0; else if (load) model = din; else model = {model[6:0], sin};
            #1;
            checks = checks + 1;
            if (q !== model) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
