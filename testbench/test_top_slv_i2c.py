# test_top_slv_i2c.py

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.triggers import ClockCycles

I2C_CLK  = 1 / 100000

@cocotb.test()
async def test_top_slv_i2c(dut):
    """ Test def_freq_i2c.v """

    clock_clk = Clock(dut.CLK, 20, units="ns")  # Create a 20ns period clock on port CLK
    cocotb.fork(clock_clk.start())  # Start the CLK
    clock_scl = Clock(dut.I_SCL, I2C_CLK, units="sec")  # Create I_SCL
    cocotb.fork(clock_scl.start())  # Start the I_SCL

    dut.RST_n <= 1
    await FallingEdge(dut.CLK)
    dut.RST_n <= 0
    cocotb.log.info("RST_n is still active: %d" % dut.RST_n)
    await ClockCycles(dut.CLK, 2, rising=False)
    dut.RST_n <= 1
    cocotb.log.info("RST_n has gone inactive: %d" % dut.RST_n)

    for i in range(10):
        await FallingEdge(dut.I_SCL)