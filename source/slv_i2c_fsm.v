module slv_i2c_fsm
    #(parameter DATA_SZ = 8) // data widht              
    (CLK, RST_n, I_SCL, I_SDA, I_RS_IO_SCL, I_FL_IO_SCL, I_RS_IO_SDA, I_FL_IO_SDA, I_ACK, I_MDL_LW_IO_SCL, I_MDL_HG_IO_SCL, I_DATA_WR,
     O_ADDR_SLV, O_RW, O_DATA_RD, O_ACK_MSTR, O_BUSY, O_DATA_VL, O_SDA);
     

//--------------------------------------------------------------------------      
    localparam CNT_BIT_DATA_SZ = $clog2(DATA_SZ) + 1; // data width of bit counter  
//  description states FSM
    localparam ST_SZ    = 9; // number of states FSM
    (* syn_encoding = "one-hot" *) reg [ST_SZ-1:0] st; // current state of FSM
    localparam IDLE     = 0; // default state
    localparam START    = 1; // start of a transaction on the I2C bus
    localparam COMM_MSTR = 2; // trasmitter of command from master to the slave
    localparam ACK_COMM = 3; // ACK from the slave to the master
    localparam WR       = 4; // writing data from the slave to the master
    localparam RD       = 6; // reading data from the master to the slave
    localparam MSTR_ACK = 7; // ACK bit data from master
/*  
    localparam ACK_DATA = 5; // ACK bit data from the slave 
                     
    localparam STOP     = 8; // I2C bus stop      */
//  input signals
    input wire               CLK;         // clock 50 MHz
    input wire               RST_n;       // asynchronous reset_n
    input wire               I_SCL;       // serial clock from the master
    input wire               I_SDA;       // serial data from the master
    input wire               I_RS_IO_SCL; // rising edge of IO_SCL
    input wire               I_FL_IO_SCL; // falling edge of IO_SCL
    input wire               I_RS_IO_SDA; // rising edge of IO_SDA
    input wire               I_FL_IO_SDA; // falling edge of IO_SDA
    input wire               I_ACK;       // ACK from the slave to the master
    input wire               I_MDL_LW_IO_SCL; // enable the slave to transmit a bit
    input wire               I_MDL_HG_IO_SCL;
    input wire [DATA_SZ-1:0] I_DATA_WR;   // data for writing to the master
//  output signals
    output reg [DATA_SZ-2:0] O_ADDR_SLV; // addr the slave
    output reg               O_RW;       // RW
    output reg [DATA_SZ-1:0] O_DATA_RD;  // read data from the master
    output reg               O_ACK_MSTR; // ACK from the master
    output reg               O_SDA;      // O_SDA from the slave to the master
    output reg               O_BUSY;
    output reg               O_DATA_VL;
//  internal signals 
    reg [ST_SZ-1:0]           nx_st;           // next state of FSM 
    reg [DATA_SZ-2:0]         nx_o_addr_slv;   // next addr the slave
    reg                       nx_o_rw;         // next RW
    reg [DATA_SZ-1:0]         nx_o_addr_reg;   // next addr reg in the slave
    reg [DATA_SZ-1:0]         nx_o_data_rd;    // next read data from the master
    reg [DATA_SZ-1:0]         buff_rd;         // data buffer of the slave
    reg [DATA_SZ-1:0]         nx_buff_rd;      // next data buffer of the slave    
    reg [CNT_BIT_DATA_SZ-1:0] cnt_bit_data;    // data bit counter
    reg [CNT_BIT_DATA_SZ-1:0] nx_cnt_bit_data; // next data bit counter
    reg                       nx_o_sda;        // next O_SDA from the slave to the mastere
    reg [DATA_SZ-1:0]         comm_slv;        // latched address and read/write
    reg [DATA_SZ-1:0]         nx_comm_slv;     // next latched address and read/write 
    reg                       go;
    reg                       nx_go;
    reg                       nx_o_busy;
    reg                       nx_o_data_vl;
    reg [DATA_SZ-1:0]         buff_wr;
    reg [DATA_SZ-1:0]         nx_buff_wr;
    reg                       nx_o_ack_mstr; // ACK from the master
    reg                       ch;
    reg                       nx_ch;
/* //  internal signals 
    reg [COMM_SZ-1:0]         sh_reg;          // shift reg
    reg [COMM_SZ-1:0]         nx_sh_reg;       // shift reg
    reg [DATA_SZ-1:0]         data_wr;         // latched data for writing to the slave
    reg [DATA_SZ-1:0]         nx_data_wr;      // next latched data for writing to the slave 
    reg                       data_o_sda;      // data for SDA transmitting 
    reg                       nx_data_o_sda;   // next data for SDA transmitting
    wire                      nx_o_scl;        // next serial clock  I2C bus
    reg                       en_o_scl;        // enables I_SCL to output in I2C bus
    reg                       nx_en_o_scl;     // next enables I_SCL to output in I2C bus
    reg                       nx_o_ack_fl;     // next flag ACK from the slave (if hight, error)*/   
 
//  determining next state of FSM and signals
    always @(*) begin
        nx_st = st;
        nx_buff_rd = buff_rd; 
        nx_cnt_bit_data = cnt_bit_data;
        nx_o_data_rd = O_DATA_RD;
        nx_o_addr_slv = O_ADDR_SLV;
        nx_o_rw = O_RW;
        nx_o_sda = O_SDA;
        nx_comm_slv = comm_slv;
        nx_go = go;
        nx_o_busy = O_BUSY;
        nx_o_data_vl = O_DATA_VL;
        nx_buff_wr = buff_wr;
        nx_o_ack_mstr = O_ACK_MSTR;
        nx_ch = ch;
/*       
      nx_data_o_sda = O_SDA;
      nx_o_ack_fl = O_ACK_FL;
      nx_comm_slv = comm_slv;
      nx_sh_reg = sh_reg;
      nx_data_wr = data_wr;  
      nx_en_o_scl = en_o_scl; */
        case (st)    
            IDLE     :  begin
                            if (I_FL_IO_SDA & I_SCL)
                                begin
                                    nx_st = START;
                                    nx_o_busy = 1'b1;
                                end
                        end
            START    :  begin   
                            if (I_RS_IO_SCL)
                                begin
                                    nx_cnt_bit_data = DATA_SZ - 1'b1;
                                    nx_buff_rd = {nx_buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_st = COMM_MSTR;
                                end
                        end
            COMM_MSTR : begin
                            if (I_RS_IO_SCL)
                                begin
                                    nx_buff_rd = {nx_buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_cnt_bit_data = cnt_bit_data - 1'b1;
                                end
                            if (&(!cnt_bit_data))
                                begin
                                    nx_comm_slv = buff_rd;
                                    nx_o_addr_slv = buff_rd[DATA_SZ-1:1];
                                    nx_o_rw = buff_rd[0];
                                    nx_o_data_vl = 1'b1;
                                    if (I_MDL_LW_IO_SCL)
                                        begin
                                            nx_cnt_bit_data = DATA_SZ - 1'b1;
                                            nx_o_sda = I_ACK;
                                            nx_go = 1'b1;
                                            nx_st = ACK_COMM;
                                            nx_o_data_vl = 1'b0;
                                        end
                                end
                        end
            ACK_COMM :  begin
                            if (I_FL_IO_SCL)
                                nx_o_sda = 1'b1;
                            if (I_MDL_LW_IO_SCL)
                                begin
                                    nx_go = 1'b0;
                                    if (comm_slv[0])
                                        begin
                                            nx_buff_wr = {I_DATA_WR[DATA_SZ-2:0], 1'b0};
                                            nx_o_sda = I_DATA_WR[DATA_SZ-1];
                                            nx_st = WR;
                                        end
                                end
                            if (I_RS_IO_SDA & I_SCL)
                                begin
                                    nx_o_busy = 1'b0;
                                    nx_o_data_vl = 1'b0;
                                    nx_st = IDLE;
                                end
                            if (I_FL_IO_SCL & !go)
                                begin
                                    nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_cnt_bit_data = DATA_SZ - 1'b1;
                                    nx_st = RD;
                                end
                            
                        end
            RD       :  begin
                            if (I_RS_IO_SCL)
                                begin
                                    nx_buff_rd = {nx_buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_cnt_bit_data = cnt_bit_data - 1'b1;
                                end
                            if (&(!cnt_bit_data))
                                begin
                                    nx_o_data_rd = buff_rd;
                                    nx_o_data_vl = 1'b1;
                                    if (I_MDL_LW_IO_SCL)
                                        begin
                                            nx_cnt_bit_data = DATA_SZ - 1'b1;
                                            nx_o_sda = I_ACK;
                                            nx_go = 1'b1;
                                            nx_o_data_vl = 1'b0;
                                            nx_st = ACK_COMM;
                                        end
                                end
                        end
            WR       :  begin
                            if (I_MDL_LW_IO_SCL)
                                begin
                                    nx_o_sda = buff_wr[DATA_SZ-1];
                                    nx_buff_wr = {buff_wr[DATA_SZ-2:0], 1'b0};
                                    nx_cnt_bit_data = cnt_bit_data - 1'b1;
                                end
                            if (&(!cnt_bit_data))
                                begin
                                    nx_st = MSTR_ACK;
                                    nx_cnt_bit_data = DATA_SZ - 1'b1;
                                end
                        end
            MSTR_ACK :  begin
                            if (I_MDL_LW_IO_SCL)
                                begin
                                    nx_o_sda = 1'b1;
                                end
                            if (I_RS_IO_SCL)
                                begin
                                    nx_o_ack_mstr = I_SDA;
                                    if (I_SDA)
                                        begin
                                            nx_st = IDLE;
                                        end
                                    else
                                        begin
                                            nx_st = WR;
                                        end
                                end
                        end
            default  :  begin
                            nx_st = IDLE;
                            nx_o_sda = 1'b1;
                            // nx_cnt_bit_data = {CNT_BIT_DATA_SZ{1'b0}};
                            // nx_buff_rd = {DATA_SZ{1'b0}}; 
                            // nx_o_data_rd = {DATA_SZ{1'b0}};;
                            // nx_o_addr_slv = O_ADDR_SLV;
                            // nx_o_rw = O_RW;
                            // nx_comm_slv = comm_slv;
                            // nx_go = go;      
                            // nx_buff_wr = {DATA_SZ{1'b0}};
                        end 
        endcase
    end

//  latching the next state of FSM and signals, every clock
    always @(posedge CLK or negedge RST_n) begin
        if (!RST_n) 
            begin
                st       <= IDLE;
                buff_rd  <= {DATA_SZ{1'b0}};
                cnt_bit_data <= {CNT_BIT_DATA_SZ{1'b0}};
                O_DATA_RD <= {DATA_SZ{1'b0}};
                O_ADDR_SLV <= {DATA_SZ-1{1'b0}};
                O_RW <= 1'b0;
                O_SDA    <= 1'b1;
                comm_slv <= {DATA_SZ{1'b0}};
                go <= 1'b0;
                O_BUSY <= 1'b0;
                O_DATA_VL <= 1'b0;
                buff_wr <= {DATA_SZ{1'b0}};
                O_ACK_MSTR <= 1'b0;
                ch <= 1'b0;
            end
        else 
            begin
                st       <= nx_st;
                buff_rd  <= nx_buff_rd;
                cnt_bit_data <= nx_cnt_bit_data;
                O_DATA_RD    <= nx_o_data_rd;
                O_ADDR_SLV <= nx_o_addr_slv;
                O_RW <= nx_o_rw;
                O_SDA    <= nx_o_sda; 
                comm_slv <= nx_comm_slv;
                go <= nx_go;
                O_BUSY <= nx_o_busy;
                O_DATA_VL <= nx_o_data_vl;
                buff_wr <= nx_buff_wr;
                O_ACK_MSTR <= nx_o_ack_mstr;
                ch <= nx_ch;
            end
    end


endmodule           