`timescale 1ns/1ps
module tb;
    reg  [7:0] a, b;
    reg        cin;
    wire [7:0] sum;
    wire       cout;
    integer i, errors, checks;
    reg [8:0] exp;
    adder8 dut (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));
    initial begin
        errors = 0; checks = 0;
        for (i = 0; i < 500; i = i + 1) begin
            a = $random; b = $random; cin = $random;
            if (i == 0) begin a = 8'hFF; b = 8'h00; cin = 1; end
            #1;
            exp = a + b + cin;
            checks = checks + 1;
            if ({cout, sum} !== exp) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
