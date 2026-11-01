"""Find out which changes snap and which fade. Watch the strip, and film it in slow motion if you can.

Run from the project root:  python tests/fade_test.py
Each test alternates two states every PERIOD seconds for DURATION seconds, then restores the strip.
Note for each one: crisp strobe, blurry pulse, or barely changes.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from async_worker import AsyncWorker
from govee_strip import GoveeStrip
from command_functions import CommandFunctions as C

PERIOD = 0.1      # seconds between writes, the same as the original fast flash
DURATION = 3.0    # seconds per test
PAUSE = 2.0       # seconds between tests

# (label, state A payload, state B payload)
TESTS = [
    ("A  global brightness   0 <-> 100   (the original fast flash)", C.brightness(0), C.brightness(100)),
    ("B  global brightness  20 <-> 100",                             C.brightness(20), C.brightness(100)),
    ("C  segment brightness  0 <-> 100, all segments",               C.brightness_segments(0), C.brightness_segments(100)),
    ("D  segment brightness 20 <-> 100, all segments",               C.brightness_segments(20), C.brightness_segments(100)),
    ("E  segment brightness  0 <-> 100, segment 0 only",             C.brightness_segments(0, mask=0x0001), C.brightness_segments(100, mask=0x0001)),
    ("F  power off <-> on",                                          C.off(), C.on()),
]


def send(worker, strip, payload, timeout=5):
    worker.submit(strip.send(payload)).result(timeout=timeout)


def restore(worker, strip):
    send(worker, strip, C.on())
    send(worker, strip, C.brightness(100))
    send(worker, strip, C.brightness_segments(100))
    send(worker, strip, C.colour_rgbic(255, 0, 0))
    time.sleep(1.5)


def main():
    worker = AsyncWorker()
    strip = GoveeStrip()
    try:
        send(worker, strip, C.on(), timeout=15)    # first call scans and connects
        restore(worker, strip)

        for label, a, b in TESTS:
            print(f"\n{label}")
            end = time.perf_counter() + DURATION
            state = False
            while time.perf_counter() < end:
                send(worker, strip, b if state else a)
                state = not state
                time.sleep(PERIOD)
            restore(worker, strip)
            time.sleep(PAUSE)
        print("\ndone")
    except KeyboardInterrupt:
        print("stopped")
    finally:
        try:
            restore(worker, strip)
            worker.submit(strip.close()).result(timeout=5)
        except Exception as e:
            print("cleanup error:", e)
        finally:
            worker.stop()


if __name__ == "__main__":
    main()