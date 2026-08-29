
# Autofans -- Control fan speeds based on temperature readings.

apt update
apt upgrade
apt install vim
apt install python3-pip
pip3 install adafruit-circuitpython-emc2101
apt install i2c-tools
pip3 install adafruit-circuitpython-mcp9808
i2cdetect -y 2
raspi-config 
i2cdetect -y 2
i2cdetect -y 1
