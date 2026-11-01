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
