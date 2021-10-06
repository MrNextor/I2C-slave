# test_top_slv_i2c.py

import cocotb
import random
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue


I2C_CLK  = 100e3;
I2C_CLK_1_2 = 100e3 * 2;
I2C_CLK_1_4 = 100e3 * 4;

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
    data = BinaryValue();
    # data_from_slv = 0;
    await ClockCycles(dut.CLK, 2, rising=False) 

#--------------------------------------------------------------------------   
# start the first transaction
    addr = random.randrange(0, 2**7); rw = 0; 
    data.binstr = addr_rw_to_str(addr, rw);
    data.binstr = add_zero(data.binstr);
    # start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut.I_SCL, dut.IO_SDA, data.binstr, dut.I_ACK)
    assert dut.slv_i2c_fsm.buff_rd.value == data, "buff_rd was incorrect on the {} data for write1_1".format(data)  
    # transfer addr_reg    
    data.integer = random.randrange(0, 2**8);
    data.binstr = add_zero(data.binstr);
    await transaction(dut.I_SCL, dut.IO_SDA, data.binstr)
    assert dut.slv_i2c_fsm.buff_rd.value == data, "buff_rd was incorrect on the {} data for write1_2".format(data)
    # ACK from slave    
    await ack_slv(dut.I_ACK, dut.I_SCL)
    # stop I2C
    await stop_i2c(dut.I_SCL, dut.IO_SDA)
    await Timer(1 / I2C_CLK_1_2, units="sec")     
 
#--------------------------------------------------------------------------    
# start the second transaction 
    addr = random.randrange(0, 2**7); rw = 0; 
    data.binstr = addr_rw_to_str(addr, rw);
    data.binstr = add_zero(data.binstr);
# start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut.I_SCL, dut.IO_SDA, data.binstr, dut.I_ACK)
    assert dut.slv_i2c_fsm.buff_rd.value == data, "buff_rd was incorrect on the {} data for write2_1".format(data)  
    # transfer addr reg    
    data.integer = random.randrange(0, 2**8);
    data.binstr = add_zero(data.binstr);
    await transaction(dut.I_SCL, dut.IO_SDA, data.binstr)
    assert dut.slv_i2c_fsm.buff_rd.value == data, "buff_rd was incorrect on the {} data for write2_2".format(data)
    # ACK from slave    
    await ack_slv(dut.I_ACK, dut.I_SCL)
    # transfer data  
    data.integer = random.randrange(0, 2**8);
    data.binstr = add_zero(data.binstr);
    await transaction(dut.I_SCL, dut.IO_SDA, data.binstr)
    assert dut.slv_i2c_fsm.buff_rd.value == data, "buff_rd was incorrect on the {} data for write2_3".format(data)
    # ACK from slave    
    await ack_slv(dut.I_ACK, dut.I_SCL)
    # stop I2C
    await stop_i2c(dut.I_SCL, dut.IO_SDA)
    await Timer(1 / I2C_CLK_1_2, units="sec")



#--------------------------------------------------------------------------   
# start the third transaction    
    addr = random.randrange(0, 2**7); rw = 1; 
    data.binstr = addr_rw_to_str(addr, rw);
    data.binstr = add_zero(data.binstr);
    # start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut.I_SCL, dut.IO_SDA, data.binstr, dut.I_ACK)
    assert dut.slv_i2c_fsm.buff_rd.value == data, "buff_rd was incorrect on the {} data for write3_1".format(data)  
    
    # transfer data from slave    
    dut.I_DATA_WR = random.randrange(2**7, 2**8);
    await wr_slv(dut.I_SCL)
    
    await Timer(1 / I2C_CLK_1_2, units="sec")
#--------------------------------------------------------------------------  

    
async def start_tr_addr_ack(IO_SCL, IO_SDA, addr_rw, ack):
    await start_i2c(IO_SCL, IO_SDA)            # start I2C
    await transaction(IO_SCL, IO_SDA, addr_rw) # transfer addr and rw  
    await ack_slv(ack, IO_SCL)                 # ACK from slave  

async def start_i2c(IO_SCL, IO_SDA):
    IO_SDA <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")    
    
async def transaction(IO_SCL, IO_SDA, data): 
    for i in data:
        IO_SDA <= int(i);
        await Timer(1 / I2C_CLK_1_4, units="sec")
        IO_SCL <= 1;
        await Timer(1 / I2C_CLK_1_2, units="sec")
        IO_SCL <= 0;
        await Timer(1 / I2C_CLK_1_4, units="sec")

async def ack_slv(ack, IO_SCL):
    ack <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 1;
    await Timer(1 / I2C_CLK_1_2, units="sec")
    IO_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    
async def stop_i2c(IO_SCL, IO_SDA):
    IO_SDA <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SCL <= 1;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    IO_SDA <= 1;

async def wr_slv(IO_SCL): 
    for i in range(8):
        await Timer(1 / I2C_CLK_1_4, units="sec")
        IO_SCL <= 1;
        await Timer(1 / I2C_CLK_1_2, units="sec")
        IO_SCL <= 0;
        await Timer(1 / I2C_CLK_1_4, units="sec")

def addr_rw_to_str(addr, rw):
    data = format(addr, 'b') + format(rw, 'b');
    return data;
    
def add_zero(data):    
    if len(data) < 8:
        need = 8 - len(data);
        data = list(data);
        for i in range(need):
           data.insert(i, '0')
        string = '';
        for i in data:
            string += i
        data = string
    return data