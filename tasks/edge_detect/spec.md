Implement a module named `edge_detect`: a rising-edge detector.

Ports:
- input  clk
- input  rst   (synchronous, active high)
- input  d
- output pulse

Behaviour: register d on every rising clock edge. `pulse` is a combinational
output that is high when the current value of d is 1 and the value registered on
the previous clock edge is 0. On reset the registered value becomes 0.
