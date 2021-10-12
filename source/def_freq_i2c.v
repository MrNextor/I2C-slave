module def_freq_i2c
    #(parameter FPGA_CLK = 50_000_000,         // FPGA frequency 50 MHz
      parameter I2C_CLK  = 100_000,            // minimum frequency of I2C bus (100 KHz)
      parameter NUM_CYC  = FPGA_CLK / I2C_CLK, // maximum number of cycles
      parameter CNT_SZ   = $clog2(NUM_CYC))    // width of clock counter
    (CLK, RST_n, I_SCL, I_RS_IO_SCL, I_FL_IO_SCL,
     O_MDL_LW_IO_SCL, O_MDL_HG_IO_SCL);


//  input signals
    input wire CLK;         // clock 50 MHz
    input wire RST_n;       // asynchronous reset_n
    input wire I_SCL;       // serial clock from the I2C_master'
    input wire I_RS_IO_SCL; // rising edge of IO_SCL
    input wire I_FL_IO_SCL; // falling edge of IO_SCL
//  output signals
    output reg O_MDL_LW_IO_SCL; // middle of HIGH IO_SCL
    output reg O_MDL_HG_IO_SCL; // middle of LOW IO_SCL
//  internal signals
    reg [CNT_SZ-1:0] cnt;    // clock counter
    reg [CNT_SZ-1:0] sv_cnt; // current value of the clock counter
    wire             en_str; // enable strobe O_MDL_LW_IO_SCL or O_MDL_HG_IO_SCL

//--------------------------------------------------------------------------
    assign en_str = cnt == (sv_cnt >> 1'b1) & (cnt > 1'b0);

//--------------------------------------------------------------------------
    always @(posedge CLK or negedge RST_n) begin
        if (!RST_n)
            begin
                cnt <= {CNT_SZ{1'b0}};
                sv_cnt <= {CNT_SZ{1'b0}};
                O_MDL_LW_IO_SCL <= 1'b0;
                O_MDL_HG_IO_SCL <= 1'b0;
            end
        else
            begin
                cnt <= I_FL_IO_SCL || I_RS_IO_SCL ? {CNT_SZ{1'b0}} : cnt + 1'b1;
                sv_cnt <= I_FL_IO_SCL ? cnt : sv_cnt;
                O_MDL_LW_IO_SCL <= !I_SCL & en_str ? 1'b1 : 1'b0;
                O_MDL_HG_IO_SCL <= I_SCL & en_str ? 1'b1 : 1'b0;
            end
    end


endmodule