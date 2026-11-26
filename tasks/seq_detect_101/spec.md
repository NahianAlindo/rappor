Implement a module named `seq_detect_101`: a Moore FSM that detects the bit
sequence 1-0-1 on a serial input, with overlapping matches allowed.

Ports:
- input  clk
- input  rst   (synchronous, active high)
- input  din
- output found

Behaviour: din is sampled on each rising clock edge. `found` is a registered
(Moore) output that is high for exactly one cycle after the edge on which the
last three sampled bits were 1, 0, 1 (oldest first). Overlap example: the input
stream 1,0,1,0,1 produces two detections. Reset returns the FSM to its idle
state with found = 0.
