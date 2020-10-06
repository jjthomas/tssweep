module top(
  input          clock,
  input          reset,
  output [63:0]  inputMemAddr,
  output         inputMemAddrValid,
  output [7:0]   inputMemAddrLen,
  input          inputMemAddrReady,
  input  [511:0] inputMemBlock,
  input          inputMemBlockValid,
  output         inputMemBlockReady,
  output [63:0]  outputMemAddr,
  output         outputMemAddrValid,
  output [7:0]   outputMemAddrLen,
  output [15:0]  outputMemAddrId,
  input          outputMemAddrReady,
  output [511:0] outputMemBlock,
  output         outputMemBlockValid,
  output         outputMemBlockLast,
  input          outputMemBlockReady,
  output         finished
);

endmodule
