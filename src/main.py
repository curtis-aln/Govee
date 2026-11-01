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

import asyncio
from bleak import BleakClient, BleakScanner

# A BLEDevice received from a BleakScanner or a Bluetooth address (e.g. device UUID)
search_timeout = 3.0  # seconds
FRAME_LEN = 20 # the length of the frame the Govee strip expects, including the checksum byte


GOVEE_SERVICE_UUID = "00010203-0405-0607-0809-0a0b0c0d1910"
CMD_CHAR_UUID      = "00010203-0405-0607-0809-0a0b0c0d2b11"   # write commands here, lists write-without-response
NOTIFY_CHAR_UUID   = "00010203-0405-0607-0809-0a0b0c0d2b10"   # strip's replies arrive here, it has notify

# H617E - he 65.6 ft (20 m) model in Govee’s RGBIC LED strip range. It is the same family as the H617A (5 m), H617C (10 m) and H617F (30 m)
# with Bluetooth-controlled RGBIC kits, meaning each segment of the strip can show a different colour at the same time
# These are the values at fixed positions in the payload
# byte 0        byte 1        byte 2+
# CMD_PREFIX    TYPE_xxx      value(s)
# The first one goes to byte 0, and the other 3 are options for byte 1.
CMD_PREFIX   = 0x33 # byte 0. It marks the packet as a control command. 0xAA marks a keep-alive and 0xA1 marks DIY data.
TYPE_POWER   = 0x01 # byte 1, selects the power command. The value byte after it is 0x01 for on and 0x00 for off. 33 01 01 is on.
TYPE_BRIGHT  = 0x04 # byte 1, selects brightness. The next byte is the level, in a range that depends on the model (0-255 or 0-100), so make that a constant too.
TYPE_COLOUR  = 0x05 # byte 1, selects colour. The byte after it is the sub-mode (0x02 manual or 0x0B segments), then R, G, B, then segment mask bytes for the segmented form.
MODE_MANUAL = 0x02   # swap for 0x0B (+ segment mask) if colour is ignored
BRIGHT_MAX  = 255    # some models use 100

# Using the constants above we can make the following abstractions 
def power(state: bool) -> bytes:
    return bytes([CMD_PREFIX, TYPE_POWER, int(state)])

def on() -> bytes:
    return power(True)

def off() -> bytes:
    return power(False)

def brightness(n: int) -> bytes:
    if not 0 <= n <= BRIGHT_MAX:
        raise ValueError(f"brightness must be 0-{BRIGHT_MAX}, got {n}")
    return bytes([CMD_PREFIX, TYPE_BRIGHT, n])

def colour(r: int, g: int, b: int) -> bytes:
    return bytes([CMD_PREFIX, TYPE_COLOUR, MODE_MANUAL, r, g, b])  # bytes() raises ValueError if any is outside 0-255

# in order to detect the govee led strips we need to use a BleakScanner to scan for devices in the area
# The scanner will listen for BLE advertisements with optional filters and return a list of devices that match the criteria.
# This can subsiquently be used with the BleakClient to connect to the device and interact with its services and characteristics.
async def find_govee():
    print("Scanning for devices...")

    # this provides an escape for the search, asyncio.Future, which is an empty box that one side fills and the other side awaits.
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
        return await asyncio.wait_for(found, search_timeout)


# `bytes` is immutable, whereas `bytearray` is mutable and is an array of values between 0 and 255.
# make_frame() is used for sending data to the LED strip. It takes the meaninful part of data and wraps it into the fixed 20 byte packet the strip expects
# (The govee-ble-local library describes “20-byte command framing” and says it was derived from the decompiled Govee app and tested on real hardware.)
# The strip ignores anything that isnt exactly in that shape, so every command sent must go through this function.

def checksum(data: bytes) -> int:
    result = 0
    for b in data:
        result ^= b
    return result

def make_frame(data : bytes) -> bytes:
    # outputs a bytes object of exactly 20 bytes, with the last byte being the XOR checksum of the first 19 bytes.
    # [ payload ][ zero padding to reach 19 bytes ][ checksum ]

    if len(data) > FRAME_LEN - 1:
        raise ValueError(f"payload is {len(data)} bytes, max is {FRAME_LEN - 1}")
    
    # Take the payload
    # Pad it with 0x00 until it’s 19 bytes long
    # XOR all 19 bytes together to get one byte, the checksum.
    # Append the checksum as byte 20.
    padded = data + bytes(FRAME_LEN - 1 - len(data))
    return padded + bytes([checksum(padded)])



async def main():
    print("Running main()")

    # running some tests to make sure my make frame works correctly
    assert make_frame(on()).hex()  == "3301010000000000000000000000000000000033"
    assert make_frame(off()).hex() == "3301000000000000000000000000000000000032"
    assert make_frame(brightness(0x80))[-1] == 0x33 ^ 0x04 ^ 0x80

    device = await find_govee()

     # Print the discovered devices
    print("Discovered device:")
    print(device.name, device.address)

    def on_notify(sender, data: bytearray):
        print(f"notify {sender}: {data.hex()}")

    async with BleakClient(device) as client:
        # Check if the client is connected
        if not client.is_connected:
            print("Failed to connect to the device.")
            return

        await client.start_notify(NOTIFY_CHAR_UUID, on_notify)

        # commands
        await client.start_notify(NOTIFY_CHAR_UUID, on_notify)
        await client.write_gatt_char(CMD_CHAR_UUID, make_frame(on()), response=False)
        await asyncio.sleep(2)



        # keep the connection open long enough to receive replies
        await asyncio.sleep(2)
        
    
    # Device disconnects when block exits


# entry point into the program
if __name__ == "__main__":
    asyncio.run(main())