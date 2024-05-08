`timescale 1ns / 1ps
module tb_Koala
#(parameter PERIOD = 1000,
skip_test = 0, 
SIZE = 257,
SIZE_DIN = 64, 
test_memory_file_KoalaP = "/home/sirena/Documents/KoalaRepo/data_tests/test_vectors-n.txt",
sim_enable_dump = 0 // 1 - True, 0 - False
);

reg [(SIZE - 1):0] test_key;
reg [(SIZE_DIN):0] test_din;
reg [(SIZE - 1):0] true_output;

reg [(SIZE - 1):0] test_output;
wire [(SIZE - 1):0] test_dout;
reg [(SIZE - 1):0] test_dkey;
reg [(SIZE_DIN - 1):0] test_ddin;

reg test_arstn;
reg test_init;
reg test_sqz;
reg test_din_valid;

reg clk;
reg test_error = 1'b0;
reg test_verification = 1'b0;

localparam tb_delay = PERIOD;
localparam tb_delay_read = 3*PERIOD;

Koala
Koala(
    .arstn(test_arstn),
    .clk(clk),
    .init(test_init),
    .sqz(test_sqz),
    .din(test_ddin),
    .din_valid(test_din_valid),
    .key(test_dkey),
    .dout(test_dout)
);


initial begin : clock_generator
    clk <= 1'b1;
    forever begin
        #(PERIOD/2);
        clk <= ~clk;
    end
end


task read_until_get_character;
    input integer file_read;
    input integer character_to_be_found;
    integer temp_text;
    begin
        temp_text = $fgetc(file_read);
        while((temp_text != character_to_be_found) && (!$feof(file_read))) begin
            temp_text = $fgetc(file_read);
        end
    end
endtask

task read_ignore_character;
    input integer file_read;
    input integer character_to_be_ignored;
    output integer last_character;
    integer temp_text;
    begin
        temp_text = $fgetc(file_read);
        while((temp_text == character_to_be_ignored) && (!$feof(file_read))) begin
            temp_text = $fgetc(file_read);
        end
        last_character = temp_text;
    end
endtask


task reverse_bits;
    input [(SIZE-1):0] buffer_in;
    output [(SIZE-1):0] buffer_out;
    integer i;
    begin
        for (i = 0 ; i < SIZE; i= i+1) begin
            buffer_out[i]=buffer_in[(SIZE-1)-i];
        end
    end
endtask


task reverse_bits_din;
    input [(SIZE_DIN-1):0] buffer_in;
    output [(SIZE_DIN-1):0] buffer_out;
    integer i;
    begin
        for (i = 0 ; i < SIZE_DIN; i= i+1) begin
            buffer_out[i]=buffer_in[(SIZE_DIN-1)-i];
        end
    end
endtask

task test_init_state_alone;
    input [(SIZE - 1):0] buffer_in;
    output [(SIZE - 1):0] buffer_out;
    begin
        test_dkey = buffer_in;
        test_init <= 1'b1;
        #(PERIOD);
        test_init <= 1'b0;
        #(PERIOD);
        test_sqz <= 1'b1;
        #(PERIOD);
        buffer_out = test_dout;
        test_sqz <= 1'b0;
        #(PERIOD);
    end
endtask


task test_init_key;
    input [(SIZE - 1):0] buffer_in;
    begin
        test_dkey = buffer_in;
        test_ddin = 64'b0;
        test_init <= 1'b1;
        #(PERIOD);
        test_init <= 1'b0;
        #(PERIOD);
    end
endtask



task test_absorb;
    input [(SIZE_DIN - 1):0] buffer_in;
    integer i;
    begin   
        test_din_valid = 1'b1; 
        test_ddin = buffer_in;
        #(PERIOD);
        test_din_valid = 1'b0;
        #(PERIOD);

    end
endtask



task test_squeeze;
    input [(SIZE_DIN - 1):0] buffer_in;
    output[(SIZE-1):0] buffer_out;
    integer i;
    begin         
        test_ddin = buffer_in;
        test_din_valid = 1'b1; 
        test_sqz = 1'b1; 
        #(PERIOD);
        test_din_valid = 1'b0;
        buffer_out = test_dout;
        test_sqz = 1'b0; 
        #(PERIOD);
     end
endtask


integer KoalaP_file;
integer temp_text1;
integer count;
integer out_size;  //leter
integer in_size; 
integer status_ram_file;

reg [(SIZE-1):0] captured_key;
reg [(SIZE-1):0] captured_out;
reg [(SIZE_DIN):0] captured_din;

reg captured_sqz;

initial begin
    test_error = 1'b0;
    test_verification = 1'b0;
    test_sqz = 1'b0;
    test_din_valid = 1'b0;
    test_init = 1'b0;
    test_key = {(SIZE-1){1'b0}}; 
    test_din = {(SIZE_DIN-1){1'b0}};
    test_output = {(SIZE-1){1'b0}}; 
    true_output = {(SIZE-1){1'b0}}; 
    #(PERIOD);
    test_arstn <= 1'b1;
    #(PERIOD);
    test_arstn <= 1'b0;
    #(PERIOD);
    #(PERIOD);
    #(PERIOD);
    #(PERIOD);
    if(skip_test == 0) begin
        $display("Start of the test");
        KoalaP_file = $fopen(test_memory_file_KoalaP, "r");
        while(!$feof(KoalaP_file)) begin
            read_until_get_character(KoalaP_file, ":");
            status_ram_file = $fscanf(KoalaP_file, "%d", count);

            read_until_get_character(KoalaP_file, ":");
            temp_text1 = $fscanf(KoalaP_file, "%b\n", captured_key);  
            reverse_bits(captured_key,test_key[(SIZE-1):0]);
                 
            
            read_until_get_character(KoalaP_file, ":");
            temp_text1 = $fscanf(KoalaP_file, "%b\n", captured_din);
            captured_sqz = captured_din[64]; 
            reverse_bits_din(captured_din[63:0],test_din); 
             
            test_init_key(test_key);
            test_absorb(test_din);  
            #(PERIOD); 
            
            read_until_get_character(KoalaP_file, ":");
            temp_text1 = $fscanf(KoalaP_file, "%b\n", captured_din);
            captured_sqz = captured_din[64]; 
            reverse_bits_din(captured_din[63:0],test_din); 
            
            
            test_absorb(test_din);  
            #(PERIOD); 
            
            read_until_get_character(KoalaP_file, ":");
            temp_text1 = $fscanf(KoalaP_file, "%b\n", captured_din);
            captured_sqz = captured_din[64]; 
            reverse_bits_din(captured_din[63:0],test_din); 
            
            
            test_squeeze(test_din,test_output);  
            #(PERIOD); 
            
            
            read_until_get_character(KoalaP_file, ":");
            temp_text1 = $fscanf(KoalaP_file, "%b\n", captured_din);
            captured_sqz = captured_din[64]; 
            reverse_bits_din(captured_din[63:0],test_din); 
            
            
            test_squeeze(test_din,test_output);  
            #(PERIOD); 
            
   
            read_until_get_character(KoalaP_file, ":");
            temp_text1 = $fscanf(KoalaP_file, "%b\n", captured_out);
            reverse_bits(captured_out,true_output[(SIZE-1):0]);
            
            test_verification <= 1'b1;
            if (true_output == test_output) begin
                test_error <= 1'b0;
                $display("Computed values match expected ones");
            end else begin
                test_error <= 1'b1;
                $display("Computed values do not match expected ones");
            end

        end
        $fclose(KoalaP_file);
    end
    $display("End of the test.");
    disable clock_generator;
    #(PERIOD);
end

generate
if(sim_enable_dump == 1'b1) begin
    initial
    begin
        $dumpfile("dump");
        $dumpvars(1, tb_KoalaP_rounds_simple_1);
    end
end
endgenerate


endmodule

