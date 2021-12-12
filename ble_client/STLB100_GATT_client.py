#!/usr/bin/env python3

import time
import platform
import asyncio
import logging

# from bleak import discover
# from bleak import BleakClient

client = 0

address = (
     "C0:CC:BB:AA:AA:AA"
)

# Distance characteristic uuid
DISTANCE_CHAR_UUID = "00140000-0001-11e1-ac36-0002a5d5c51b"
# Haptic characteristic uuid
HAPTIC_CHAR_UUID = "20000000-0001-11e1-ac36-0002a5d5c51b"

devices_dict = {}
devices_list = []
receive_data = []

# async def scan():
#     dev = await discover()
#     for i in range(0,len(dev)):
#         if dev[i].name == "STLB250":
#            #Print the devices discovered
#            #TODO write to the log file
#             print("[" + str(i) + "]" + dev[i].address,dev[i].name,dev[i].metadata["uuids"])
#             devices_dict[dev[i].address] = []
#             devices_dict[dev[i].address].append(dev[i].name)
#             devices_dict[dev[i].address].append(dev[i].metadata["uuids"])
#             devices_list.append(dev[i].address)
 
async def run_haptic_feedback(queue_haptic: asyncio.Queue):
    print("running haptic feedback")
    while True:
        # Use await asyncio.wait_for(queue.get(), timeout=1.0) if you want a timeout for getting data.
        data = await queue_haptic.get()
        print(f"{data}: haptic handler received!")
        #if data is None:
        #    print("Logic disconnecting! Exiting consumer loop...")
        #    break
        #else:
            # disconnect distance streaming
            #await global_client.write_gatt_char(DISTANCE_CHAR_UUID, 0, response=True)
            #await asyncio.sleep(1.0) 
            #await global_client.write_gatt_char(HAPTIC_CHAR_UUID, b'\x01', response=True)
            #await asyncio.sleep(1.0)
            # re-start distance streaming
            #await global_client.write_gatt_char(DISTANCE_CHAR_UUID, 4, response=True)
 
async def run_ble_client(queue: asyncio.Queue()):
    print("rnning ble")
    debug=False

    disconnected_event = asyncio.Event()
    print("rnning ble middle")
    def disconnected_callback(client):
        print("Disconnected callback called!")
        disconnected_event.set()
    
    log = logging.getLogger(__name__)
    if debug:
        import sys

        log.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        log.addHandler(h)

    async def notification_handler(sender, data):
        d = ""
        d = ''.join('{:02x}'.format(x) for x in data)
        hex_lower_byte = str(d[12:14])
        hex_upper_byte = str(d[14:16])
        hex_distance = hex_upper_byte + hex_lower_byte
        # distance in millimeters
        mill_distance = int(hex_distance, base=16)
        #distance in inches
        distance = round(mill_distance * 0.0393701, 2)
        await queue.put((time.time(), distance))
    print("rnning ble end")

#     async with BleakClient(address, disconnected_callback = disconnected_callback) as client:
#         try:
# 
#             await scan()
# 
#             x = await client.is_connected()
#             log.info("Connected: {0}".format(x))
#             
#             for service in client.services:
#                 log.info("[Service] {0}: {1}".format(service.uuid, service.description))
#                 for char in service.characteristics:
#                     if "read" in char.properties:
#                         try:
#                             value = bytes(await client.read_gatt_char(char.uuid))
#                         except Exception as e:
#                             value = str(e).encode()
#                     else:
#                         value = None
#                         log.info(
#                             "\t[Characteristic] {0}: (Handle: {1}) ({2}) | Name: {3}, Value: {4} ".format(
#                                 char.uuid,
#                                 char.handle,
#                                 ",".join(char.properties),
#                                 char.description,
#                                 value,
#                         )
#                     )
#                     for descriptor in char.descriptors:
#                         value = await client.read_gatt_descriptor(descriptor.handle)
#                         log.info(
#                             "\t\t[Descriptor] {0}: (Handle: {1}) | Value: {2} ".format(
#                                 descriptor.uuid, descriptor.handle, bytes(value)
#                             )
#                         )
# 
#             # Turn on haptic sensor with value 0x01 (Move hand right)
#             #await client.write_gatt_char(HAPTIC_CHAR_UUID, b'\x01', response=True)
#             #await asyncio.sleep(5.0)
#             # Turn off haptic sensor with a value of 0x00
#             #await client.write_gatt_char(HAPTIC_CHAR_UUID, b'\x00', response=True)
# 
#             await client.start_notify(DISTANCE_CHAR_UUID, notification_handler)
#             await client.write_gatt_char(DISTANCE_CHAR_UUID, 4, response=True)
#             await asyncio.sleep(5.0)
#             await client.stop_notify(DISTANCE_CHAR_UUID) 
#             # send exit command to the consumer
#             await queue.put((time.time(), None))
#         except Exception as e:
#              await disconnected_event.wait()
#     
# 