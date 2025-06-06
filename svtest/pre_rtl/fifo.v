`timescale 1ns/1ps
module fifo
#(
	parameter integer DWIDTH = 32,
	parameter integer AWIDTH = 4
)
(
	input clock, reset, wr_en, rd_en,
	input [DWIDTH-1:0] data_in,
	output f_full, f_empty,
	output [DWIDTH-1:0] data_out
);
	reg [DWIDTH-1:0] mem [0:2**AWIDTH-1];
	reg [AWIDTH-1:0] wr_ptr;
	reg [AWIDTH-1:0] rd_ptr;
	reg [AWIDTH-1:0] counter;
	wire [AWIDTH-1:0] wr;
	wire [AWIDTH-1:0] rd;
	wire [AWIDTH-1:0] w_counter;
	always@(posedge clock)
	begin
		if (reset)
		begin
			wr_ptr <= {(AWIDTH){1'b0}};
		end
		else if (wr_en && !f_full)
		begin
			mem[wr_ptr]<=data_in;
			wr_ptr <= wr;
		end
	end
	always@(posedge clock)
	begin
		if (reset)
		begin
			rd_ptr <= {(AWIDTH){1'b0}};
		end
		else if (rd_en && !f_empty)
		begin
			rd_ptr <= rd;
		end
	end
	always@(posedge clock)
	begin
		if (reset)
		begin
			counter <= {(AWIDTH){1'b0}};
		end
		else
		begin
			if (rd_en && !f_empty && !wr_en)
			begin
				counter <= w_counter;
			end
			else if (wr_en && !f_full && !rd_en)
			begin
				counter <= w_counter;
			end
		end
	end
	assign f_full = (counter == 4'd15)?1'b1:1'b0;
	assign f_empty = (counter == 4'd0)?1'b1:1'b0;
	assign wr = (wr_en && !f_full)?wr_ptr + 4'd1:wr_ptr + 4'd0;
	assign rd = (rd_en && !f_empty)?rd_ptr+ 4'd1:rd_ptr+ 4'd0;
	assign w_counter = (rd_en && !f_empty && !wr_en)? counter - 4'd1:
			   (wr_en && !f_full && !rd_en)? counter + 4'd1:
			    w_counter + 4'd0;
	assign data_out = mem[rd_ptr];
endmodule
