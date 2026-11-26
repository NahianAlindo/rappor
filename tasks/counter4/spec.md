Implement a module named `counter4`: a 4-bit up counter.

Ports:
- input        clk
- input        rst   (synchronous, active high)
- input        en
- output [3:0] q

Behaviour: on each rising edge of clk, if rst is high q becomes 0; otherwise if
en is high q increments by 1 (wrapping from 15 to 0); otherwise q holds.
