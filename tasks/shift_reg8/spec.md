Implement a module named `shift_reg8`: an 8-bit serial-in, parallel-out shift register.

Ports:
- input        clk
- input        rst   (synchronous, active high)
- input        load
- input  [7:0] din
- input        sin
- output [7:0] q

Behaviour on each rising clock edge, in priority order:
1. rst high: q becomes 0.
2. load high: q becomes din.
3. otherwise: shift left by one, with sin entering at bit 0 (q <= {q[6:0], sin}).
