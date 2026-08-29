# autofans

Control fan speeds on a Raspberry Pi based on temperature readings from an
MCP9808 sensor, driving an EMC2101 fan controller over I2C.

This project targets a Raspberry Pi (the "target system"); it is not meant
to run on the development machine used to write/edit it.

## Setup (on the Raspberry Pi)

```
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
```

## Usage

Run the control loop:

```
./autofans.py
```

Check the current fan speed and exit, without starting the control loop:

```
./autofans.py --check
```

## Running at startup

To start `autofans.py` automatically at boot via `/etc/rc.local`, add the
following line to `/etc/rc.local`, replacing `user` with your own username:

```
sudo -u user /home/user/autofans/startfans.sh &
```
