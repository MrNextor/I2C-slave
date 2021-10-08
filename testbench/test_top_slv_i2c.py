# test_top_slv_i2c.py

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer
from cocotb.binary import BinaryValue

#--------------------------------------------------------------------------
I2C_CLK  = 100e3;
I2C_CLK_1_2 = 100e3 * 2;
I2C_CLK_1_4 = 100e3 * 4;

#--------------------------------------------------------------------------
@cocotb.test()
async def test_top_slv_i2c(dut):
    """ Test def_freq_i2c.v """

#--------------------------------------------------------------------------      
# Create a 20ns period clock on port CLK
    clock_clk = Clock(dut.CLK, 20, units="ns") # Create a 20ns period clock on port CLK
    cocotb.fork(clock_clk.start())             # Start the CLK

#--------------------------------------------------------------------------   
# async reset
    dut.RST_n <= 1;
    await FallingEdge(dut.CLK)
    dut.RST_n <= 0;
    cocotb.log.info("RST_n is still active: %d" % dut.RST_n)
    await ClockCycles(dut.CLK, 2, rising=False)
    dut.RST_n <= 1;
    cocotb.log.info("RST_n has gone inactive: %d" % dut.RST_n)

#--------------------------------------------------------------------------       
# initial values
    dut.I_SCL <= 1; 
    dut.IO_SDA <= 1;
    comm_slv = BinaryValue();
    addr_slv = BinaryValue();
    addr_reg = BinaryValue();
    data = BinaryValue();
    data_from_slv_before = 0;
    data_from_slv_after = 0;
    await ClockCycles(dut.CLK, 2, rising=False) 

#--------------------------------------------------------------------------   
# start the first transaction, writting of two bytes
    addr_slv = addr = random.randrange(0, 2**7); rw = 0; 
    comm_slv.binstr = addr_rw_to_str(addr, rw);
    comm_slv.binstr = add_zero(comm_slv.binstr);
# start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut.I_SCL, dut.IO_SDA, comm_slv.binstr, dut.I_ACK, dut.O_CH_CNCT) 
# transfer addr_reg    
    addr_reg.integer = random.randrange(0, 2**8);
    addr_reg.binstr = add_zero(addr_reg.binstr);
    await Timer(60, units="ns")
    await transaction(dut.I_SCL, dut.IO_SDA, addr_reg.binstr)
# ACK from slave
    await ack_slv(dut.I_SCL)
# transfer data 
    i = 0; num_byte = 2;
    while i < num_byte:
        data.integer = random.randrange(0, 2**8);
        data.binstr = add_zero(data.binstr);
        await Timer(60, units="ns")
        await transaction(dut.I_SCL, dut.IO_SDA, data.binstr)
        check_writting(dut.O_ADDR_SLV.value, addr_slv, dut.O_RW.value, rw, dut.O_ADDR_REG.value, addr_reg, dut.O_DATA_RD.value, data, dut.O_DATA_VL, i)
        await ack_slv(dut.I_SCL)
        i += 1;
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut.I_SCL, dut.IO_SDA)
    await Timer(1 / I2C_CLK_1_2, units="sec")     


#--------------------------------------------------------------------------      
async def start_tr_addr_ack(IO_SCL, IO_SDA, addr_rw, ack, O_CH_CNCT):
    await start_i2c(IO_SCL, IO_SDA)            # start I2C
    await transaction(IO_SCL, IO_SDA, addr_rw) # transfer addr and rw  
    assert O_CH_CNCT == 1, "O_CH_CNCT was incorrect 1"
    await ack_start(ack, IO_SCL)               # ACK from slave     

#--------------------------------------------------------------------------    
async def start_i2c(IO_SCL, IO_SDA):
    IO_SDA <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")    

#--------------------------------------------------------------------------        
async def transaction(IO_SCL, IO_SDA, data): 
    for i in data:
        IO_SDA <= int(i);
        await Timer(1 / I2C_CLK_1_4, units="sec")
        IO_SCL <= 1;
        await Timer(1 / I2C_CLK_1_2, units="sec")
        IO_SCL <= 0;
        await Timer(1 / I2C_CLK_1_4, units="sec")

#--------------------------------------------------------------------------    
async def ack_start(ack, IO_SCL):
    ack <= 0;
    await ack_slv(IO_SCL)
    
#-------------------------------------------------------------------------- 
async def ack_slv(IO_SCL):
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 1;
    await Timer(1 / I2C_CLK_1_2, units="sec")
    IO_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")

#--------------------------------------------------------------------------        
async def stop_i2c(IO_SCL, IO_SDA):
    IO_SDA <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 1;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SDA <= 1;

#--------------------------------------------------------------------------    
async def wr_slv(IO_SCL, IO_SDA): 
    data_from_slv = [];
    string = "";
    for i in range(8):
        await Timer(1 / I2C_CLK_1_4, units="sec")
        IO_SCL <= 1; what_save(IO_SDA, data_from_slv)
        await Timer(1 / I2C_CLK_1_2, units="sec")
        IO_SCL <= 0;
        await Timer(1 / I2C_CLK_1_4, units="sec")
    for i in data_from_slv:
        string += str(i);
    data_from_slv = int((string), base=2);
    return data_from_slv;

#--------------------------------------------------------------------------    
async def mstr_ack(IO_SCL, IO_SDA, ack_mstr):
    IO_SDA <= ack_mstr;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 1;
    await Timer(1 / I2C_CLK_1_2, units="sec")
    IO_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SDA <= 1;

#--------------------------------------------------------------------------        
def what_save(IO_SDA, data_from_slv):
    if IO_SDA.value.binstr == "z" or IO_SDA == 1:
        data_from_slv.append(1)
    else:
        data_from_slv.append(0)
    return data_from_slv;

#--------------------------------------------------------------------------    
def addr_rw_to_str(addr, rw):
    data = format(addr, "b") + format(rw, "b");
    return data;

#--------------------------------------------------------------------------        
def add_zero(data):    
    if len(data) < 8:
        need = 8 - len(data);
        data = list(data);
        for i in range(need):
           data.insert(i, "0")
        string = "";
        for i in data:
            string += i;
        data = string
    return data
   
def check_writting(O_ADDR_SLV, addr_slv, O_RW, rw, O_ADDR_REG, addr_reg, O_DATA_RD, data, O_DATA_VL, i):
    assert O_ADDR_SLV == addr_slv, "O_ADDR_SLV was incorrect on the {} addr_slv for write in {} loop" .format(addr_slv, i)
    assert O_RW == rw, "O_RW was incorrect on the {} rw for write in {} loop" .format(rw, i)
    assert O_ADDR_REG == addr_reg + i, "O_ADDR_REG was incorrect on the {} addr_reg for write in {} loop" .format(addr_reg, i)
    assert O_DATA_RD == data, "O_DATA_RD was incorrect on the {} data for write in {} loop" .format(data, i)
    assert O_DATA_VL == 1, "O_DATA_VL was incorrect 1 in {} loop" .format(i)      