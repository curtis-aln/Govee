import tkinter as tk

import queue
from tkinter import colorchooser

from constants import BRIGHT_MAX
from command_functions import CommandFunctions

from command_functions import CommandFunctions
from govee_strip import GoveeStrip
from async_worker import AsyncWorker

# This is the GUI thread, which is separate from the asyncio loop thread. The GUI thread runs the Tk mainloop, and the asyncio loop thread runs the GoveeStrip's async methods. 
# Communication between them is done via a queue and futures.

class App(tk.Tk): # root is the top-level Tk window, and widgets can’t exist without a parent
    PRESETS = {"Red": (255, 0, 0), "Green": (0, 255, 0), "Blue": (0, 0, 255),
           "Warm white": (255, 180, 100), "Purple": (160, 32, 240)}
    
    def __init__(self, worker: AsyncWorker, strip: GoveeStrip):
        super().__init__()
        self.worker = worker # the AsyncWorker that runs the asyncio loop in a separate thread
        self.strip = strip # the GoveeStrip that runs on the asyncio loop in the separate thread
        self.set_window_details()

        self.messages = queue.Queue()   # loop thread -> Tk thread, the only safe crossing
        self.build_widgets()
        self.after(100, self._poll)

    def set_window_details(self):
        self.title("Govee Strip Control")
        self.geometry("400x300")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_widgets(self):
        pad = dict(fill="x", padx=10, pady=4)

        tk.Button(self, text="On", command=lambda: self._send(CommandFunctions.on())).pack(**pad)
        tk.Button(self, text="Off", command=lambda: self._send(CommandFunctions.off())).pack(**pad)

        self.brightness = tk.Scale(self, from_=0, to=BRIGHT_MAX, orient="horizontal", label="Brightness")
        self.brightness.set(BRIGHT_MAX)
        self.brightness.bind("<ButtonRelease-1>", self._on_brightness)   # send on release, not per pixel
        self.brightness.pack(**pad)

        tk.Button(self, text="Colour...", command=self._pick_colour).pack(**pad)

        row = tk.Frame(self)
        row.pack(**pad)
        for name, rgb in self.PRESETS.items():
            # rgb=rgb binds the current value; a bare lambda would see only the loop's last value
            tk.Button(row, text=name, command=lambda rgb=rgb: self._send(CommandFunctions.colour_rgbic(*rgb))).pack(side="left", padx=2)

        self.status = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status, anchor="w").pack(**pad)

    def _on_brightness(self, event):
        self._send(CommandFunctions.brightness(self.brightness.get()))

    def _pick_colour(self):
        rgb, _ = colorchooser.askcolor(title="Pick a colour")
        if rgb is None:                      # dialog cancelled
            return
        r, g, b = (int(c) for c in rgb)      # can arrive as floats
        self._send(CommandFunctions.colour_rgbic(r, g, b))
        print(f"Picked colour: {r}, {g}, {b}")

    def _poll(self):
        # runs on the Tk thread, so widget updates are safe here
        try:
            while True:
                self.status.set(self.messages.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._poll)          # re-arm

    def _send(self, payload):
        fut = self.worker.submit(self.strip.send(payload))
        fut.add_done_callback(self._on_done) # error protection: if the coroutine raises, print the exception. This runs on the loop thread, so don't touch widgets here.

    def _on_done(self, fut):
        # loop thread: no widgets here, only the queue
        exc = fut.exception()
        self.messages.put(f"Error: {exc}" if exc else "Sent")


    def on_close(self):
        try:
            # disconnect on the loop thread, and wait so the strip is released before we exit
            self.worker.submit(self.strip.close()).result(timeout=5)
        except Exception as e:
            print("Error while disconnecting:", e)
        finally:
            # always run these, even if the disconnect failed or timed out
            self.worker.stop()
            self.destroy()
