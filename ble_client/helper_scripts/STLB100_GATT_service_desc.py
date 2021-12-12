#!/usr/bin/env python3

import sys
import platform
import asyncio
import logging

from bleak import BleakClient

logger = logging.getLogger(__name__)

devices_dict = {}
devices_list = []
receive_data = []

ADDRESS = (
    "AA:AA:AA:DD:EE:FF"
    if platform.system() != "Darwin"
    else "B9EA5233-37EF-4DD6-87A8-2A875E821C46"
)

# Environmental data
char_uuid = "00140000-0001-11e1-ac36-0002a5d5c51b"

def env_notify_callback(sender: int, data: bytearray):
    print(f"{sender}: {data}")

#To discover BLE devices nearby 
async def discover():
    devices = await discover()
    for i in range(0,len(devices)):
        if i.name == "STLB250":
            #Print the devices discovered
            print("[" + str(i) + "]" + dev[i].address,dev[i].name,dev[i].metadata["uuids"])
            #Put devices information into list
            devices_dict[dev[i].address] = []
            devices_dict[dev[i].address].append(dev[i].name)
            devices_dict[dev[i].address].append(dev[i].metadata["uuids"])
            devices_list.append(dev[i].address)

#An easy notify function, just print the recieve data
def notification_handler(sender, data):
    print(', '.join('{:02x}'.format(x) for x in data))

async def main(address):

    disconnected_event = asyncio.Event()
    
    def disconnected_callback(client):
        print("Disconnected callback called!")
        disconnected_event.set()

    async with BleakClient(address) as client:
        logger.info(f"Connected: {client.is_connected}")

        for service in client.services:
            logger.info(f"[Service] {service}")
            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = bytes(await client.read_gatt_char(char.uuid))
                        logger.info(
                            f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                        )
                    except Exception as e:
                        logger.error(
                            f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {e}"
                        )

                else:
                    value = None
                    logger.info(
                        f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                    )

                for descriptor in char.descriptors:
                    try:
                        value = bytes(
                            await client.read_gatt_descriptor(descriptor.handle)
                        )
                        logger.info(f"\t\t[Descriptor] {descriptor}) | Value: {value}")
                    except Exception as e:
                        logger.error(f"\t\t[Descriptor] {descriptor}) | Value: {e}")
    
    #client.start_notify(char_uuid, env_notify_callback)
    


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(sys.argv[1] if len(sys.argv) == 2 else ADDRESS))
