Implement a module named `alu4`: a small 4-bit ALU.

Ports:
- input  [3:0] a, b
- input  [2:0] op
- output [3:0] y
- output       zero

Operations (op):
- 0: y = a + b (low 4 bits)
- 1: y = a - b (low 4 bits)
- 2: y = a & b
- 3: y = a | b
- 4: y = a ^ b
- 5: y = ~a
- 6: y = a << 1 (low 4 bits)
- 7: y = 1 if a < b (unsigned) else 0

`zero` is 1 when y is 0. Purely combinational.
