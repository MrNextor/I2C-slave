# test_top_slv_i2c.py

import random
import i2c
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer
from cocotb.binary import BinaryValue

#--------------------------------------------------------------------------
I2C_CLK  = 100e3;
I2C_CLK_1_2 = I2C_CLK * 2;
I2C_CLK_1_4 = I2C_CLK * 4;

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
    write = i2c.Write();
    read = i2c.Read();
    await ClockCycles(dut.CLK, 2, rising=False) 

#--------------------------------------------------------------------------   
# start the first transaction, writting of two bytes
    await start_tr_addr(dut, write.addr_slv_wr()) # start I2C, transfer addr and RW  
    check_start_wr(dut, write) # check
    await ack_start(dut) # ACK from slave 
    await Timer(60, units="ns")
    await transaction(dut, write.addr_reg()) # transfer addr_reg 
    await ack_slv(dut) # ACK from slave
# transfer data 
    num_byte = 4;
    for i in range(num_byte):
        await Timer(60, units="ns")
        await transaction(dut, write.data())
        check_writting(dut, write, i) # check
        await ack_slv(dut)
        write.new_data(); # overwrite data
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut)
    await Timer(1 / I2C_CLK_1_2, units="sec")     

#--------------------------------------------------------------------------   
# start the second transaction, reading of two bytes
    await start_tr_addr(dut, read.addr_slv_wr()) # start I2C, transfer addr and RW, ACK from slave  
    check_start_wr(dut, read) # check
    await ack_start(dut) # ACK from slave  
    await Timer(60, units="ns")    
    await transaction(dut, read.addr_reg()) # transfer addr_reg
    await ack_slv(dut) # ACK from slave
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut)
    await Timer(1 / I2C_CLK_1_2, units="sec") 
# start I2C, transfer addr and RW, ACK from slave    
    await start_tr_addr(dut, read.addr_slv_rd())
    check_start_rd(dut, read)
    await ack_start(dut) # ACK from slave 
# transfer data 
    num_byte = 2; ack_mstr = 0;
    for i in range(num_byte):
        dut.I_DATA_WR = int(read.data_from_slv(), base=2);
        data_from_slv_after = await wr_slv(dut)
        assert dut.I_DATA_WR.value == data_from_slv_after, "Read the data was incorrect {} written the data in {} loop".format(data_from_slv_after, i)  
        if i != num_byte - 1:
            ack_mstr = 0;
        else:
            ack_mstr = 1;
        await Timer(60, units="ns")
        await mstr_ack(dut, read, ack_mstr, i)
        read.new_data_from_slv() # overwrite data
# stop I2C
    await Timer(60, units="ns")    
    await stop_i2c(dut)
    await Timer(1 / I2C_CLK_1_2, units="sec")  


#--------------------------------------------------------------------------      
async def start_tr_addr(dut, data):
    await start_i2c(dut)         # start I2C
    await transaction(dut, data) # transfer addr and rw  

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
async def mstr_ack(dut, read, ack_mstr, i):
    dut.IO_SDA <= ack_mstr;
    await Timer(1 / I2C_CLK_1_4, units="sec")
    dut.I_SCL <= 1;
    await ClockCycles(dut.CLK, 3, rising=False)
    check_reading(dut, read, ack_mstr, i)  
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
def check_start_wr(dut, wr_rd):
    assert dut.O_CH_CNCT.value == True, "O_CH_CNCT was incorrect on the 1"
    assert dut.O_ADDR_SLV.value == int(wr_rd.addr_slv(), base=2), "O_ADDR_SLV was incorrect on the {} addr slave for write" .format(wr_rd.addr_slv())
    assert dut.O_RW.value == int(wr_rd.rw_wr()), "O_RW was incorrect on the {} rw" .format(wr_rd.rw_wr())  

#--------------------------------------------------------------------------  
def check_start_rd(dut, read):
    assert dut.O_DATA_VL.value == True, "O_DATA_VL was incorrect on the 1"    
    assert dut.O_ADDR_SLV.value == int(read.addr_slv(), base=2), "O_ADDR_SLV was incorrect on the {} addr slve for write" .format(read.addr_slv())
    assert dut.O_RW.value == int(read.rw_rd()), "O_RW was incorrect on the {} rw for write" .format(read.rw_rd())
    assert dut.O_ADDR_REG.value == int(read.addr_reg(), base=2), "O_ADDR_REG was incorrect on the {} addr reg for write" .format(read.addr_reg())

#--------------------------------------------------------------------------     
def check_writting(dut, write, i):
    assert dut.O_DATA_VL.value == True, "O_DATA_VL was incorrect on the 1 in {} loop" .format(i)      
    assert dut.O_ADDR_SLV.value == int(write.addr_slv(), base=2), "O_ADDR_SLV was incorrect on the {} addr slave for write in {} loop" .format(write.addr_slv(), i)
    assert dut.O_RW.value == int(write.rw_wr()), "O_RW was incorrect on the {} rw in {} loop" .format(write.rw_wr(), i)
    assert dut.O_ADDR_REG.value == int(write.addr_reg(), base=2) + i, "O_ADDR_REG was incorrect on the {} addr reg for write in {} loop" .format(write.addr_reg(), i)
    assert dut.O_DATA_RD.value == int(write.data(), base=2), "O_DATA_RD was incorrect on the {} data for write in {} loop" .format(write.data(), i)

#--------------------------------------------------------------------------      
def check_reading(dut, read, ack_mstr, i):
    valid = 0;
    if ack_mstr == False:
        i += 1;
        valid = 1;
    assert dut.O_ADDR_SLV.value == int(read.addr_slv(), base=2), "O_ADDR_SLV was incorrect on the {} addr_slv for write in {} loop" .format(read.addr_slv(), i)
    assert dut.O_RW.value == int(read.rw_rd()), "O_RW was incorrect on the {} rw for write in {} loop" .format(read.rw_rd(), i)
    assert dut.O_ADDR_REG.value == int(read.addr_reg(), base=2) + i, "O_ADDR_REG was incorrect on the {} addr_reg for write in {} loop" .format(read.addr_reg(), i)    
    assert dut.O_DATA_VL.value == valid, "O_DATA_VL was incorrect {} in {} loop" .format(valid, i)      