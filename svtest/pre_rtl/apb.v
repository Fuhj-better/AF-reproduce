`timescale 1ns/1ps
module apb(
	    	input PCLK,
			input PRESETn,
			input PSELx,
			input PWRITE,
			input PENABLE,
			input [31:0] PADDR,
			input [31:0] PWDATA,
			input [31:0] READ_DATA_ON_RX,
			input ERROR,
			input TX_EMPTY,
			input RX_EMPTY,
			output [31:0] PRDATA,
			output reg [13:0] INTERNAL_I2C_REGISTER_CONFIG,
			output reg [13:0] INTERNAL_I2C_REGISTER_TIMEOUT,
			output [31:0] WRITE_DATA_ON_TX,
			output  WR_ENA,
			output  RD_ENA,
			output PREADY,
			output PSLVERR,
			output INT_RX,
			output INT_TX
	  );
assign WR_ENA = (PWRITE == 1'b1 & PENABLE == 1'b1 & PADDR == 32'd0 & PSELx == 1'b1)?  1'b1:1'b0;
assign RD_ENA = (PWRITE == 1'b0 & PENABLE == 1'b1  & PADDR == 32'd4 & PSELx == 1'b1)?  1'b1:1'b0;
assign PREADY = ((WR_ENA == 1'b1 | RD_ENA == 1'b1 | PADDR == 32'd8 | PADDR == 32'd12) &  (PENABLE == 1'b1 & PSELx == 1'b1))? 1'b1:1'b0;
assign WRITE_DATA_ON_TX = (PADDR == 32'd0)? PWDATA:PWDATA;
assign PRDATA = (PADDR == 32'd4)? READ_DATA_ON_RX:READ_DATA_ON_RX;
assign PSLVERR = ERROR;
assign INT_TX = TX_EMPTY;
assign INT_RX = RX_EMPTY;
always@(posedge PCLK)
begin
	if(!PRESETn)
	begin
		INTERNAL_I2C_REGISTER_CONFIG <= 14'd0;
		INTERNAL_I2C_REGISTER_TIMEOUT <= 14'd0;
	end
	else
	begin
		if(PADDR == 32'd8 && PSELx == 1'b1 && PWRITE == 1'b1 && PREADY == 1'b1)
		begin
			INTERNAL_I2C_REGISTER_CONFIG <= PWDATA[13:0];
		end
		else if(PADDR == 32'd12 && PSELx == 1'b1 && PWRITE == 1'b1 && PREADY == 1'b1)
		begin
			INTERNAL_I2C_REGISTER_TIMEOUT <= PWDATA[13:0];
		end
		else
		begin
			INTERNAL_I2C_REGISTER_CONFIG <= INTERNAL_I2C_REGISTER_CONFIG;
		end
	end
end
endmodule
