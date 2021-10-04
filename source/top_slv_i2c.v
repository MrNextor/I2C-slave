module top_slv_i2c
    #(parameter FPGA_CLK = 50_000_000,  // FPGA frequency 50 MHz
      parameter I2C_CLK  = 100_000,     // I2C bus frequency 400 KHz
      parameter DATA_SZ  = 8)           // data widht
    (CLK, RST_n, I_ACK, I_SCL,
     O_ADDR_SLV, O_RW, O_DATA_RD, O_ACK_MSTR, O_BUSY,
     IO_SDA);
    
    
//--------------------------------------------------------------------------    
//  input signals
    input wire                CLK;       // clock 50 MHz
    input wire                RST_n;     // asynchronous reset_n
    input wire I_SCL; // serial clock I2C bus 
    input wire I_ACK;
//  output signals
    output wire [DATA_SZ-2:0] O_ADDR_SLV; // addr the slave
    output wire               O_RW;       // RW
    output wire [DATA_SZ-1:0] O_DATA_RD;  // read data from the master
    output wire               O_ACK_MSTR; // ACK from the master
    output wire               O_BUSY;
//  bidirectional signals
    inout wire IO_SDA; // serial data I2C bus
//  internal signals        
    wire               mdl_lw_io_scl;     // enable I2_C slave to transmit a bit    
    wire               mdl_hg_io_scl;     
    wire sda;
    wire sda_out;
    reg cr_sda;
    reg pr_sda;
    wire rs_sda;
    wire fl_sda;
    reg cr_scl;
    reg pr_scl;
    wire rs_scl;
    wire fl_scl;
    
//--------------------------------------------------------------------------       
    assign sda    = IO_SDA;
    assign IO_SDA = sda_out ? 1'bz : 1'b0;
    assign rs_sda = cr_sda & !pr_sda;
    assign fl_sda = !cr_sda & pr_sda;
    assign rs_scl = cr_scl & !pr_scl;
    assign fl_scl = !cr_scl & pr_scl;

//--------------------------------------------------------------------------       
    always @(posedge CLK or negedge RST_n) begin
        if (!RST_n)
            begin
                cr_scl <= 1'b0;
                pr_scl <= 1'b0;
                cr_sda <= 1'b0;
                pr_sda <= 1'b0;
            end
        else
            begin
                cr_scl <= I_SCL;
                pr_scl <= cr_scl;
                cr_sda <= sda;
                pr_sda <= cr_sda;
            end
    end


    def_freq_i2c
         #(
         .FPGA_CLK(FPGA_CLK),
         .I2C_CLK(I2C_CLK)
        ) 
    def_freq_i2c    
		  (
         .CLK(CLK), 
         .RST_n(RST_n),
         .I_SCL(I_SCL), 
         .I_RS_IO_SCL(rs_scl),
         .I_FL_IO_SCL(fl_scl),         
         .O_MDL_LW_IO_SCL(mdl_lw_io_scl),
         .O_MDL_HG_IO_SCL(mdl_hg_io_scl)
        );
        
    slv_i2c_fsm
        #(.DATA_SZ(DATA_SZ))
    slv_i2c_fsm
        (
         .CLK(CLK), 
         .RST_n(RST_n), 
         .I_SCL(I_SCL), 
         .I_SDA(sda), 
         .I_RS_IO_SCL(rs_scl), 
         .I_FL_IO_SCL(fl_scl), 
         .I_RS_IO_SDA(rs_sda), 
         .I_FL_IO_SDA(fl_sda), 
         .I_ACK(I_ACK), 
         .I_MDL_LW_IO_SCL(mdl_lw_io_scl), 
         .I_MDL_HG_IO_SCL(mdl_hg_io_scl),
         .O_ADDR_SLV(O_ADDR_SLV), 
         .O_RW(O_RW), 
         .O_DATA_RD(O_DATA_RD), 
         .O_ACK_MSTR(O_ACK_MSTR), 
         .O_SDA(sda_out),
         .O_BUSY(O_BUSY)
        );        
      
        
        
`ifdef COCOTB_SIM
initial begin
  $dumpfile ("top_slv_i2c.vcd2");
  $dumpvars (0, top_slv_i2c);
  #1;
end
`endif
 
endmodule