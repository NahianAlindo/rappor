`timescale 1ns/1ps
module tb;
    reg clk, rst, wr_en, rd_en;
    reg  [7:0] wr_data;
    wire [7:0] rd_data;
    wire full, empty;
    reg  [7:0] q [0:15];
    integer head, tail, n, i, errors, checks;
    reg w, r;
    sync_fifo dut (.clk(clk), .rst(rst), .wr_en(wr_en), .wr_data(wr_data),
                   .rd_en(rd_en), .rd_data(rd_data), .full(full), .empty(empty));
    always #5 clk = ~clk;
    initial begin
        clk = 0; rst = 1; wr_en = 0; rd_en = 0; wr_data = 0;
        head = 0; tail = 0; n = 0; errors = 0; checks = 0;
        @(posedge clk); #1; rst = 0;
        for (i = 0; i < 600; i = i + 1) begin
            wr_en = (i < 300) ? ($random % 3 != 0) : ($random % 3 == 0);
            rd_en = (i < 300) ? ($random % 3 == 0) : ($random % 3 != 0);
            wr_data = $random;
            #1;
            checks = checks + 1;
            if (full !== (n == 4) || empty !== (n == 0)) errors = errors + 1;
            if (n > 0) begin
                checks = checks + 1;
                if (rd_data !== q[head % 16]) errors = errors + 1;
            end
            w = wr_en && (n < 4);
            r = rd_en && (n > 0);
            @(posedge clk);
            if (w) begin q[tail % 16] = wr_data; tail = tail + 1; end
            if (r) head = head + 1;
            n = n + w - r;
            #1;
        end
        $display("RESULT errors=%0d checks=%0d", errors, checks);
        $finish;
    end
endmodule
