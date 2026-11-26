`timescale 1ns/1ps
module tb;
    reg  [3:0] a, b;
    reg  [2:0] op;
    wire [3:0] y;
    wire       zero;
    reg  [3:0] exp;
    integer i, errors, checks;
    alu4 dut (.a(a), .b(b), .op(op), .y(y), .zero(zero));
    initial begin
        errors = 0; checks = 0;
        for (i = 0; i < 2048; i = i + 1) begin
            {op, a, b} = i;
            #1;
            case (op)
                0: exp = a + b;  1: exp = a - b;  2: exp = a & b;  3: exp = a | b;
                4: exp = a ^ b;  5: exp = ~a;     6: exp = a << 1;
                default: exp = (a < b) ? 1 : 0;
            endcase
            checks = checks + 1;
            if (y !== exp || zero !== (exp == 0)) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
