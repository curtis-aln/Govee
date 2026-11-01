from constants import FRAME_LEN, NOTIFY_CHAR_UUID

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


