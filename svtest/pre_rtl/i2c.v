`timescale 1ns/1ps
module i2c(
	input PCLK,
	input PRESETn,
	input [31:0] PADDR,
	input [31:0] PWDATA,
	input PWRITE,
	input PSELx,
	input PENABLE,
	output PREADY,
	output PSLVERR,
	output INT_RX,
	output INT_TX,
	output [31:0] PRDATA,
	output SDA_ENABLE,
	output SCL_ENABLE,
	inout SDA,
	inout SCL
	  );
	wire RESET_N;
	assign RESET_N = (PRESETn == 0)?1'b1:1'b0;
	wire TX_RD_EN;
	wire TX_F_EMPTY;
	wire TX_F_FULL;
	wire [31:0] TX_DATA_IN;
	wire [31:0] TX_DATA_OUT;
	wire TX_WRITE_ENA;
	wire RX_RD_EN;
	wire RX_F_EMPTY;
	wire RX_F_FULL;
	wire [31:0] RX_DATA_IN;
	wire [31:0] RX_DATA_OUT;
	wire RX_WRITE_ENA;
	wire [13:0] REGISTER_CONFIG;
	wire [13:0] TIMEOUT_CONFIG;
	wire error;
	wire tx_empty;
	wire rx_empty;
	wire w_full;
	fifo DUT_FIFO_TX (
				.clock(PCLK),
				.reset(RESET_N),
				.wr_en(TX_WRITE_ENA),
				.rd_en(TX_RD_EN),
				.data_in(TX_DATA_IN),
				.f_full(w_full),
				.f_empty(TX_F_EMPTY),
				.data_out(TX_DATA_OUT)
		         );
	assign TX_F_FULL = w_full;
	fifo DUT_FIFO_RX (
				.clock(PCLK),
				.reset(RESET_N),
				.wr_en(RX_WRITE_ENA),
				.rd_en(RX_RD_EN),
				.data_in(RX_DATA_IN),
				.f_full(RX_F_FULL),
				.f_empty(RX_F_EMPTY),
				.data_out(RX_DATA_OUT)
		         );
	apb DUT_APB (
			.PCLK(PCLK),
			.PRESETn(PRESETn),
                        .PADDR(PADDR),
			.PRDATA(PRDATA),
			.PWDATA(PWDATA),
			.PWRITE(PWRITE),
			.PSELx(PSELx),
			.PENABLE(PENABLE),
			.PREADY(PREADY),
			.PSLVERR(PSLVERR),
			.READ_DATA_ON_RX(RX_DATA_OUT),
			.INTERNAL_I2C_REGISTER_CONFIG(REGISTER_CONFIG),
			.INTERNAL_I2C_REGISTER_TIMEOUT(TIMEOUT_CONFIG),
			.INT_RX(INT_RX),
			.WR_ENA(TX_WRITE_ENA),
			.WRITE_DATA_ON_TX(TX_DATA_IN),
			.RD_ENA(RX_RD_EN),
			.INT_TX(INT_TX),
			.TX_EMPTY(tx_empty),
			.RX_EMPTY(rx_empty),
			.ERROR(error)
		     );
	module_i2c DUT_I2C_INTERNAL_RX_TX (
				  	.PCLK(PCLK),
					.PRESETn(PRESETn),
					.fifo_rx_wr_en(RX_WRITE_ENA),
					.fifo_rx_f_empty(RX_F_EMPTY),
					.fifo_rx_data_in(RX_DATA_IN),
					.fifo_rx_f_full(RX_F_FULL),
					.fifo_tx_f_full(TX_F_FULL),
					.fifo_tx_f_empty(TX_F_EMPTY),
					.fifo_tx_rd_en(TX_RD_EN),
					.fifo_tx_data_out(TX_DATA_OUT),
					.DATA_CONFIG_REG(REGISTER_CONFIG),
					.TIMEOUT_TX(TIMEOUT_CONFIG),
					.RX_EMPTY(rx_empty),
					.TX_EMPTY(tx_empty),
					.ERROR(error),
					.ENABLE_SDA(SDA_ENABLE),
					.ENABLE_SCL(SCL_ENABLE),
					.SDA(SDA),
					.SCL(SCL)
				    );
endmodule
