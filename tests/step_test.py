"""Measure how the strip responds to single changes, then how fast flashing has to be before it disappears.

Run from the project root:  python tests/step_test.py
Part 1: one slow step down and back up per channel, with timestamps printed so you can match them to a slow-motion video.
Part 2: flashing at decreasing periods, to find where the flicker stops being visible.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from async_worker import AsyncWorker
from govee_strip import GoveeStrip
from command_functions import CommandFunctions as C

HOLD = 3.0           # seconds to hold each level in part 1
SWEEP_SECONDS = 4.0  # seconds per period in part 2
PERIODS = [1.0, 0.5, 0.3, 0.2, 0.1]

# (label, high payload, low payload)
STEP_TESTS = [
    ("global brightness 100 -> 0 -> 100",    C.brightness(100),                C.brightness(0)),
    ("global brightness 100 -> 10 -> 100",   C.brightness(100),                C.brightness(10)),
    ("segment brightness 100 -> 0 -> 100",   C.brightness_segments(100),       C.brightness_segments(0)),
    ("segment brightness 100 -> 10 -> 100",  C.brightness_segments(100),       C.brightness_segments(10)),
    ("power on -> off -> on",                C.on(),                           C.off()),
]

SWEEP_TESTS = [
    ("global  10 <-> 100",  C.brightness(100),          C.brightness(10)),
    ("segment 10 <-> 100",  C.brightness_segments(100), C.brightness_segments(10)),
]


def send(worker, strip, payload, timeout=5):
    worker.submit(strip.send(payload)).result(timeout=timeout)


def restore(worker, strip):
    send(worker, strip, C.on())
    send(worker, strip, C.brightness(100))
    send(worker, strip, C.brightness_segments(100))
    send(worker, strip, C.colour_rgbic(255, 0, 0))
    time.sleep(1.5)


def part1(worker, strip):
    print("\n===== PART 1: single steps. Note how long each transition takes (instant / 0.5 s / 1 s+) =====")
    for label, high, low in STEP_TESTS:
        print(f"\n{label}")
        restore(worker, strip)
        t0 = time.perf_counter()
        print(f"  t={time.perf_counter() - t0:4.1f}s  sending LOW now")
        send(worker, strip, low)
        time.sleep(HOLD)
        print(f"  t={time.perf_counter() - t0:4.1f}s  sending HIGH now")
        send(worker, strip, high)
        time.sleep(HOLD)


def part2(worker, strip):
    print("\n===== PART 2: flashing. Note the period where the flicker stops being visible =====")
    for label, high, low in SWEEP_TESTS:
        for period in PERIODS:
            print(f"\n{label} every {period} s")
            restore(worker, strip)
            end = time.perf_counter() + SWEEP_SECONDS
            state = False
            while time.perf_counter() < end:
                send(worker, strip, high if state else low)
                state = not state
                time.sleep(period)


def main():
    worker = AsyncWorker()
    strip = GoveeStrip()
    try:
        send(worker, strip, C.on(), timeout=15)    # first call scans and connects
        part1(worker, strip)
        part2(worker, strip)
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