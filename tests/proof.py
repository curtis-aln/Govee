"""Govee BLE LED strip controller (Windows/Linux/macOS). pip install bleak
Usage: python govee_ctl.py [BLE_ADDRESS]
Close the Govee phone app first: the strip only accepts one BLE connection.
"""
import asyncio, sys, threading, tkinter as tk
from tkinter import colorchooser
from bleak import BleakScanner, BleakClient

CHAR = "00010203-0405-0607-0809-0a0b0c0d2b11"   # write characteristic
BRIGHT_MAX = 255                                # some models want 0-100; change if brightness acts odd


def pkt(*b):
    """20-byte frame: payload zero-padded to 19 bytes + XOR checksum."""
    p = bytes(b) + bytes(19 - len(b))
    c = 0
    for x in p:
        c ^= x
    return p + bytes([c])


ON, OFF = pkt(0x33, 1, 1), pkt(0x33, 1, 0)
bright = lambda v: pkt(0x33, 4, v)
color_manual = lambda r, g, b: pkt(0x33, 5, 0x02, r, g, b)                      # H6159/H6001 style
color_segment = lambda r, g, b: pkt(0x33, 5, 0x0B, r, g, b, 0, 0, 0xFF, 0x7F)   # H6199/H6127 style


class Strip:
    def __init__(self, addr=None):
        self.addr, self.client = addr, None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        # in Strip.__init__, add:
        self._lock = asyncio.Lock()

    async def _connect(self):
        async with self._lock:
            if self.client and self.client.is_connected:
                return
            if not self.addr:
                devs = await BleakScanner.discover(timeout=8)
                hits = [d for d in devs if (d.name or "").startswith(("ihoment", "Govee"))]
                print("found:", [(d.name, d.address) for d in hits])
                if not hits:
                    raise RuntimeError("no Govee device found")
                self.addr = hits[0].address
            self.client = BleakClient(self.addr, winrt=dict(use_cached_services=False))
            await self.client.connect()
            for s in self.client.services:
                print(s.uuid)
                for c in s.characteristics:
                    print("   ", c.uuid, c.properties)

    async def _send(self, data):
        await self._connect()
        await self.client.write_gatt_char(CHAR, data, response=False)

    def send(self, data):
        f = asyncio.run_coroutine_threadsafe(self._send(data), self.loop)
        f.add_done_callback(lambda f: f.exception() and print("err:", f.exception()))


def main():
    strip = Strip(sys.argv[1] if len(sys.argv) > 1 else None)
    root = tk.Tk()
    root.title("Govee")
    seg = tk.BooleanVar(value=False)

    def pick():
        rgb, _ = colorchooser.askcolor()
        if rgb:
            r, g, b = map(int, rgb)
            strip.send((color_segment if seg.get() else color_manual)(r, g, b))

    tk.Button(root, text="On", command=lambda: strip.send(ON)).pack(fill="x")
    tk.Button(root, text="Off", command=lambda: strip.send(OFF)).pack(fill="x")
    tk.Button(root, text="Colour...", command=pick).pack(fill="x")
    tk.Checkbutton(root, text="segment colour packet (try if Colour does nothing)", variable=seg).pack()
    s = tk.Scale(root, from_=1, to=100, orient="horizontal", label="Brightness %")
    s.set(100)
    s.bind("<ButtonRelease-1>", lambda e: strip.send(bright(round(s.get() / 100 * BRIGHT_MAX))))
    s.pack(fill="x")
    root.mainloop()


if __name__ == "__main__":
    main()