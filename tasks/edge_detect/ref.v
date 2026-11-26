module edge_detect (
    input  wire clk,
    input  wire rst,
    input  wire d,
    output wire pulse
);
    reg d_q;
    always @(posedge clk) begin
        if (rst) d_q <= 1'b0;
        else     d_q <= d;
    end
    assign pulse = d & ~d_q;
endmodule
