module alu4 (
    input  wire [3:0] a, b,
    input  wire [2:0] op,
    output reg  [3:0] y,
    output wire       zero
);
    always @(*) begin
        case (op)
            3'd0: y = a + b;
            3'd1: y = a - b;
            3'd2: y = a & b;
            3'd3: y = a | b;
            3'd4: y = a ^ b;
            3'd5: y = ~a;
            3'd6: y = a << 1;
            default: y = (a < b) ? 4'd1 : 4'd0;
        endcase
    end
    assign zero = (y == 4'd0);
endmodule
