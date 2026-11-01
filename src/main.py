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

import asyncio
from bleak import BleakClient, BleakScanner

# A BLEDevice received from a BleakScanner or a Bluetooth address (e.g. device UUID)
address = "A4:C1:38:3B:19:10"  # Replace with your device's address
search_timeout = 5.0  # seconds

# in order to detect the govee led strips we need to use a BleakScanner to scan for devices in the area
# The scanner will listen for BLE advertisements with optional filters and return a list of devices that match the criteria.
# This can subsiquently be used with the BleakClient to connect to the device and interact with its services and characteristics.
async def get_address():
    print("Scanning for devices...")

    ## This is where all our device information will be stored
    devices = await BleakScanner.discover(timeout=search_timeout, return_adv=True)
    
    # Print the discovered devices
    print("Discovered devices:")
    for device in devices:
        print(device)


async def main():
    print("Running main()")

    async with BleakClient(address) as client:
        # Check if the client is connected
        ...
    
    # Device disconnects when block exits



if __name__ == "__main__":
    asyncio.run(get_address())
    asyncio.run(main())