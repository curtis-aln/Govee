# Tkinter is used for the GUI, but both tkinter and asyncio each want to own the main thread,
# so most of this code will be about getting them to cooperate.

# root.mainloop() blocks forever and runs Tk's event loop.
# asyncio.run() blocks forever and runs asyncio's event loop.

# The standard solution is to run Tk on the main thread. and push asyncio onto a secondary thread, which owns the GoveeStrip.
# Button callbacks hand coroutine to that loop with asyncio.run_coroutine_threadsafe(coro, loop).
# It’s thread-safe, returns immediately, and gives you a concurrent.futures.Future for the result.

# Main thread:  Tk mainloop ── button click ──► run_coroutine_threadsafe ─┐
# Loop thread:  asyncio loop ◄───────────────────────────────────────────┘
#               └─ GoveeStrip, BleakClient, the lock

import asyncio
import concurrent
import threading

class AsyncWorker:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

    def submit(self, coro) -> concurrent.futures.Future:
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
        self.loop.close() # loop.stop() halts the loop, but never closes it
