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
BRIGHT_MAX  = 100    # this model has a brightness range of 0-100
ALL_SEGMENTS = 0x7FFF   # 15 bits, one per segment on the models documented so far

MODE_MANUAL  = 0x02    # was overwritten with 0x0B
MODE_SEGMENT = 0x0B
MODE_RGBIC   = 0x15    # H617x family, per the H617A notes