module slv_i2c_fsm
    #(parameter DATA_SZ = 8) // data widht              
    (CLK, RST_n, I_SCL, I_SDA, I_RS_IO_SCL, I_FL_IO_SCL, I_RS_IO_SDA, I_FL_IO_SDA, I_ACK, I_MDL_LW_IO_SCL, I_DATA_WR,
     O_ADDR_SLV, O_RW, O_ADDR_REG, O_DATA_RD,  O_SDA, O_BUSY, O_CH_CNCT, O_DATA_VL);
     

//--------------------------------------------------------------------------      
    localparam CNT_BIT_DATA_SZ = $clog2(DATA_SZ) + 1; // data width of bit counter  
//  description states FSM
    localparam ST_SZ     = 9; // number of states FSM
    (* syn_encoding = "one-hot" *) reg [ST_SZ-1:0] st; // current state of FSM
    localparam IDLE      = 0; // default state
    localparam START     = 1; // start of a transaction on the I2C bus
    localparam COMM_MSTR = 2; // trasmitter of command from the master to the slave
    localparam ACK_COMM  = 3; // ACK bit comnmand from the slave to the master
    localparam ADDR_REG  = 4; // addr_reg in the slave
    localparam ACK_DATA  = 5; // ACK bit data from the slave to the master
    localparam WR        = 6; // writing data from the slave to the master
    localparam RD        = 7; // reading data from the master to the slave
    localparam MSTR_ACK  = 8; // ACK bit data from master
//  input signals
    input wire               CLK;             // clock 50 MHz
    input wire               RST_n;           // asynchronous reset_n
    input wire               I_SCL;           // serial clock from the master
    input wire               I_SDA;           // serial data from the master
    input wire               I_RS_IO_SCL;     // rising edge of IO_SCL
    input wire               I_FL_IO_SCL;     // falling edge of IO_SCL
    input wire               I_RS_IO_SDA;     // rising edge of IO_SDA
    input wire               I_FL_IO_SDA;     // falling edge of IO_SDA
    input wire               I_ACK;           // ACK from the slave to the master
    input wire               I_MDL_LW_IO_SCL; // enable the slave to transmit a bit
    input wire [DATA_SZ-1:0] I_DATA_WR;       // data for writing to the master
//  output signals
    output reg [DATA_SZ-2:0] O_ADDR_SLV; // addr the slave
    output reg               O_RW;       // RW
    output reg [DATA_SZ-1:0] O_ADDR_REG; // addr reg of the slave
    output reg [DATA_SZ-1:0] O_DATA_RD;  // read data from the master
    output reg               O_SDA;      // O_SDA from the slave to the master
    output reg               O_BUSY;     // busy slave
    output reg               O_CH_CNCT;  // check connection
    output reg               O_DATA_VL;  // valid data
//  internal signals 
    reg [ST_SZ-1:0]           nx_st;           // next state of FSM 
    reg [DATA_SZ-2:0]         nx_o_addr_slv;   // next addr the slave
    reg                       nx_o_rw;         // next RW
    reg [DATA_SZ-1:0]         nx_o_addr_reg;   // next addr_reg in the slave
    reg [DATA_SZ-1:0]         nx_o_data_rd;    // next read data from the master
    reg                       nx_o_sda;        // next O_SDA from the slave to the master
    reg                       nx_o_busy;       // nest busy slave
    reg                       nx_o_ch_cnct;    // next check connection
    reg                       nx_o_data_vl;    // next valid data
    reg [DATA_SZ-1:0]         buff_rd;         // data buffer of the slave
    reg [DATA_SZ-1:0]         nx_buff_rd;      // next data buffer of the slave    
    reg [DATA_SZ-1:0]         buff_wr;         // buffer for writting
    reg [DATA_SZ-1:0]         nx_buff_wr;      // next buffer for writting
    reg [CNT_BIT_DATA_SZ-1:0] cnt_bit_data;    // data bit counter
    reg [CNT_BIT_DATA_SZ-1:0] nx_cnt_bit_data; // next data bit counter
    reg [DATA_SZ-1:0]         comm_slv;        // latched address and read/write
    reg [DATA_SZ-1:0]         nx_comm_slv;     // next latched address and read/write 
    reg [DATA_SZ-1:0]         pr_comm_slv;
    reg [DATA_SZ-1:0]         nx_pr_comm_slv;
    reg [DATA_SZ-1:0]         pr_addr_reg;
    reg [DATA_SZ-1:0]         nx_pr_addr_reg;
    reg [DATA_SZ-1:0]         addr_reg_offset;
    reg [DATA_SZ-1:0]         nx_addr_reg_offset;
    reg                       ack_from_slave;
    reg                       nx_ack_from_slave;
    reg                       go;
    reg                       nx_go;
 
//  determining next state of FSM and signals
    always @(*) begin
        nx_st = st;
        nx_o_addr_slv = O_ADDR_SLV;
        nx_o_rw = O_RW;
        nx_o_addr_reg = O_ADDR_REG;
        nx_o_data_rd = O_DATA_RD;
        nx_o_sda = O_SDA;
        nx_o_busy = O_BUSY;
        nx_o_ch_cnct = O_CH_CNCT;
        nx_o_data_vl = O_DATA_VL;
        nx_buff_rd = buff_rd; 
        nx_buff_wr = buff_wr;
        nx_cnt_bit_data = cnt_bit_data;
        nx_comm_slv = comm_slv;
        nx_pr_comm_slv = pr_comm_slv;
        nx_pr_addr_reg = pr_addr_reg;
        nx_addr_reg_offset = addr_reg_offset;
        nx_ack_from_slave = ack_from_slave;
        nx_go = go;
        case (st)    
            IDLE     :  begin
                            if (I_FL_IO_SDA & I_SCL)
                                begin
                                    nx_o_busy = 1'b1;
                                    nx_st = START;
                                end
                        end
            START    :  begin   
                            if (I_RS_IO_SCL)
                                begin
                                    nx_cnt_bit_data = DATA_SZ - 1'b1;
                                    nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_st = COMM_MSTR;
                                end
                        end
            COMM_MSTR : begin
                            if (I_RS_IO_SCL)
                                begin
                                    nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_cnt_bit_data = cnt_bit_data - 1'b1;
                                end
                            if (&(!cnt_bit_data))
                                begin
                                    nx_comm_slv = buff_rd;
                                    nx_o_rw = buff_rd[0];
                                    nx_o_ch_cnct = 1'b1;
                                    nx_o_addr_slv = buff_rd[DATA_SZ-1:1];
                                    if ({pr_comm_slv[DATA_SZ-1:1], 1'b1} == buff_rd)
                                        begin
                                            nx_o_addr_reg = pr_addr_reg;
                                            nx_o_data_vl = 1'b1;
                                        end
                                    if (I_MDL_LW_IO_SCL)
                                        begin
                                            nx_cnt_bit_data = DATA_SZ - 1'b1;
                                            nx_o_sda = I_ACK;
                                            nx_ack_from_slave = I_ACK;
                                            nx_go = 1'b1;
                                            nx_o_ch_cnct = 1'b0;
                                            nx_o_data_vl = 1'b0;
                                            nx_st = ACK_COMM;
                                        end
                                end
                        end
            ACK_COMM :  begin
                            if (I_MDL_LW_IO_SCL)
                                begin
                                    nx_go = 1'b0;
                                    nx_o_sda = 1'b1;
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
                                    nx_st = IDLE;
                                end
                            if (I_FL_IO_SCL & !go)
                                begin
                                    nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_st = ADDR_REG;
                                end
                        end
            ADDR_REG :  begin
                            if (I_RS_IO_SCL)
                                begin
                                    nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_cnt_bit_data = cnt_bit_data - 1'b1;
                                end
                            if (&(!cnt_bit_data))
                                begin
                                    nx_o_addr_reg = buff_rd;
                                    nx_addr_reg_offset = {DATA_SZ{1'b0}};
                                    if (I_MDL_LW_IO_SCL)
                                        begin
                                            nx_cnt_bit_data = DATA_SZ - 1'b1;
                                            nx_o_sda = ack_from_slave;
                                            nx_go = 1'b1;
                                            nx_st = ACK_DATA;
                                        end
                                end
                        end
            ACK_DATA :  begin
                            if (I_MDL_LW_IO_SCL)
                                begin
                                    nx_go = 1'b0;
                                    nx_o_sda = 1'b1; 
                                end
                            if (I_RS_IO_SDA & I_SCL)
                                begin
                                    nx_o_busy = 1'b0;
                                    nx_pr_addr_reg = O_ADDR_REG;
                                    nx_pr_comm_slv = comm_slv;
                                    nx_st = IDLE;
                                end
                            if (I_FL_IO_SCL & !go)
                                begin
                                    if (comm_slv[0])
                                        begin
                                            nx_buff_wr = {I_DATA_WR[DATA_SZ-2:0], 1'b0};
                                            nx_o_sda = I_DATA_WR[DATA_SZ-1];
                                            nx_st = WR;
                                        end
                                    else 
                                        begin
                                            nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                            nx_st = RD;
                                        end
                                end
                        end       
            RD       :  begin
                            if (I_RS_IO_SCL)
                                begin
                                    nx_buff_rd = {buff_rd[DATA_SZ-2:0], I_SDA};
                                    nx_cnt_bit_data = cnt_bit_data - 1'b1;
                                end
                            if (&(!cnt_bit_data))
                                begin
                                    nx_o_addr_reg = &(!addr_reg_offset) ? O_ADDR_REG : addr_reg_offset;
                                    nx_o_data_rd = buff_rd;
                                    nx_o_data_vl = 1'b1;
                                    if (I_MDL_LW_IO_SCL)
                                        begin
                                            nx_cnt_bit_data = DATA_SZ - 1'b1;
                                            nx_o_sda = ack_from_slave;
                                            nx_go = 1'b1;
                                            nx_o_data_vl = 1'b0;
                                            nx_st = ACK_DATA;
                                            nx_addr_reg_offset = O_ADDR_REG + 1'b1;
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
                                    if (I_MDL_LW_IO_SCL)
                                        begin
                                            nx_cnt_bit_data = DATA_SZ - 1'b1;
                                            nx_o_sda = 1'b1;
                                            nx_st = MSTR_ACK;
                                        end
                                end
                        end
            MSTR_ACK :  begin
                            if (I_RS_IO_SCL)
                                begin
                                    if (I_SDA)
                                        begin
                                            nx_o_busy = 1'b0;
                                            nx_st = IDLE;
                                        end
                                    else
                                        begin
                                            nx_o_addr_reg = O_ADDR_REG + 1'b1;
                                            nx_o_data_vl = 1'b1;                                        
                                        end  
                                end
                            if (I_MDL_LW_IO_SCL)
                                begin
                                    nx_buff_wr = {I_DATA_WR[DATA_SZ-2:0], 1'b0};
                                    nx_o_sda = I_DATA_WR[DATA_SZ-1];
                                    nx_o_data_vl = 1'b0;
                                    nx_st = WR;
                                end
                        end
            default  :  begin
                            nx_st = IDLE;
                            nx_o_sda = 1'b1;
                            nx_o_busy = 1'b0;
                            nx_o_data_vl = 1'b0;
                            pr_comm_slv = {DATA_SZ{1'b0}};
                            nx_ack_from_slave = 1'b1;
                        end 
        endcase
    end

//  latching the next state of FSM and signals, every clock
    always @(posedge CLK or negedge RST_n) begin
        if (!RST_n) 
            begin
                st              <= IDLE;
                O_ADDR_SLV      <= {DATA_SZ-1{1'b0}};
                O_RW            <= 1'b0;
                O_ADDR_REG      <= {DATA_SZ{1'b0}};
                O_DATA_RD       <= {DATA_SZ{1'b0}};
                O_SDA           <= 1'b1;
                O_BUSY          <= 1'b0;
                O_CH_CNCT       <= 1'b0;
                O_DATA_VL       <= 1'b0;
                buff_rd         <= {DATA_SZ{1'b0}};
                buff_wr         <= {DATA_SZ{1'b0}};
                cnt_bit_data    <= {CNT_BIT_DATA_SZ{1'b0}};
                comm_slv        <= {DATA_SZ{1'b0}};
                pr_comm_slv     <= {DATA_SZ{1'b0}};
                pr_addr_reg     <= {DATA_SZ{1'b0}}; 
                addr_reg_offset <= {DATA_SZ{1'b0}};
                ack_from_slave  <= 1'b1;
                go              <= 1'b0;
            end
        else 
            begin
                st              <= nx_st;
                O_ADDR_SLV      <= nx_o_addr_slv;
                O_RW            <= nx_o_rw;
                O_ADDR_REG      <= nx_o_addr_reg;
                O_DATA_RD       <= nx_o_data_rd;
                O_SDA           <= nx_o_sda; 
                O_BUSY          <= nx_o_busy;
                O_CH_CNCT       <= nx_o_ch_cnct;
                O_DATA_VL       <= nx_o_data_vl;
                buff_rd         <= nx_buff_rd;
                buff_wr         <= nx_buff_wr;
                cnt_bit_data    <= nx_cnt_bit_data;
                comm_slv        <= nx_comm_slv;
                pr_comm_slv     <= nx_pr_comm_slv;
                pr_addr_reg     <= nx_pr_addr_reg;
                addr_reg_offset <= nx_addr_reg_offset;
                ack_from_slave  <= nx_ack_from_slave;
                go              <= nx_go;
            end
    end


endmodule           