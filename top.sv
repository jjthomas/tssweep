module StreamingWrapper(
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

parameter NUM_PU = {num_pu};
parameter NUM_PARAMS = {num_params};
parameter NUM_OUTPUTS = {num_outputs};

logic [31:0] input_word;
logic input_valid [NUM_PU-1:0];
logic input_finished [NUM_PU-1:0];
logic [31:0] output_word [NUM_PU-1:0];
logic output_valid [NUM_PU-1:0];
logic output_ready [NUM_PU-1:0];

logic [$max(1, $clog2(NUM_PU))-1:0] param_pu_counter;
logic [$max(1, $clog2(NUM_PARAMS))-1:0] param_counter;
logic [511:0] input_buffer;
logic [3:0] word_in_input; // 16 32-bit words
logic [31:0] input_addr;
logic [31:0] stream_len; // in 32-bit words
logic [31:0] addr_word_counter; // word counter in stream for addr request FSM
logic [31:0] data_word_counter; // word counter in stream for data processing FSM
logic at_stream; // past params & len

enum logic [1:0] {SEND_INPUT_ADDR = 0, RCV_INPUT_DATA = 1, PROCESS_INPUT_DATA = 2} input_state;

always_comb begin

end

always_ff @(posedge clock) begin
  if (reset) begin
    input_addr <= 0;
  end
end

genvar i;
generate
  for (i = 0; i < NUM_PU; i = i + 1) begin
    {comp_name} pu (.clock(clock), .reset(reset), .input_word(input_word),
                    .input_valid(input_valid[i]), .input_finished(input_finished[i]),
                    .output_word(output_word[i]), .output_valid(output_valid[i]),
                    .output_ready(output_ready[i]));
  end
endgenerate

endmodule
