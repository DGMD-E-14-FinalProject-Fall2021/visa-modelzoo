VISA App receives distance and haptic sensor data from SensorTile that acts as GATT server. Here is implementation of STLB100_GATT_client that connects to the server, reads its characteristcs' values and dispaches to appropriate consumer.

Implementation Background:

GATT client is implemented using Bleak framework. Bleak is a GATT client software, capable of connecting to BLE devices acting as GATT servers. It is designed to provide an asynchronous, cross-platform Python API to connect and communicate with e.g. sensors. 

Bleak documentation:

https://buildmedia.readthedocs.org/media/pdf/bleak/stable/bleak.pdf

Requirenments to use STLB100_GATT_client:

1. Install Bluez 5.50 or newer

sudo apt install bluez

2. Install Bleak on Raspberry Pi 4 or your host platform for VISA App (tested platforms Raspberry Pi 4, Zero W armv6).

pip install bleak

3. Get familiar with bluetopthctl, gatttool, hciconfig, systemctl stop/start/restart  bluetooth

Current Functionality:

1. Connenct to the GATT server
2. Read servicess UUIDs, characteristics and descriptors.
3. Read distance in milliseconds, convert into inches using environmental UUID
4. Dispatch distance data to consumer

TODO:
1. Test client against VISA SensorTile firmware. Add functionality to write haptic feedback values to GATT server and dispatch it to consumer.
