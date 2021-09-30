# Makefile

SIM = icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(shell pwd)/../source/top_slv_i2c.v
VERILOG_SOURCES += $(shell pwd)/../source/def_freq_i2c.v
TOPLEVEL = top_slv_i2c
MODULE = test_top_slv_i2c

include $(shell cocotb-config --makefiles)/Makefile.sim
