`timescale 1ns / 1ps

module tb_KoalaP_round
#(parameter PERIOD = 1000,
maximum_number_of_tests = 100,
test_memory_file_KoalaP_permutation = "/home/sirena/Documents/KoalaRepo/data_tests/KoalaP.dat",
sim_enable_dump = 1 // 1 - True, 0 - False
);

reg [256:0] test_state;
wire [256:0] test_new_state;
reg [256:0] true_new_state;

reg [256:0] test_state_nr;
reg [256:0] true_new_state_nr;


reg clk;
reg test_error = 1'b0;
reg test_verification = 1'b0;

localparam tb_delay = PERIOD/2;
localparam tb_delay_read = 3*PERIOD/4;

KoalaP_round
test (
    .round_i(test_state),
    .round_o(test_new_state)
);
    
initial begin : clock_generator
    clk <= 1'b1;
    forever begin
        #(PERIOD/2);
        clk <= ~clk;
    end
end


task reverse_bits;
    input [256:0] in;
    output [256:0] out;
    integer i;
    begin
        for (i = 0 ; i < 257; i= i+1) begin
            out[i]=in[(256)-i];
        end
    end
endtask

integer ram_file;
integer number_of_tests;
integer test_iterator;
integer status_ram_file;
initial begin
    test_state <= 257'b0;
    #(PERIOD*2);
    #(tb_delay);
    ram_file = $fopen(test_memory_file_KoalaP_permutation, "r");
    status_ram_file = $fscanf(ram_file, "%d", number_of_tests);
    #(PERIOD);
    if((number_of_tests > maximum_number_of_tests) && (maximum_number_of_tests != 0)) begin
        number_of_tests = maximum_number_of_tests;
    end
    for (test_iterator = 1; test_iterator < number_of_tests; test_iterator = test_iterator + 1) begin
        test_error <= 1'b0;
        test_verification <= 1'b0;
        status_ram_file = $fscanf(ram_file, "%b", test_state_nr);
        
        reverse_bits(test_state_nr,test_state[256:0]);
        
        
        status_ram_file = $fscanf(ram_file, "%b", true_new_state_nr);
        
        reverse_bits(true_new_state_nr,true_new_state[256:0]);
        
        //#PERIOD;
        test_verification <= 1'b1;
        if (true_new_state == test_new_state) begin
            test_error <= 1'b0;
        end else begin
            test_error <= 1'b1;
            $display("Computed values do not match expected ones");
        end
        #PERIOD;
        test_error <= 1'b0;
        test_verification <= 1'b0;
        #PERIOD;
    end
    $fclose(ram_file);
    $display("End of the test.");
    disable clock_generator;
    #(PERIOD);
end

generate
if(sim_enable_dump == 1'b1) begin
    initial
    begin
        $dumpfile("dump");
        $dumpvars(1, tb_KoalaP_round);
    end
    end
endgenerate

endmodule

