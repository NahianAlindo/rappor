module shift_reg8 (
    input  wire       clk,
    input  wire       rst,
    input  wire       load,
    input  wire [7:0] din,
    input  wire       sin,
    output reg  [7:0] q
);
    always @(posedge clk) begin
        if (rst)       q <= 8'd0;
        else if (load) q <= din;
        else           q <= {q[6:0], sin};
    end
endmodule
