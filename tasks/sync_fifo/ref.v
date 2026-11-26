module sync_fifo (
    input  wire       clk,
    input  wire       rst,
    input  wire       wr_en,
    input  wire [7:0] wr_data,
    input  wire       rd_en,
    output wire [7:0] rd_data,
    output wire       full,
    output wire       empty
);
    reg [7:0] mem [0:3];
    reg [1:0] wp, rp;
    reg [2:0] count;
    wire do_wr = wr_en && !full;
    wire do_rd = rd_en && !empty;
    always @(posedge clk) begin
        if (rst) begin
            wp <= 0; rp <= 0; count <= 0;
        end else begin
            if (do_wr) begin mem[wp] <= wr_data; wp <= wp + 1; end
            if (do_rd) rp <= rp + 1;
            count <= count + do_wr - do_rd;
        end
    end
    assign rd_data = mem[rp];
    assign full  = (count == 3'd4);
    assign empty = (count == 3'd0);
endmodule
