# The Computer is the Central, and the strip is the peripheral.
# The peripheral exposes services which contain characteristics we read, write, or subscribe to.
# Some write types include "write with response" which waits for ACK (Aknowledgement). Govee usually uses the latter for commands.
# Govee Uses 20 byte frames with the XOR checksum in the last byte

# BLE - Bluetooth Low Energy which is a low power version of Bluetooth used by sensors, wearables and smart lights. Its
#       designed for sending small bursts of data cheaply
# GATT is the Generic Attribute Profile. It defines how a BLE device organises its data, so every BLE device is a tiny database.
# - A service is a group of related data, identified by a UUID (universally Unique Identifier) which is a 128-bit number
#   guarenteed to not collide with any other UUID. (for example, Govee’s ...1910).
# - a characteristic sits inside a service and is one value that you can interact with, identified by its own UUID, and it
#   has proprerties that define how you can interact with it (read, write, notify, etc). 

# BleakClient is an Asynchronous context manager which automatically connects and disconnects from a device.

"""
UI / CLI           "set colour red", slider moved
   ↓
Commands           on(), off(), brightness(n), colour(r,g,b)  → return payload bytes
   ↓
Framing            make_frame(payload) → 20-byte frame  
   ↓
Transport (BLE)    find device, connect, write_gatt_char(frame)
"""

# The segment colour packet ends with two mask bytes.
# Together they form a 16-bit number where, by my hypothesis, each bit selects one segment: 
# bit 0 is segment 1, bit 1 is segment 2, and so on. 0x7FFF is 15 bits set, 
# which is why the older notes treat it as “all 15 segments”

from constants import search_timeout, NOTIFY_CHAR_UUID, CMD_CHAR_UUID
from make_frame import make_frame

import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic

import time

class GoveeStrip:
    def __init__(self, address: str | None = None):
        self.address = address
        self.client: BleakClient | None = None
        self.lock = asyncio.Lock()
        self.last_reply = None

    # lifecycle
    async def connect(self) -> None:
        # Hold the lock for the whole method so two callers can't connect at the same time
        async with self.lock:
            # Already connected: nothing to do. This is what makes send() cheap
            if self.client and self.client.is_connected:
                return

            # First run (or after a failed connect): scan for the strip
            if self.address is None:
                self.address = await self._find()

            # Build the client but don't use `async with`, because that would disconnect
            # as soon as the block ends. close() handles the disconnect instead
            self.client = BleakClient(
                self.address,
                disconnected_callback=self._on_disconnect,
                winrt=dict(use_cached_services=False),  # skip Windows' stale GATT cache
            )

            try:
                # Raises on failure, so no is_connected check is needed afterwards
                await self.client.connect()
                # Subscribe once here so replies from the strip are caught from the first command
                await self.client.start_notify(NOTIFY_CHAR_UUID, self._on_notify)
            except Exception:
                if self.client and self.client.is_connected:
                    await self.client.disconnect()
                self.address = None
                self.client = None
                raise

    async def close(self) -> None: # disconnect if connected
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from the device.")
        self.client = None

    # the hooks Python calls for async with
    # async with GoveeStrip() as strip:
    #     await strip.send(on())
    async def __aenter__(self): # await self.connect(); return self
        await self.connect() # what the strip binds to
        return self

    async def __aexit__(self, *exc): # await self.close()
        await self.close()


    # sending
    async def send(self, payload: bytes) -> None: # ensure connected, make_frame, write_gatt_char
        await self.connect() # returns instantly if already connected
        await self.client.write_gatt_char(CMD_CHAR_UUID, make_frame(payload), response=False)


    # internals
    async def _find(self) -> str: # used to find govee device
        # this provides an escape for the search, asyncio.Future, which is an empty box that one side fills and the other side awaits.
        # A Future is an empty box that something else fills in later
        found = asyncio.get_running_loop().create_future()
    
        # if the device is found, we set the result of the future to the device, which will allow the main function to continue
        # and if the device is callback is called, we check if the device name starts with "Govee" and if the future is not done, we set the result of the future to the device.
        def callback(device, adv):
            name = device.name or adv.local_name or ""
            if name.startswith("Govee") and not found.done():
                found.set_result(device)
                print(f"Found device: {name} ({device.address})")
    
        # we use the BleakScanner as an asynchronous context manager, which will automatically start and stop scanning for devices when the block is entered and exited.
        async with BleakScanner(callback):
            try:
                device = await asyncio.wait_for(found, search_timeout)
            except TimeoutError:
                raise RuntimeError("no Govee strip found: is it powered and not connected to another app?") from None
        return device.address


    def _on_notify(self, sender: BleakGATTCharacteristic, data: bytearray) -> None: # callback for notifications
        self.last_reply = bytes(data)
        self.last_reply_at = time.perf_counter()
        print("reply:", data.hex())

    def _on_disconnect(self, client):
        print(f"Device {client.address} disconnected.")
        if self.client is client:
            self.client = None
