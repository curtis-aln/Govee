"""Map mask bits to segments and hunt for a working segment-brightness frame, using the strip's own read-back as the oracle.

Run from the project root:  python tests/segment_probe.py
Close the Govee phone app first.

The read-back (aa a5 NN) returns 3 segments per page as (brightness, R, G, B), so the strip's stored state can be
checked directly instead of by eye. The candidate brightness frames are guesses inside the 0x15 segment-mode
namespace. The script re-reads the strip's mode after each one and restores plain red if anything unexpected
changes. If the strip ever behaves oddly, Ctrl+C is safe, and power-cycling the strip resets it.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from async_worker import AsyncWorker
from govee_strip import GoveeStrip
from command_functions import CommandFunctions as C

RUN_MAPPING = True
RUN_BRIGHTNESS_PROBE = True

NUM_BITS = 16        # one past the documented 15, to see whether bit 15 maps to anything
PAGES = 5            # read-back pages, 3 segments each -> 15 segments
TEST_VALUE = 5       # brightness the candidate frames try to set (full is 100)

# 0x01 is the colour sub-type, so it is skipped
SUBTYPES = [0x00, 0x02, 0x03, 0x04, 0x05, 0x06]

# candidate frame layouts: where the brightness value and the 16-bit segment mask sit after 33 05 15 <sub>
LAYOUTS = {
    "A value@4 mask@12": lambda s, v, m: bytes([0x33, 0x05, 0x15, s, v, 0, 0, 0, 0, 0, 0, 0, m & 0xFF, m >> 8]),
    "B value@4 mask@5":  lambda s, v, m: bytes([0x33, 0x05, 0x15, s, v, m & 0xFF, m >> 8]),
    "C mask@4 value@6":  lambda s, v, m: bytes([0x33, 0x05, 0x15, s, m & 0xFF, m >> 8, v]),
}

replies: list[tuple[float, bytes]] = []   # filled from the loop thread


def tap_notify(strip: GoveeStrip) -> None:
    """Wrap the strip's notify handler so replies are collected. Must run before the first connect."""
    original = strip._on_notify

    def tap(sender, data):
        replies.append((time.perf_counter(), bytes(data)))
        original(sender, data)

    strip._on_notify = tap


def send(worker, strip, payload, timeout=5):
    worker.submit(strip.send(payload)).result(timeout=timeout)


def query(worker, strip, payload, prefix, timeout=0.6):
    """Send a query and return the first reply starting with `prefix`, or None on timeout."""
    start = len(replies)
    send(worker, strip, payload)
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        for _, d in replies[start:]:
            if d.startswith(prefix):
                return d
        time.sleep(0.01)
    return None


def read_segments(worker, strip):
    """Return a list of (brightness, r, g, b) per segment, or None where a page got no reply."""
    segs = []
    for p in range(1, PAGES + 1):
        r = query(worker, strip, bytes([0xAA, 0xA5, p]), prefix=bytes([0xAA, 0xA5, p]))
        if r is None:
            segs.extend([None] * 3)
            continue
        for g in range(3):
            o = 3 + g * 4
            segs.append(tuple(r[o:o + 4]))
    return segs


def read_mode(worker, strip):
    r = query(worker, strip, bytes([0xAA, 0x05]), prefix=bytes([0xAA, 0x05]))
    return None if r is None else r[2]


def fmt(seg):
    return "--------" if seg is None else "".join(f"{x:02x}" for x in seg)


def diff(base, now):
    return [i for i, (a, b) in enumerate(zip(base, now)) if a != b]


def reset(worker, strip):
    send(worker, strip, C.brightness(100))
    send(worker, strip, C.colour_rgbic(255, 0, 0))
    time.sleep(0.5)


def mapping_test(worker, strip):
    print("\n== segment mapping: set one mask bit blue, see which stored segments change ==")
    reset(worker, strip)
    base = read_segments(worker, strip)
    print("baseline:", [fmt(s) for s in base])
    if any(s != (100, 255, 0, 0) for s in base):
        print("note: baseline is not 15 x bright red (64ff0000). Either the colour frame isn't taking effect or the read-back differs.")

    table = {}
    for n in range(NUM_BITS):
        send(worker, strip, C.colour_rgbic(0, 0, 255, mask=1 << n))
        time.sleep(0.2)
        now = read_segments(worker, strip)
        changed = diff(base, now)
        table[n] = changed
        print(f"bit {n:2d} mask=0x{1 << n:04X} -> segment index {changed}  {[fmt(now[i]) for i in changed]}")
        send(worker, strip, C.colour_rgbic(255, 0, 0))   # all back to red
        time.sleep(0.2)

    print("\nmulti-bit mask 0x0005 (expect the segments of bit 0 and bit 2 together):")
    send(worker, strip, C.colour_rgbic(0, 0, 255, mask=0x0005))
    time.sleep(0.2)
    print("  changed:", diff(base, read_segments(worker, strip)))
    reset(worker, strip)

    used = sorted({i for v in table.values() for i in v})
    print(f"\nsegments reached: {len(used)} -> {used}")
    print("bits that changed nothing:", [n for n, v in table.items() if not v])


def brightness_probe(worker, strip):
    print("\n== segment brightness: try candidate frames, check the stored brightness byte ==")
    reset(worker, strip)
    base = read_segments(worker, strip)
    if any(s is None or s[0] != 100 for s in base):
        print("warning: baseline brightness is not 100 everywhere:", [fmt(s) for s in base])

    hits = []
    for sub in SUBTYPES:
        for lname, build in LAYOUTS.items():
            payload = build(sub, TEST_VALUE, 0x0001)
            label = f"sub=0x{sub:02X} {lname}"
            send(worker, strip, payload)
            time.sleep(0.15)
            now = read_segments(worker, strip)
            mode = read_mode(worker, strip)
            changed = diff(base, now)

            if changed:
                print(f"HIT  {label}  frame={payload.hex()}")
                for i in changed:
                    print(f"       segment {i}: {fmt(base[i])} -> {fmt(now[i])}")
                hits.append((label, payload))
            else:
                print(f"none {label}")

            if mode != 0x15:
                print(f"       mode is now {mode}, restoring red")
            if changed or mode != 0x15:
                send(worker, strip, build(sub, 100, 0x0001))      # undo the brightness change, if it was one
                reset(worker, strip)
                if diff(base, read_segments(worker, strip)):
                    print("       warning: state did not return to baseline")

    print("\n== summary ==")
    if hits:
        for label, payload in hits:
            print(f"  {label}: {payload.hex()}")
    else:
        print("  no candidate changed any stored segment value; the capture from the Govee app is the next step")


def main():
    worker = AsyncWorker()
    strip = GoveeStrip()
    tap_notify(strip)
    try:
        send(worker, strip, C.on(), timeout=15)    # first call scans and connects
        if RUN_MAPPING:
            mapping_test(worker, strip)
        if RUN_BRIGHTNESS_PROBE:
            brightness_probe(worker, strip)
    except KeyboardInterrupt:
        print("stopped")
    finally:
        try:
            reset(worker, strip)
            worker.submit(strip.close()).result(timeout=5)
        except Exception as e:
            print("cleanup error:", e)
        finally:
            worker.stop()


if __name__ == "__main__":
    main()