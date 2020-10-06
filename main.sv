module {comp_name}(
  input clock,
  input reset,
  input [31:0] input_word,
  input input_valid,
  input input_finished,
  output [31:0] output_word,
  output output_valid,
  output output_finished,
  input output_ready
);

logic [$max(1, $clog2({num_params}))-1:0] param_input_counter;
logic param_input_finished;
logic input_finished_reg;
logic [$max(1, $clog2({num_state_vars}))-1:0] state_output_counter;
logic state_output_finished;
logic [31:0] output_word_wire;

{logics}

{input_slice}

always_ff @(posedge clock) begin
  if (reset) begin
    param_input_counter <= 0;
    param_input_finished <= 0;
    input_finished_reg <= 0;
    state_output_counter <= 0;
    state_output_finished <= 0;
  end else begin
    if (input_valid && !param_input_finished) begin
      param_input_counter <= param_input_counter + 1;
      if (param_input_counter == {num_params} - 1) begin
        param_input_finished <= 1;
      end
    end
    if (input_finished) begin
      input_finished_reg <= 1;
    end
    if (output_valid && output_ready) begin
      state_output_counter <= state_output_counter + 1;
      if (state_output_counter == {num_state_vars} - 1) begin
        state_output_finished <= 1;
      end
    end
  end
end

always_ff @(posedge clock) begin
{param_setting}
end

always_comb begin
{output_state_selection}
end

always_comb begin
{next_states}
end

always_ff @(posedge clock) begin
  if (reset) begin
{state_vars_init} 
  end else if (input_valid && param_input_finished) begin
{state_vars_update}
  end
end

assign output_word = output_word_wire;
assign output_valid = input_finished_reg && !state_output_finished;
assign output_finished = state_output_finished;
endmodule

