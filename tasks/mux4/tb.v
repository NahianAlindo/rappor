`timescale 1ns/1ps
module tb;
    reg  [7:0] a, b, c, d;
    reg  [1:0] sel;
    wire [7:0] y;
    integer i, errors, checks;
    reg [7:0] exp;
    mux4 dut (.a(a), .b(b), .c(c), .d(d), .sel(sel), .y(y));
    initial begin
        errors = 0; checks = 0;
        for (i = 0; i < 200; i = i + 1) begin
            a = $random; b = $random; c = $random; d = $random; sel = $random;
            #1;
            case (sel) 0: exp = a; 1: exp = b; 2: exp = c; default: exp = d; endcase
            checks = checks + 1;
            if (y !== exp) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
