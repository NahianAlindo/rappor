`timescale 1ns/1ps
module tb;
    reg  [7:0] req;
    wire [2:0] idx;
    wire       valid;
    reg  [2:0] exp_idx;
    integer i, j, errors, checks;
    prio_enc8 dut (.req(req), .idx(idx), .valid(valid));
    initial begin
        errors = 0; checks = 0;
        for (i = 0; i < 256; i = i + 1) begin
            req = i;
            exp_idx = 0;
            for (j = 0; j < 8; j = j + 1) if (req[j]) exp_idx = j;
            #1;
            checks = checks + 1;
            if (valid !== (req != 0) || idx !== exp_idx) errors = errors + 1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
