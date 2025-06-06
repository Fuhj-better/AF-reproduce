// 文件名: simple_dff.v

module simple_dff (
    input wire clk,      // 时钟输入
    input wire rst_n,    // 同步低有效复位输入
    input wire d_in,     // 数据输入
    output reg q_out     // 数据输出（声明为 reg 类型，因为在 always 块中赋值）
);

    // 这是一个 always 块，它在 clk 的上升沿触发
    // 实现一个带同步复位的 D 触发器
    always @(posedge clk) begin
        if (!rst_n) begin // 如果复位信号 rst_n 为低（有效复位）
            q_out <= 1'b0; // 输出被复位为 0
        end else begin        // 否则（非复位状态）
            q_out <= d_in;   // 将输入 d_in 的值赋给输出 q_out
        end
    end

endmodule