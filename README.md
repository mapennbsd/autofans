# autofans

Control fan speeds on a Raspberry Pi based on temperature readings from an
MCP9808 sensor, driving an EMC2101 fan controller over I2C.

This project targets a Raspberry Pi (the "target system"); it is not meant
to run on the development machine used to write/edit it.

## Setup (on the Raspberry Pi)

These steps assume a fresh Raspberry Pi OS install with the MCP9808
temperature sensor and EMC2101 fan controller already wired to the Pi's I2C
pins.

1. Update the system and install prerequisites:

   ```
   sudo apt update
   sudo apt upgrade
   sudo apt install vim python3-pip i2c-tools
   ```

   (`vim` is optional — use whatever editor you prefer.)

2. Install the Python drivers for the two sensor/controller boards:

   ```
   pip3 install adafruit-circuitpython-emc2101 adafruit-circuitpython-mcp9808
   ```

3. Enable the I2C interface. Run `sudo raspi-config`, then go to
   **Interface Options → I2C** and enable it. Reboot if prompted.

4. Confirm the devices are visible on the I2C bus:

   ```
   i2cdetect -y 1
   ```

   You should see two addresses show up in the grid — one for the MCP9808
   sensor and one for the EMC2101 fan controller. If nothing appears, double
   check the wiring and that I2C was actually enabled in step 3.

   Some Pi models expose I2C on bus 2 instead of (or in addition to) bus 1;
   if bus 1 comes back empty, also try:

   ```
   i2cdetect -y 2
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
