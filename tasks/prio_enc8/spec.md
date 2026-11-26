Implement a module named `prio_enc8`: an 8-input priority encoder.

Ports:
- input  [7:0] req
- output [2:0] idx
- output       valid

Behaviour: `idx` is the index of the highest-numbered bit of req that is set
(bit 7 has the highest priority). `valid` is 1 when any bit of req is set.
When req is 0, valid is 0 and idx is 0. Purely combinational.
