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
    data_from_slv_before = BinaryValue();
    await ClockCycles(dut.CLK, 2, rising=False) 

#--------------------------------------------------------------------------   
# start the first transaction, writting of two bytes
    addr_slv = addr = random.randrange(0, 2**7); rw = 0; 
    comm_slv.binstr = addr_rw_to_str(addr, rw);
    comm_slv.binstr = add_zero(comm_slv.binstr);
# start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut, comm_slv.binstr, addr_slv, rw, addr_reg, data) 
# transfer addr_reg    
    addr_reg.integer = random.randrange(0, 2**8);
    addr_reg.binstr = add_zero(addr_reg.binstr);
    await Timer(60, units="ns")
    await transaction(dut, addr_reg.binstr)
# ACK from slave
    await ack_slv(dut)
# transfer data 
    i = 0; num_byte = 2;
    while i < num_byte:
        data.integer = random.randrange(0, 2**8);
        data.binstr = add_zero(data.binstr);
        await Timer(60, units="ns")
        await transaction(dut, data.binstr)
        check_writting(dut, addr_slv, rw, addr_reg, data, i)
        await ack_slv(dut)
        i += 1;
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut)
    await Timer(1 / I2C_CLK_1_2, units="sec")     

#--------------------------------------------------------------------------   
# start the second transaction, reading of two bytes
    addr_slv = addr = random.randrange(0, 2**7); rw = 0; 
    comm_slv.binstr = addr_rw_to_str(addr, rw);
    comm_slv.binstr = add_zero(comm_slv.binstr);
# start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut, comm_slv.binstr, addr_slv, rw, addr_reg, data)  
# transfer addr_reg    
    addr_reg.integer = random.randrange(0, 2**8);
    addr_reg.binstr = add_zero(addr_reg.binstr);
    await Timer(60, units="ns")
    await transaction(dut, addr_reg.binstr)
# ACK from slave
    await ack_slv(dut)
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut)
    await Timer(1 / I2C_CLK_1_2, units="sec") 
    rw = 1;
    comm_slv.binstr = addr_rw_to_str(addr, rw);
    comm_slv.binstr = add_zero(comm_slv.binstr);
# start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr_ack(dut, comm_slv.binstr, addr_slv, rw, addr_reg, data) 
# transfer data 
    i = 0; num_byte = 2;
    data_from_slv_after = 0;
    ack_mstr = 0;
    while i < num_byte:
        data_from_slv_before.integer = random.randrange(0, 2**8);
        data_from_slv_before.binstr = add_zero(data.binstr);
        dut.I_DATA_WR = data_from_slv_before;
        data_from_slv_after = await wr_slv(dut)
        assert data_from_slv_before == data_from_slv_after, "Read the data was incorrect {} written the data in {} loop".format(data_from_slv_after, i)  
        if i != num_byte - 1:
            ack_mstr = 0;
        else:
            ack_mstr = 1;
        await Timer(60, units="ns")
        await mstr_ack(dut, ack_mstr, addr_slv, rw, addr_reg, i)
        i += 1;
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut)
    await Timer(1 / I2C_CLK_1_2, units="sec")  


#--------------------------------------------------------------------------      
async def start_tr_addr_ack(dut, comm_slv, addr_slv, rw, addr_reg, data):
    await start_i2c(dut)             # start I2C
    await transaction(dut, comm_slv) # transfer addr and rw  
    if rw == False:
        check_start_wr(dut, addr_slv, rw)
    else:
        check_start_rd(dut, addr_slv, rw, addr_reg, data) 
    await ack_start(dut)             # ACK from slave     

#--------------------------------------------------------------------------    
async def start_i2c(dut):
    dut.IO_SDA <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.I_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")    

#--------------------------------------------------------------------------        
async def transaction(dut, data): 
    for i in data:
        dut.IO_SDA <= int(i);
        await Timer(1 / I2C_CLK_1_4, units="sec")
        dut.I_SCL <= 1;
        await Timer(1 / I2C_CLK_1_2, units="sec")
        dut.I_SCL <= 0;
        await Timer(1 / I2C_CLK_1_4, units="sec")

#--------------------------------------------------------------------------    
async def ack_start(dut):
    dut.I_ACK <= 0;
    await ack_slv(dut)
    
#-------------------------------------------------------------------------- 
async def ack_slv(dut):
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.I_SCL <= 1;
    await Timer(1 / I2C_CLK_1_2, units="sec")
    dut.I_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")

#--------------------------------------------------------------------------        
async def stop_i2c(dut):
    dut.IO_SDA <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.I_SCL <= 1;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.IO_SDA <= 1;

#--------------------------------------------------------------------------    
async def wr_slv(dut): 
    data_from_slv = [];
    string = "";
    for i in range(8):
        await Timer(1 / I2C_CLK_1_4, units="sec")
        dut.I_SCL <= 1; what_save(dut, data_from_slv)
        await Timer(1 / I2C_CLK_1_2, units="sec")
        dut.I_SCL <= 0;
        await Timer(1 / I2C_CLK_1_4, units="sec")
    for i in data_from_slv:
        string += str(i);
    data_from_slv = int((string), base=2);
    return data_from_slv;

#--------------------------------------------------------------------------    
async def mstr_ack(dut, ack_mstr, addr_slv, rw, addr_reg, i):
    dut.IO_SDA <= ack_mstr;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.I_SCL <= 1;
    await ClockCycles(dut.CLK, 3, rising=False)
    check_reading(dut, addr_slv, rw, addr_reg, i, ack_mstr)  
    await Timer(1 / I2C_CLK_1_2, units="sec")
    dut.I_SCL <= 0;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.IO_SDA <= 1;

#--------------------------------------------------------------------------        
def what_save(dut, data_from_slv):
    if dut.IO_SDA.value.binstr == "z" or dut.IO_SDA == 1:
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

#--------------------------------------------------------------------------  
def check_start_wr(dut, addr_slv, rw):
    assert dut.O_CH_CNCT == True, "O_CH_CNCT was incorrect 1"
    assert dut.O_ADDR_SLV == addr_slv, "O_ADDR_SLV was incorrect on the {} addr_slv for write" .format(addr_slv)
    assert dut.O_RW == rw, "O_RW was incorrect on the {} rw for write" .format(rw)  

#--------------------------------------------------------------------------  
def check_start_rd(dut, addr_slv, rw, addr_reg, data):
    assert dut.O_DATA_VL == True, "O_DATA_VL was incorrect 1" .format(i)      
    assert dut.O_ADDR_SLV == addr_slv, "O_ADDR_SLV was incorrect on the {} addr_slv for write" .format(addr_slv)
    assert dut.O_RW == rw, "O_RW was incorrect on the {} rw for write" .format(rw)
    assert dut.O_ADDR_REG == addr_reg, "O_ADDR_REG was incorrect on the {} addr_reg for write" .format(addr_reg)
    assert dut.O_DATA_RD == data, "O_DATA_RD was incorrect on the {} data for write in {} loop" .format(data, i)

#--------------------------------------------------------------------------     
def check_writting(dut, addr_slv, rw, addr_reg, data, i):
    assert dut.O_DATA_VL.value == True, "O_DATA_VL was incorrect 1 in {} loop" .format(i)      
    assert dut.O_ADDR_SLV.value == addr_slv, "O_ADDR_SLV was incorrect on the {} addr_slv for write in {} loop" .format(addr_slv, i)
    assert dut.O_RW.value == rw, "O_RW was incorrect on the {} rw for write in {} loop" .format(rw, i)
    assert dut.O_ADDR_REG.value == addr_reg + i, "O_ADDR_REG was incorrect on the {} addr_reg for write in {} loop" .format(addr_reg, i)
    assert dut.O_DATA_RD.value == data, "O_DATA_RD was incorrect on the {} data for write in {} loop" .format(data, i)

#--------------------------------------------------------------------------      
def check_reading(dut, addr_slv, rw, addr_reg, i, ack_mstr):
    valid = 0;
    if ack_mstr == False:
        i += 1;
        valid = 1;
    assert dut.O_ADDR_SLV.value == addr_slv, "O_ADDR_SLV was incorrect on the {} addr_slv for write in {} loop" .format(addr_slv, i)
    assert dut.O_RW.value == rw, "O_RW was incorrect on the {} rw for write in {} loop" .format(rw, i)
    assert dut.O_ADDR_REG.value == addr_reg + i, "O_ADDR_REG was incorrect on the {} addr_reg for write in {} loop" .format(addr_reg, i)    
    assert dut.O_DATA_VL.value == valid, "O_DATA_VL was incorrect {} in {} loop" .format(valid, i)      