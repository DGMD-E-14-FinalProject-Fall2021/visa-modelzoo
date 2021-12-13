#!/usr/bin/env python3

import time
import platform
import asyncio
import logging

from bleak import discover
from bleak import BleakClient

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

async def scan():
    dev = await discover()
    for i in range(0,len(dev)):
        if dev[i].name == "STLB250":
           #Print the devices discovered
           #TODO write to the log file
            print("[" + str(i) + "]" + dev[i].address,dev[i].name,dev[i].metadata["uuids"])
            devices_dict[dev[i].address] = []
            devices_dict[dev[i].address].append(dev[i].name)
            devices_dict[dev[i].address].append(dev[i].metadata["uuids"])
            devices_list.append(dev[i].address)
 
async def write_haptic_feedback(direction):
    feedback = bytes([direction])
    print(f'writing haptic feedback: {feedback}' )
    await global_client.write_gatt_char(HAPTIC_CHAR_UUID, feedback)
    print('Done sending feedback')
    await asyncio.sleep(1.0)
 
async def start_ble_client():

    disconnected_event = asyncio.Event()
    
    def disconnected_callback(client):
        print("Disconnected callback called!")
        disconnected_event.set()

    async with BleakClient(address, disconnected_callback = disconnected_callback) as client:
        try:

            await scan()

            x = await client.is_connected()
            log.info("Connected: {0}".format(x))

            for service in client.services:
                log.info("[Service] {0}: {1}".format(service.uuid, service.description))
                for char in service.characteristics:
                    if "read" in char.properties:
                        try:
                            value = bytes(await client.read_gatt_char(char.uuid))
                        except Exception as e:
                            value = str(e).encode()
                    else:
                        value = None
                        log.info(
                            "\t[Characteristic] {0}: (Handle: {1}) ({2}) | Name: {3}, Value: {4} ".format(
                                char.uuid,
                                char.handle,
                                ",".join(char.properties),
                                char.description,
                                value,
                        )
                    )
                    for descriptor in char.descriptors:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        log.info(
                            "\t\t[Descriptor] {0}: (Handle: {1}) | Value: {2} ".format(
                                descriptor.uuid, descriptor.handle, bytes(value)
                            )
                        )

            # Turn on haptic sensor with value 0x01 (Move hand right)
            await client.write_gatt_char(HAPTIC_CHAR_UUID, b'\x01', response=True)
            await asyncio.sleep(3.0)
            # Turn off haptic sensor with a value of 0x00
            await client.write_gatt_char(HAPTIC_CHAR_UUID, b'\x00', response=True)

        except Exception as e:
             await disconnected_event.wait()
    
