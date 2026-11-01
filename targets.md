
[DONE] Stage 0: Enumerate. Write a script that scans, connects to your strip, and prints every service and characteristic with its properties. You’ll need BleakScanner.discover, BleakClient as an async context manager, and client.services.
Checkpoint: you know which characteristics have write-without-response and which have notify. This also fixes your current error, since the UUID I hardcoded may not exist on the H617E.

Stage 1: Frame builder, no Bluetooth. Write make_frame(*payload) -> bytes that pads to 19 bytes and appends the XOR checksum. Then write on(), off() and brightness(n) on top of it.
Checkpoint: plain asserts against known-good frames. 33 01 01 00...00 33 is on. This layer is pure and testable without hardware, so keep it separate from the Bluetooth code.

Stage 2: One command end to end. Connect, write the ON frame, disconnect. Then try off and brightness.
Checkpoint: the strip reacts. If it doesn’t, that’s Stage 3.

Stage 3: Decode the protocol yourself. The H617E is likely newer than the reverse-engineered models, and its frames may differ. The method:

On an Android phone, enable Developer options → Bluetooth HCI snoop log.
In the Govee app, do actions in a deliberate order: on, off, red, green, blue, then brightness at a few steps.
Pull the log (adb bugreport, then find btsnoop_hci.log in the zip).
Open it in Wireshark and filter btatt.opcode == 0x52 || btatt.opcode == 0x12. Those are the ATT write commands and requests.
Diff the payloads. Change one thing at a time and see which bytes move.

Checkpoint: you can predict the frame for “set colour to (R,G,B)” before sending it.

Stage 4: Async model. Learn asyncio properly: coroutines, await, the event loop, asyncio.Lock, and run_coroutine_threadsafe. Then decide your GUI architecture:

Tkinter blocks the main thread, so the async loop has to live in a background thread, which is what the starter did.
Alternatively, use a GUI with async integration, such as qasync with PySide6.
Or skip the GUI and make a CLI first. This is the better choice for learning.