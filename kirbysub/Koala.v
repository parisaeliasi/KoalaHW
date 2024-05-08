module Koala
(
    input arstn,
    input clk,
    input init,
    input sqz,
    input [256:0] key,
    input [63:0] din,
    input din_valid,
    output [256:0] dout
);

reg [256:0]  reg_state;
reg[256:0] bef_KoalaP_w;
reg [256:0] dout_s;

reg init_saved; 
reg din_valid_saved;
reg sqz_saved; 
reg next_init_saved;
reg next_din_valid_saved;
reg next_sqz_saved;

wire[256:0] KoalaP_i_w;
wire[256:0] KoalaP_o_w;
wire[256:0] KoalaP_all_xored; 

wire[31:0] v0;
wire[31:0] v1;
wire[31:0] v2;
wire[31:0] v3;


always @(posedge clk or posedge arstn) begin
    if (arstn == 1'b1) begin
        reg_state <= 257'b0;
    end else if (init_saved == 1'b1 || (sqz_saved == 1'b0 && din_valid_saved == 1'b1)) begin
        reg_state <= KoalaP_all_xored;
    end else begin
        reg_state <= reg_state;
    end
end

genvar gen_i;
generate
    for (gen_i = 0; gen_i < 32; gen_i = gen_i + 1) begin : f_of_D      
        assign v0[gen_i] = ((~din[2*gen_i])&(~din[2*gen_i+1]));
        assign v1[gen_i] = ((~din[2*gen_i])&(din[2*gen_i+1])); 
        assign v2[gen_i] = ((din[2*gen_i])&(~din[2*gen_i+1]));
        assign v3[gen_i] = ((din[2*gen_i])&(din[2*gen_i+1]));
    end
endgenerate   
        
always @(posedge clk or posedge arstn) begin
    if (arstn == 1'b1) begin
        init_saved <= 1'b0;
        sqz_saved <= 1'b0;
        din_valid_saved <= 1'b0;
    end else begin
        init_saved <= next_init_saved;
        sqz_saved<= next_sqz_saved;
        din_valid_saved <= next_din_valid_saved;
    end
end

always @(*) begin
    if(init == 1'b1) begin
        next_init_saved = 1'b1;
    end else begin
        next_init_saved = 1'b0;
    end
    if(sqz == 1'b1) begin
        next_sqz_saved = 1'b1;
    end else begin
        next_sqz_saved = 1'b0;
    end
    if(din_valid == 1'b1)begin
        next_din_valid_saved = 1'b1;
    end else begin 
        next_din_valid_saved = 1'b0;
    end 
end    

always @(*) begin
    if(init_saved == 1'b1) begin
        bef_KoalaP_w = key;
    end else if (din_valid_saved == 1'b1) begin 
        bef_KoalaP_w[31:0] = reg_state[31:0]^v0;
        bef_KoalaP_w[63:32] = reg_state[63:32]^v1;
        bef_KoalaP_w[95:64] = reg_state[95:64]^v2;
        bef_KoalaP_w[127:96] = reg_state[127:96]^v3;
        bef_KoalaP_w[255:128]= reg_state[255:128];
        bef_KoalaP_w[256] = reg_state[256]^sqz;
    end else begin
        bef_KoalaP_w = reg_state;
    end 
end

always @(*) begin
    if(sqz == 1'b1) begin
        dout_s = KoalaP_all_xored ;
    end else begin
        dout_s = 257'b0;
    end
end

assign KoalaP_i_w = bef_KoalaP_w;
KoalaP
KoalaP (
    .KoalaP_i(KoalaP_i_w),
    .KoalaP_o(KoalaP_o_w)
);
assign KoalaP_all_xored  = KoalaP_o_w ^ KoalaP_i_w;
assign dout = dout_s;

endmodule 
     

