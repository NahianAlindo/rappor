module adder8 (
    input  wire [7:0] a, b,
    input  wire       cin,
    output wire [7:0] sum,
    output wire       cout
);
    assign {cout, sum} = a + b + cin;
endmodule
