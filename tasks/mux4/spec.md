Implement a module named `mux4`: a 4-to-1 multiplexer with 8-bit data inputs.

Ports:
- input  [7:0] a, b, c, d
- input  [1:0] sel
- output [7:0] y

Behaviour: y = a when sel == 0, b when sel == 1, c when sel == 2, d when sel == 3.
Purely combinational.
