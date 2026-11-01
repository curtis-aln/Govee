
Stage 0: Enumerate. Write a script that scans, connects to your strip, and prints every service and characteristic with its properties. You’ll need BleakScanner.discover, BleakClient as an async context manager, and client.services.
Checkpoint: you know which characteristics have write-without-response and which have notify. This also fixes your current error, since the UUID I hardcoded may not exist on the H617E.
