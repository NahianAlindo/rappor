module seq_detect_101 (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output wire found
);
    localparam IDLE = 2'd0, S1 = 2'd1, S10 = 2'd2, S101 = 2'd3;
    reg [1:0] state;
    always @(posedge clk) begin
        if (rst) state <= IDLE;
        else begin
            case (state)
                IDLE: state <= din ? S1   : IDLE;
                S1:   state <= din ? S1   : S10;
                S10:  state <= din ? S101 : IDLE;
                S101: state <= din ? S1   : S10;
            endcase
        end
    end
    assign found = (state == S101);
endmodule
