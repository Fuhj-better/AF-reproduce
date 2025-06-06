module simple_dff (
    input wire clk,
    input wire rst_n,
    input wire d_in,
    output reg q_out
);
    always @(posedge clk) begin
        if (!rst_n) begin
            q_out <= 1'b0;
        end else begin
            q_out <= d_in;
        end
    end
endmodule
