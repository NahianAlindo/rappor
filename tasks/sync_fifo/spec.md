Implement a module named `sync_fifo`: a synchronous FIFO, 8 bits wide and 4 entries deep.

Ports:
- input        clk
- input        rst   (synchronous, active high)
- input        wr_en
- input  [7:0] wr_data
- input        rd_en
- output [7:0] rd_data
- output       full
- output       empty

Behaviour:
- A write happens on a rising edge when wr_en is high and the FIFO is not full.
- A read happens on a rising edge when rd_en is high and the FIFO is not empty.
- A read and a write may happen on the same edge.
- `rd_data` is combinational and always shows the oldest entry (first-word
  fall-through). Its value is don't-care while empty.
- `full` and `empty` are derived from the current entry count.
- Reset empties the FIFO.
