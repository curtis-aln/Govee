import tkinter as tk

from command_functions import CommandFunctions
from govee_strip import GoveeStrip
from async_worker import AsyncWorker

class App(tk.Tk): # root is the top-level Tk window, and widgets can’t exist without a parent
    def __init__(self, worker: AsyncWorker, strip: GoveeStrip):
        super().__init__()
        self.worker = worker # the AsyncWorker that runs the asyncio loop in a separate thread
        self.strip = strip # the GoveeStrip that runs on the asyncio loop in the separate thread
        self.set_window_details()

    def set_window_details(self):
        self.title("Govee Strip Control")
        self.geometry("400x300")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        tk.Button(self, text="On", command=lambda: self._send(CommandFunctions.on())).pack(fill="x")
        tk.Button(self, text="Off", command=lambda: self._send(CommandFunctions.off())).pack(fill="x")

    def _send(self, payload):
        fut = self.worker.submit(self.strip.send(payload))
        fut.add_done_callback(self._on_done) # error protection: if the coroutine raises, print the exception. This runs on the loop thread, so don't touch widgets here.

    def _on_done(self, fut):
        exc = fut.exception()       # runs on the LOOP thread, so don't touch widgets here
        if exc:
            print("Error sending command:", exc)


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
