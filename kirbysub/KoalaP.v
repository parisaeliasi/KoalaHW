module KoalaP
#(nr_rounds = 8)
(
    input [256:0] KoalaP_i,
    output [256:0] KoalaP_o
);

wire[256:0] round_i_s [(nr_rounds-1):0];
wire[256:0] round_o_s [(nr_rounds-1):0];

genvar i;
generate
    for (i=0; i<nr_rounds; i=i+1) begin: KoalaP_round_n
		KoalaP_round KoalaP_round_ins(
			.round_i(round_i_s[i]),
			.round_o(round_o_s[i])
		);
    end 
endgenerate

assign round_i_s[0] = KoalaP_i;


genvar j;
generate
    for (j=1; j<nr_rounds; j=j+1) begin : chainrounds
        assign round_i_s[j] = round_o_s[j-1];
    end 
endgenerate

assign KoalaP_o = round_o_s[nr_rounds-1];
endmodule

