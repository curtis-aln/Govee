import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from async_worker import AsyncWorker
from govee_strip import GoveeStrip
from command_functions import CommandFunctions as C

NUM_BITS = 16        # one past the documented 15, to see whether bit 15 does anything
DELAY = 1          # seconds between segments
RESET_EACH = False   # True: blank the whole strip before each segment (shows whether colours persist)
DIM = 0


def send(worker, strip, payload, timeout=5):
    worker.submit(strip.send(payload)).result(timeout=timeout)

def main():
    worker = AsyncWorker()
    strip = GoveeStrip()
    try:
        DIM = 1
        send(worker, strip, C.brightness(100))
        send(worker, strip, C.colour_rgbic(255, 255, 0))
        send(worker, strip, C.brightness_segments(DIM))      # everything dim
        time.sleep(1)

        prev = None
        while True:
            for n in range(15):
                send(worker, strip, C.brightness_segments(100, mask=1 << n))
                if prev is not None:
                    send(worker, strip, C.brightness_segments(DIM, mask=1 << prev))
                prev = n
                time.sleep(DELAY)

    except KeyboardInterrupt:
        print("stopped")
    finally:
        try:
            send(worker, strip, C.colour_rgbic(0, 0, 0))   # leave the strip dark
            worker.submit(strip.close()).result(timeout=5)
        except Exception as e:
            print("cleanup error:", e)
        finally:
            worker.stop()


if __name__ == "__main__":
    main()