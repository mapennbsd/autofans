#!/usr/bin/python

import time
import board
import sys
import datetime
from adafruit_emc2101 import EMC2101
import adafruit_mcp9808

i2c = board.I2C()  # uses board.SCL and board.SDA

emc = EMC2101(i2c)

# To initialise using the default address:
mcp = adafruit_mcp9808.MCP9808(i2c)

# To initialise using a specified address:
# Necessary when, for example, connecting A0 to VDD to make address=0x19
# mcp = adafruit_mcp9808.MCP9808(i2c_bus, address=0x19)

print("Current Fan speed", emc.fan_speed, flush=True)
