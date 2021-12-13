import asyncio

from bleak import BleakClient, discover

address = (
     "C0:CC:BB:AA:AA:AA"
)

devices_dict = {}
devices_list = []
receive_data = []

class Connection:
    
    client: BleakClient = None
    
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
    ):
        self.loop = loop
        self.connected = False
       
    def on_disconnect(self, client: BleakClient, future: asyncio.Future):
        self.connected = False
        print(f"Disconnected from {devices_list}!")

    async def cleanup(self):
        if self.client:
            await self.client.disconnect()

    async def manager(self):
        print("Starting connection manager.")
        while True:
            if self.client:
                await self.connect()
            else:
                await self.scan()
                await asyncio.sleep(10.0)       

    async def connect(self):
        if self.connected:
            return
        try:
            await self.client.connect()
            self.connected = await self.client.is_connected()
            if self.connected:
                print(F"Connected to {devices_list}")
                self.client.set_disconnected_callback(self.on_disconnect)
                while True:
                    if not self.connected:
                        break
                    await asyncio.sleep(3.0)
            else:
                print(f"Failed to connect to {devices_list}")
        except Exception as e:
            print(e)

    async def scan(self):
        print('scanning...')
        dev = await discover()
        for i in range(0,len(dev)):
            if dev[i].name == "STLB250":
            #Print the devices discovered
                print("[" + str(i) + "]" + dev[i].address,dev[i].name,dev[i].metadata["uuids"])
                devices_dict[dev[i].address] = []
                devices_dict[dev[i].address].append(dev[i].name)
                devices_dict[dev[i].address].append(dev[i].metadata["uuids"])
                devices_list.append(dev[i].address)
                self.client = BleakClient(dev[i].address, loop=self.loop)
                
