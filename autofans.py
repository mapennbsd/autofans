#!/usr/bin/python

import time
import board
import sys
import argparse
import datetime
from adafruit_emc2101 import EMC2101
import adafruit_mcp9808

parser = argparse.ArgumentParser(description="Monitor temperature and control fan speed.")
parser.add_argument("--check", action="store_true",
                     help="print the current fan speed and exit, without running the control loop")
args = parser.parse_args()

i2c = board.I2C()  # uses board.SCL and board.SDA

emc = EMC2101(i2c)

# To initialise using the default address:
mcp = adafruit_mcp9808.MCP9808(i2c)

# To initialise using a specified address:
# Necessary when, for example, connecting A0 to VDD to make address=0x19
# mcp = adafruit_mcp9808.MCP9808(i2c_bus, address=0x19)

print("Current Fan speed", emc.fan_speed, flush=True)

if args.check:
    sys.exit(0)

speed = 100

while True:
    ct = datetime.datetime.now()
    oldspeed = speed
    tempC = mcp.temperature
    tempF = tempC * 9 / 5 + 32
    print(ct, "Temperature: {} F ".format(tempF), "Fan speed RPM:", int(emc.fan_speed), "PWM %:", int(emc.manual_fan_speed), flush=True)
    temp = int(tempF)
    if temp < 75:
        speed = 25
    elif temp <= 80:
        speed = 50
    elif temp <= 82:
        speed = 60
    elif temp <= 84:
        speed = 70
    elif temp <= 86:
        speed = 80
    elif temp <= 88:
        speed = 90
    else:
        speed = 100

    if oldspeed != speed:
        print("Setting fan speed to ", speed, "%", flush=True)
        emc.manual_fan_speed = speed

    time.sleep(60)
