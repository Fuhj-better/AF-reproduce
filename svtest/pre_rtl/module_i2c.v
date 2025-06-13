`timescale 1ns/1ps
module module_i2c#(
			parameter integer DWIDTH = 32,
			parameter integer AWIDTH = 14
		)
		(
		 input PCLK,
		 input PRESETn,
		 input fifo_tx_f_full,
		 input fifo_tx_f_empty,
		 input [DWIDTH-1:0] fifo_tx_data_out,
		 input fifo_rx_f_full,
		 input fifo_rx_f_empty,
		 output reg fifo_rx_wr_en,
		 output reg [DWIDTH-1:0] fifo_rx_data_in,
		 input [AWIDTH-1:0] DATA_CONFIG_REG,
 		 input [AWIDTH-1:0] TIMEOUT_TX,
		 output reg fifo_tx_rd_en,
		 output   TX_EMPTY,
		 output   RX_EMPTY,
		 output ERROR,
		 output ENABLE_SDA,
		 output ENABLE_SCL,
		inout SDA,
		inout SCL
		 );
assign TX_EMPTY = (fifo_tx_f_empty == 1'b1)? 1'b1:1'b0;
assign RX_EMPTY = (fifo_rx_f_empty == 1'b1)? 1'b1:1'b0;
	reg [1:0] count_tx;
	reg [1:0] count_rx;
	reg [11:0] count_send_data;
	reg [11:0] count_receive_data;
	reg [11:0] count_timeout;
	reg BR_CLK_O;
	reg SDA_OUT;
	reg BR_CLK_O_RX;
	reg SDA_OUT_RX;
	reg RESPONSE;
localparam [5:0] IDLE = 6'd0,
	   START = 6'd1,
	     CONTROLIN_1 = 6'd2,
	     CONTROLIN_2 = 6'd3,
	     CONTROLIN_3 = 6'd4,
             CONTROLIN_4 = 6'd5,
	     CONTROLIN_5 = 6'd6,
	     CONTROLIN_6 = 6'd7,
             CONTROLIN_7 = 6'd8,
             CONTROLIN_8 = 6'd9,
	     RESPONSE_CIN =6'd10,
	     ADDRESS_1 = 6'd11,
	     ADDRESS_2 = 6'd12,
	     ADDRESS_3 = 6'd13,
             ADDRESS_4 = 6'd14,
	     ADDRESS_5 = 6'd15,
	     ADDRESS_6 = 6'd16,
             ADDRESS_7 = 6'd17,
             ADDRESS_8 = 6'd18,
	     RESPONSE_ADDRESS =6'd19,
	     DATA0_1 = 6'd20,
	     DATA0_2 = 6'd21,
	     DATA0_3 = 6'd22,
             DATA0_4 = 6'd23,
	     DATA0_5 = 6'd24,
	     DATA0_6 = 6'd25,
             DATA0_7 = 6'd26,
             DATA0_8 = 6'd27,
	     RESPONSE_DATA0_1 = 6'd28,
	     DATA1_1 = 6'd29,
	     DATA1_2 = 6'd30,
	     DATA1_3 = 6'd31,
             DATA1_4 = 6'd32,
	     DATA1_5 = 6'd33,
	     DATA1_6 = 6'd34,
             DATA1_7 = 6'd35,
             DATA1_8 = 6'd36,
	     RESPONSE_DATA1_1 = 6'd37,
	     DELAY_BYTES = 6'd38,
	     NACK = 6'd39,
	     STOP = 6'd40;
	reg [5:0] state_tx;
	reg [5:0] next_state_tx;
assign SDA =(DATA_CONFIG_REG[0] == 1'b1 & DATA_CONFIG_REG[1] == 1'b0 & state_tx != RESPONSE_CIN & state_tx != RESPONSE_ADDRESS & state_tx != RESPONSE_DATA0_1 & state_tx != RESPONSE_DATA1_1)?SDA_OUT:SDA_OUT_RX;
assign SCL = (DATA_CONFIG_REG[0] == 1'b1 & DATA_CONFIG_REG[1] == 1'b0)?BR_CLK_O:BR_CLK_O_RX;
assign ERROR = (DATA_CONFIG_REG[0] == 1'b1 & DATA_CONFIG_REG[1] == 1'b1)?1'b1:1'b0;
always@(*)
begin
	next_state_tx=state_tx;
	case(state_tx)
	IDLE:
	begin
		if(DATA_CONFIG_REG[0] == 1'b0 && (fifo_tx_f_full == 1'b1 || fifo_tx_f_empty == 1'b0) && DATA_CONFIG_REG[1] == 1'b0)
		begin
			next_state_tx   = IDLE;
		end
		else if(DATA_CONFIG_REG[0] == 1'b1 && (fifo_tx_f_full == 1'b1 || fifo_tx_f_empty == 1'b0) && DATA_CONFIG_REG[1] == 1'b1)
		begin
			next_state_tx   = IDLE;
		end
		else if(DATA_CONFIG_REG[0] == 1'b1 && ((fifo_tx_f_full == 1'b0 && fifo_tx_f_empty == 1'b0) || fifo_tx_f_full == 1'b1) && DATA_CONFIG_REG[1] == 1'b0 && count_timeout < TIMEOUT_TX)
		begin
			next_state_tx   = START;
		end
	end
	START:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx   = START;
		end
		else
		begin
			next_state_tx   = CONTROLIN_1;
		end
	end
	CONTROLIN_1:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = CONTROLIN_1;
		end
		else
		begin
			next_state_tx  =  CONTROLIN_2;
		end
	end
	CONTROLIN_2:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx   = CONTROLIN_2;
		end
		else
		begin
			next_state_tx   = CONTROLIN_3;
		end
	end
	CONTROLIN_3:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  =  CONTROLIN_3;
		end
		else
		begin
			next_state_tx   = CONTROLIN_4;
		end
	end
	CONTROLIN_4:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx   = CONTROLIN_4;
		end
		else
		begin
			next_state_tx   = CONTROLIN_5;
		end
	end
	CONTROLIN_5:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = CONTROLIN_5;
		end
		else
		begin
			next_state_tx = CONTROLIN_6;
		end
	end
	CONTROLIN_6:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = CONTROLIN_6;
		end
		else
		begin
			next_state_tx = CONTROLIN_7;
		end
	end
	CONTROLIN_7:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = CONTROLIN_7;
		end
		else
		begin
			next_state_tx = CONTROLIN_8;
		end
	end
	CONTROLIN_8:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = CONTROLIN_8;
		end
		else
		begin
			next_state_tx  = RESPONSE_CIN;
		end
	end
	RESPONSE_CIN:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = RESPONSE_CIN;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_tx = DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_tx = NACK;
		end
	end
	ADDRESS_1:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = ADDRESS_1;
		end
		else
		begin
			next_state_tx  =  ADDRESS_2;
		end
	end
	ADDRESS_2:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_2;
		end
		else
		begin
			next_state_tx = ADDRESS_3;
		end
	end
	ADDRESS_3:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_3;
		end
		else
		begin
			next_state_tx = ADDRESS_4;
		end
	end
	ADDRESS_4:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_4;
		end
		else
		begin
			next_state_tx = ADDRESS_5;
		end
	end
	ADDRESS_5:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_5;
		end
		else
		begin
			next_state_tx = ADDRESS_6;
		end
	end
	ADDRESS_6:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_6;
		end
		else
		begin
			next_state_tx = ADDRESS_7;
		end
	end
	ADDRESS_7:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_7;
		end
		else
		begin
			next_state_tx = ADDRESS_8;
		end
	end
	ADDRESS_8:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = ADDRESS_8;
		end
		else
		begin
			next_state_tx = RESPONSE_ADDRESS;
		end
	end
	RESPONSE_ADDRESS:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = RESPONSE_ADDRESS;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_tx = DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_tx = NACK;
		end
	end
	DATA0_1:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA0_1;
		end
		else
		begin
			next_state_tx = DATA0_2;
		end
	end
	DATA0_2:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA0_2;
		end
		else
		begin
			next_state_tx = DATA0_3;
		end
	end
	DATA0_3:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA0_3;
		end
		else
		begin
			next_state_tx = DATA0_4;
		end
	end
	DATA0_4:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA0_4;
		end
		else
		begin
			next_state_tx = DATA0_5;
		end
	end
	DATA0_5:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA0_5;
		end
		else
		begin
			next_state_tx   = DATA0_6;
		end
	end
	DATA0_6:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = DATA0_6;
		end
		else
		begin
			next_state_tx  = DATA0_7;
		end
	end
	DATA0_7:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = DATA0_7;
		end
		else
		begin
			next_state_tx  = DATA0_8;
		end
	end
	DATA0_8:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = DATA0_8;
		end
		else
		begin
			next_state_tx  =  RESPONSE_DATA0_1;
		end
	end
	RESPONSE_DATA0_1:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  =  RESPONSE_DATA0_1;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_tx  =   DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_tx  =   NACK;
		end
	end
	DATA1_1:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = DATA1_1;
		end
		else
		begin
			next_state_tx  = DATA1_2;
		end
	end
	DATA1_2:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA1_2;
		end
		else
		begin
			next_state_tx = DATA1_3;
		end
	end
	DATA1_3:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = DATA1_3;
		end
		else
		begin
			next_state_tx  =  DATA1_4;
		end
	end
	DATA1_4:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  = DATA1_4;
		end
		else
		begin
			next_state_tx  = DATA1_5;
		end
	end
	DATA1_5:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA1_5;
		end
		else
		begin
			next_state_tx = DATA1_6;
		end
	end
	DATA1_6:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx  =  DATA1_6;
		end
		else
		begin
			next_state_tx  =  DATA1_7;
		end
	end
	DATA1_7:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx =  DATA1_7;
		end
		else
		begin
			next_state_tx =  DATA1_8;
		end
	end
	DATA1_8:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = DATA1_8;
		end
		else
		begin
			next_state_tx = RESPONSE_DATA1_1;
		end
	end
	RESPONSE_DATA1_1:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx   =  RESPONSE_DATA1_1;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_tx   =  DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_tx   =  NACK;
		end
	end
	DELAY_BYTES:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx =  DELAY_BYTES;
		end
		else
		begin
			if(count_tx == 2'd0)
			begin
				next_state_tx = ADDRESS_1;
			end
			else if(count_tx   == 2'd1)
			begin
				next_state_tx = DATA0_1;
			end
			else if(count_tx   == 2'd2)
			begin
				next_state_tx = DATA1_1;
			end
			else if(count_tx   == 2'd3)
			begin
				next_state_tx = STOP;
			end
		end
	end
	NACK:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2]*2'd2)
		begin
			next_state_tx  = NACK;
		end
		else
		begin
			if(count_tx == 2'd0)
			begin
				next_state_tx = CONTROLIN_1;
			end
			else if(count_tx == 2'd1)
			begin
				next_state_tx = ADDRESS_1;
			end
			else if(count_tx  == 2'd2)
			begin
				next_state_tx   = DATA0_1;
			end
			else if(count_tx == 2'd3)
			begin
				next_state_tx = DATA1_1;
			end
		end
	end
	STOP:
	begin
		if(count_send_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_tx = STOP;
		end
		else
		begin
			next_state_tx = IDLE;
		end
	end
	default:
	begin
		next_state_tx =  IDLE;
	end
	endcase
end
always@(posedge PCLK)
begin
	if(!PRESETn)
	begin
		count_send_data <= 12'd0;
		state_tx   <= IDLE;
		SDA_OUT<= 1'b1;
		fifo_tx_rd_en <= 1'b0;
		count_tx   <= 2'd0;
		BR_CLK_O <= 1'b1;
		RESPONSE<= 1'b0;
	end
	else
	begin
		state_tx  <= next_state_tx;
		case(state_tx)
		IDLE:
		begin
			fifo_tx_rd_en <= 1'b0;
			if(DATA_CONFIG_REG[0] == 1'b0 && (fifo_tx_f_full == 1'b1 ||fifo_tx_f_empty == 1'b0) && DATA_CONFIG_REG[1] == 1'b0)
			begin
				count_send_data <= 12'd0;
				SDA_OUT<= 1'b1;
				BR_CLK_O <= 1'b1;
			end
			else if(DATA_CONFIG_REG[0] == 1'b1 && ((fifo_tx_f_empty == 1'b0 && fifo_tx_f_full == 1'b0 )|| fifo_tx_f_full == 1'b1 ) && DATA_CONFIG_REG[1] == 1'b0)
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=1'b0;
			end
			else if(DATA_CONFIG_REG[0] == 1'b1 && (fifo_tx_f_full == 1'b1 ||fifo_tx_f_empty == 1'b0) && DATA_CONFIG_REG[1] == 1'b1)
			begin
				count_send_data <= 12'd0;
				SDA_OUT<= 1'b1;
				BR_CLK_O <= 1'b1;
			end
		end
		START:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				BR_CLK_O <= 1'b0;
			end
			else
			begin
				count_send_data <= 12'd0;
			end
			if(count_send_data == DATA_CONFIG_REG[13:2]- 12'd1)
			begin
				SDA_OUT<=fifo_tx_data_out[0:0];
				count_tx   <= 2'd0;
			end
		end
		CONTROLIN_1:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[0:0];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[1:1];
			end
		end
		CONTROLIN_2:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[1:1];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[2:2];
			end
		end
		CONTROLIN_3:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[2:2];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[3:3];
			end
		end
		CONTROLIN_4:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[3:3];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[4:4];
			end
		end
		CONTROLIN_5:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[4:4];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[5:5];
			end
		end
		CONTROLIN_6:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[5:5];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[6:6];
			end
		end
		CONTROLIN_7:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[6:6];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[7:7];
			end
		end
		CONTROLIN_8:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[7:7];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<= 1'b0;
			end
		end
		RESPONSE_CIN:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				RESPONSE<= SDA;
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
			end
		end
		ADDRESS_1:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[8:8];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[9:9];
			end
		end
		ADDRESS_2:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[9:9];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[10:10];
			end
		end
		ADDRESS_3:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[10:10];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[11:11];
			end
		end
		ADDRESS_4:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[11:11];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[12:12];
			end
		end
		ADDRESS_5:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[12:12];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[13:13];
			end
		end
		ADDRESS_6:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[13:13];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[14:14];
			end
		end
		ADDRESS_7:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[14:14];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[15:15];
			end
		end
		ADDRESS_8:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[15:15];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=1'b0;
			end
		end
		RESPONSE_ADDRESS:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				RESPONSE<= SDA;
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
			end
		end
		DATA0_1:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[16:16];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[17:17];
			end
		end
		DATA0_2:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[17:17];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[18:18];
			end
		end
		DATA0_3:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[18:18];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[19:19];
			end
		end
		DATA0_4:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[19:19];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[20:20];
			end
		end
		DATA0_5:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[20:20];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[21:21];
			end
		end
		DATA0_6:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[21:21];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[22:22];
			end
		end
		DATA0_7:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[22:22];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[23:23];
			end
		end
		DATA0_8:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[23:23];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=1'b0;
			end
		end
		RESPONSE_DATA0_1:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				RESPONSE<= SDA;
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
			end
		end
		DATA1_1:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[24:24];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[25:25];
			end
		end
		DATA1_2:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[25:25];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[26:26];
			end
		end
		DATA1_3:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[26:26];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[27:27];
			end
		end
		DATA1_4:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[27:27];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[28:28];
			end
		end
		DATA1_5:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[28:28];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[29:29];
			end
		end
		DATA1_6:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[29:29];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[30:30];
			end
		end
		DATA1_7:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[30:30];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=fifo_tx_data_out[31:31];
			end
		end
		DATA1_8:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				SDA_OUT<=fifo_tx_data_out[31:31];
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				SDA_OUT<=1'b0;
			end
		end
		RESPONSE_DATA1_1:
		begin
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				RESPONSE<= SDA;
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd4)
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data >= DATA_CONFIG_REG[13:2]/12'd4 && count_send_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					BR_CLK_O <= 1'b1;
				end
				else
				begin
					BR_CLK_O <= 1'b0;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				fifo_tx_rd_en <= 1'b1;
			end
		end
		DELAY_BYTES:
		begin
			fifo_tx_rd_en <= 1'b0;
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				BR_CLK_O <= 1'b0;
				SDA_OUT<=1'b0;
			end
			else
			begin
				if(count_tx == 2'd0)
				begin
					count_tx <= count_tx + 2'd1;
					SDA_OUT<=fifo_tx_data_out[8:8];
				end
				else if(count_tx   == 2'd1)
				begin
					count_tx <= count_tx + 2'd1;
					SDA_OUT<=fifo_tx_data_out[16:16];
				end
				else if(count_tx == 2'd2)
				begin
					count_tx <= count_tx + 2'd1;
					SDA_OUT<=fifo_tx_data_out[24:24];
				end
				else if(count_tx == 2'd3)
				begin
					count_tx <= 2'd0;
				end
				count_send_data <= 12'd0;
			end
		end
		NACK:
		begin
			fifo_tx_rd_en <= 1'b0;
			if(count_send_data < DATA_CONFIG_REG[13:2]*2'd3)
			begin
				count_send_data <= count_send_data + 12'd1;
				if(count_receive_data < DATA_CONFIG_REG[13:2]/12'd2)
				begin
					SDA_OUT<=1'b0;
				end
				else if(count_send_data > DATA_CONFIG_REG[13:2]/12'd2-12'd1 && count_send_data < DATA_CONFIG_REG[13:2])
				begin
					SDA_OUT<=1'b1;
				end
				else if(count_send_data  == DATA_CONFIG_REG[13:2]*2'd2)
				begin
					SDA_OUT<=1'b0;
				end
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd2)
				begin
					BR_CLK_O <= 1'b1;
				end
				else if(count_send_data > DATA_CONFIG_REG[13:2]/12'd2-12'd1 && count_send_data < DATA_CONFIG_REG[13:2])
				begin
					BR_CLK_O <= 1'b0;
				end
				else if(count_send_data < DATA_CONFIG_REG[13:2]*2'd2)
				begin
					BR_CLK_O <= 1'b1;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
				if(count_tx == 2'd0)
				begin
					count_tx <= 2'd0;
					SDA_OUT<=fifo_tx_data_out[0:0];
				end
				else if(count_tx == 2'd1)
				begin
					count_tx <= 2'd1;
					SDA_OUT<=fifo_tx_data_out[8:8];
				end
				else if(count_tx == 2'd2)
				begin
					count_tx <= 2'd2;
					SDA_OUT<=fifo_tx_data_out[16:16];
				end
				else if(count_tx == 2'd3)
				begin
					count_tx <= 2'd3;
					SDA_OUT<=fifo_tx_data_out[24:24];
				end
			end
		end
		STOP:
		begin
			BR_CLK_O <= 1'b1;
			if(count_send_data < DATA_CONFIG_REG[13:2])
			begin
				count_send_data <= count_send_data + 12'd1;
				if(count_send_data < DATA_CONFIG_REG[13:2]/12'd2-12'd2)
				begin
					SDA_OUT<=1'b0;
				end
				else if(count_send_data > DATA_CONFIG_REG[13:2]/12'd2-12'd1 && count_send_data < DATA_CONFIG_REG[13:2])
				begin
					SDA_OUT<=1'b1;
				end
			end
			else
			begin
				count_send_data <= 12'd0;
			end
		end
		default:
		begin
			fifo_tx_rd_en <= 1'b0;
			count_send_data <= 12'd4095;
		end
		endcase
	end
end
	reg [5:0] state_rx;
	reg [5:0] next_state_rx;
assign ENABLE_SDA = (state_rx ==  RESPONSE_CIN||
		     state_rx ==  RESPONSE_ADDRESS||
		     state_rx == RESPONSE_DATA0_1||
		     state_rx == RESPONSE_DATA1_1)?1'b1:
		    (state_tx ==  RESPONSE_CIN||
		     state_tx ==  RESPONSE_ADDRESS||
		     state_tx == RESPONSE_DATA0_1||
		     state_tx == RESPONSE_DATA1_1)?1'b0:1'b1;
assign ENABLE_SCL = (state_rx ==  RESPONSE_CIN||
		     state_rx ==  RESPONSE_ADDRESS||
		     state_rx == RESPONSE_DATA0_1||
		     state_rx == RESPONSE_DATA1_1)?1'b1:
		    (state_tx ==  RESPONSE_CIN||
		     state_tx ==  RESPONSE_ADDRESS||
		     state_tx == RESPONSE_DATA0_1||
		     state_tx == RESPONSE_DATA1_1)?1'b1:1'b0;
always@(*)
begin
	next_state_rx = state_rx;
	case(state_rx)
	IDLE:
	begin
		if(DATA_CONFIG_REG[0] == 1'b0 && DATA_CONFIG_REG[1] == 1'b0)
		begin
			next_state_rx =   IDLE;
		end
		else if(DATA_CONFIG_REG[0] == 1'b1 && DATA_CONFIG_REG[1] == 1'b1)
		begin
			next_state_rx =   IDLE;
		end
		else if(DATA_CONFIG_REG[0] == 1'b0 && DATA_CONFIG_REG[1] == 1'b1 && SDA_OUT_RX == 1'b0 && BR_CLK_O_RX == 1'b0)
		begin
			next_state_rx =   START;
		end
	end
	START:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   START;
		end
		else if(fifo_rx_data_in[0] == 1'b0 && fifo_rx_data_in[1] == 1'b0)
		begin
			next_state_rx =   CONTROLIN_1;
		end
		else
		begin
			next_state_rx =   IDLE;
		end
	end
	  CONTROLIN_1:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_1;
		end
		else
		begin
			next_state_rx =   CONTROLIN_2;
		end
	end
	  CONTROLIN_2:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_2;
		end
		else
		begin
			next_state_rx =   CONTROLIN_3;
		end
	end
	  CONTROLIN_3:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_3;
		end
		else
		begin
			next_state_rx =   CONTROLIN_4;
		end
	end
	  CONTROLIN_4:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_4;
		end
		else
		begin
			next_state_rx =   CONTROLIN_5;
		end
	end
	  CONTROLIN_5:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_5;
		end
		else
		begin
			next_state_rx =   CONTROLIN_6;
		end
	end
	  CONTROLIN_6:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_6;
		end
		else
		begin
			next_state_rx =   CONTROLIN_7;
		end
	end
	  CONTROLIN_7:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_7;
		end
		else
		begin
			next_state_rx =   CONTROLIN_8;
		end
	end
	  CONTROLIN_8:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   CONTROLIN_8;
		end
		else
		begin
			next_state_rx =   RESPONSE_CIN;
		end
	end
	RESPONSE_CIN:
	begin
		if(count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   RESPONSE_CIN;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_rx  =   DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_rx  =   NACK;
		end
	end
	ADDRESS_1:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_1;
		end
		else
		begin
			next_state_rx =   ADDRESS_2;
		end
	end
	ADDRESS_2:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_2;
		end
		else
		begin
			next_state_rx =   ADDRESS_3;
		end
	end
	ADDRESS_3:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_3;
		end
		else
		begin
			next_state_rx =   ADDRESS_4;
		end
	end
	ADDRESS_4:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_4;
		end
		else
		begin
			next_state_rx =   ADDRESS_5;
		end
	end
	ADDRESS_5:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_5;
		end
		else
		begin
			next_state_rx =   ADDRESS_6;
		end
	end
	ADDRESS_6:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_6;
		end
		else
		begin
			next_state_rx =   ADDRESS_7;
		end
	end
	ADDRESS_7:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_7;
		end
		else
		begin
			next_state_rx =   ADDRESS_8;
		end
	end
	ADDRESS_8:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   ADDRESS_8;
		end
		else
		begin
			next_state_rx =   RESPONSE_ADDRESS;
		end
	end
	RESPONSE_ADDRESS:
	begin
		if(count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   RESPONSE_ADDRESS;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_rx  =   DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_rx  =   NACK;
		end
	end
	DATA0_1:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_1;
		end
		else
		begin
			next_state_rx =   DATA0_2;
		end
	end
	  DATA0_2:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_2;
		end
		else
		begin
			next_state_rx =   DATA0_3;
		end
	end
	  DATA0_3:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_3;
		end
		else
		begin
			next_state_rx =   DATA0_4;
		end
	end
	  DATA0_4:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_4;
		end
		else
		begin
			next_state_rx =   DATA0_5;
		end
	end
	  DATA0_5:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_5;
		end
		else
		begin
			next_state_rx =   DATA0_6;
		end
	end
	  DATA0_6:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_6;
		end
		else
		begin
			next_state_rx =   DATA0_7;
		end
	end
	  DATA0_7:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_7;
		end
		else
		begin
			next_state_rx =   DATA0_8;
		end
	end
	  DATA0_8:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA0_8;
		end
		else
		begin
			next_state_rx =   RESPONSE_DATA0_1;
		end
	end
	RESPONSE_DATA0_1:
	begin
		if(count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   RESPONSE_DATA0_1;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_rx  =   DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_rx  =   NACK;
		end
	end
	DATA1_1:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_1;
		end
		else
		begin
			next_state_rx =   DATA1_2;
		end
	end
	DATA1_2:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_2;
		end
		else
		begin
			next_state_rx =   DATA1_3;
		end
	end
	DATA1_3:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_3;
		end
		else
		begin
			next_state_rx =   DATA1_4;
		end
	end
	  DATA1_4:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_4;
		end
		else
		begin
			next_state_rx =   DATA1_5;
		end
	end
	  DATA1_5:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_5;
		end
		else
		begin
			next_state_rx =   DATA1_6;
		end
	end
	  DATA1_6:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_6;
		end
		else
		begin
			next_state_rx =   DATA1_7;
		end
	end
	  DATA1_7:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_7;
		end
		else
		begin
			next_state_rx =   DATA1_8;
		end
	end
	  DATA1_8:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DATA1_8;
		end
		else
		begin
			next_state_rx =   RESPONSE_DATA1_1;
		end
	end
	RESPONSE_DATA1_1:
	begin
		if(count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   RESPONSE_DATA0_1;
		end
		else if(RESPONSE == 1'b0)
		begin
			next_state_rx  =   DELAY_BYTES;
		end
		else if(RESPONSE == 1'b1)
		begin
			next_state_rx  =   NACK;
		end
	end
	DELAY_BYTES:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   DELAY_BYTES;
		end
		else
		begin
			if(count_rx == 2'd0)
			begin
				next_state_rx =   ADDRESS_1;
			end
			else if(count_rx == 2'd1)
			begin
				next_state_rx =   DATA0_1;
			end
			else if(count_rx == 2'd2)
			begin
				next_state_rx =   DATA1_1;
			end
			else if(count_rx == 2'd3)
			begin
				next_state_rx =   STOP;
			end
		end
	end
	  STOP:
	begin
		if(  count_receive_data != DATA_CONFIG_REG[13:2])
		begin
			next_state_rx =   STOP;
		end
		else
		begin
			next_state_rx =   IDLE;
		end
	end
	default:
	begin
			next_state_rx =   IDLE;
	end
	endcase
end
always@(posedge PCLK)
begin
	if(!PRESETn)
	begin
		  count_receive_data <= 12'd0;
		state_rx <=   IDLE;
		SDA_OUT_RX<= 1'b0;
		fifo_rx_wr_en <= 1'b0;
		count_rx <= 2'd0;
		BR_CLK_O_RX <= 1'b0;
	end
	else
	begin
		state_rx <= next_state_rx;
		case(state_rx)
		  IDLE:
		begin
			if(((fifo_rx_f_full == 1'b0 && fifo_rx_f_empty == 1'b0) || (fifo_rx_f_full == 1'b0 && fifo_rx_f_empty == 1'b1)) && DATA_CONFIG_REG[1] == 1'b1)
			begin
				  SDA_OUT_RX<= SDA;
				  BR_CLK_O_RX<=SCL;
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  SDA_OUT_RX<= SDA_OUT_RX;
				  BR_CLK_O_RX<=BR_CLK_O_RX;
				  count_receive_data <=   count_receive_data;
			end
		end
		  START:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(  count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[0]<= SDA;
				fifo_rx_data_in[1]<= SCL;
			end
		end
		  CONTROLIN_1:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[0]<= SDA;
			end
		end
		  CONTROLIN_2:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[1]<= SDA;
			end
		end
		  CONTROLIN_3:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[2]<= SDA;
			end
		end
		  CONTROLIN_4:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[3]<= SDA;
			end
		end
		  CONTROLIN_5:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
					fifo_rx_data_in[4]<= SDA;
			end
		end
		  CONTROLIN_6:
		begin
				if(  count_receive_data < DATA_CONFIG_REG[13:2])
				begin
					  count_receive_data <=   count_receive_data + 12'd1;
				end
				else
				begin
					  count_receive_data <= 12'd0;
				end
				if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
				begin
					fifo_rx_data_in[5]<= SDA;
				end
		end
		  CONTROLIN_7:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[6]<= SDA;
			end
		end
		  CONTROLIN_8:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[7]<= SDA;
			end
		end
		  RESPONSE_CIN:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
		end
		  ADDRESS_1:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[8]<= SDA;
			end
		end
		  ADDRESS_2:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[9]<= SDA;
			end
		end
		  ADDRESS_3:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[10]<= SDA;
			end
		end
		  ADDRESS_4:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[11]<= SDA;
			end
		end
		  ADDRESS_5:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[12]<= SDA;
			end
		end
		  ADDRESS_6:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[13]<= SDA;
			end
		end
		  ADDRESS_7:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[14]<= SDA;
			end
		end
		  ADDRESS_8:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[15]<= SDA;
			end
		end
		  RESPONSE_ADDRESS:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
		end
		  DATA0_1:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[16]<= SDA;
			end
		end
		  DATA0_2:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[17]<= SDA;
			end
		end
		  DATA0_3:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[18]<= SDA;
			end
		end
		  DATA0_4:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[19]<= SDA;
			end
		end
		  DATA0_5:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[20]<= SDA;
			end
		end
		  DATA0_6:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[21]<= SDA;
			end
		end
		  DATA0_7:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[22]<= SDA;
			end
		end
		  DATA0_8:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[23]<= SDA;
			end
		end
		  RESPONSE_DATA0_1:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
		end
		  DATA1_1:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[24]<= SDA;
			end
		end
		  DATA1_2:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[25]<= SDA;
			end
		end
		  DATA1_3:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[26]<= SDA;
			end
		end
		  DATA1_4:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[27]<= SDA;
			end
		end
		  DATA1_5:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[28]<= SDA;
			end
		end
		  DATA1_6:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[29]<= SDA;
			end
		end
		  DATA1_7:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[30]<= SDA;
			end
		end
		  DATA1_8:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			if(SCL == 1'b1 &&   count_receive_data >= DATA_CONFIG_REG[13:2]/12'd4 &&   count_receive_data < (DATA_CONFIG_REG[13:2]-(DATA_CONFIG_REG[13:2]/12'd4))-12'd1)
			begin
				fifo_rx_data_in[31]<= SDA;
			end
		end
		RESPONSE_DATA1_1:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
		end
		DELAY_BYTES:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				if(count_rx == 2'd0)
				begin
					count_rx <= count_rx + 2'd1;
				end
				else if(count_rx   == 2'd1)
				begin
					count_rx <= count_tx + 2'd1;
				end
				else if(count_rx == 2'd2)
				begin
					count_rx <= count_rx + 2'd1;
				end
				else if(count_rx == 2'd3)
				begin
					count_rx <= 2'd0;
				end
				count_receive_data <= 12'd0;
			end
		end
		STOP:
		begin
			if(  count_receive_data < DATA_CONFIG_REG[13:2])
			begin
				  count_receive_data <=   count_receive_data + 12'd1;
			end
			else
			begin
				  count_receive_data <= 12'd0;
			end
			fifo_rx_wr_en <= 1'b0;
		end
		default:
		begin
			fifo_rx_wr_en <= 1'b0;
			  count_receive_data <= 12'd4095;
		end
		endcase
	end
end
always@(posedge PCLK)
begin
	if(!PRESETn)
	begin
		count_timeout <= 12'd0;
	end
	else
	begin
		if(count_timeout <= TIMEOUT_TX && state_tx == IDLE)
		begin
			if(SDA == 1'b0 && SCL == 1'b0)
			count_timeout <= count_timeout + 12'd1;
		end
		else
		begin
			count_timeout <= 12'd0;
		end
	end
end
endmodule
