# Using the constants above we can make the following abstractions 
from constants import TYPE_POWER, TYPE_BRIGHT, TYPE_COLOUR, MODE_MANUAL, CMD_PREFIX, BRIGHT_MAX, ALL_SEGMENTS, MODE_SEGMENT, MODE_RGBIC

class CommandFunctions:
    @staticmethod
    def power(state: bool) -> bytes:
        return bytes([CMD_PREFIX, TYPE_POWER, int(state)])

    @staticmethod
    def on() -> bytes:
        return CommandFunctions.power(True)

    @staticmethod
    def off() -> bytes:
        return CommandFunctions.power(False)

    @staticmethod
    def brightness(n: int) -> bytes:
        if not 0 <= n <= BRIGHT_MAX:
            raise ValueError(f"brightness must be 0-{BRIGHT_MAX}, got {n}")
        return bytes([CMD_PREFIX, TYPE_BRIGHT, n])

    @staticmethod
    def brightness_segments(n: int, mask: int = ALL_SEGMENTS) -> bytes:
        if not 0 <= n <= BRIGHT_MAX:
            raise ValueError(f"brightness must be 0-{BRIGHT_MAX}, got {n}")
        if not 0 <= mask <= 0xFFFF:
            raise ValueError(f"mask must fit in 16 bits, got {mask}")
        return bytes([CMD_PREFIX, TYPE_COLOUR, MODE_RGBIC, 0x02, n,
                    mask & 0xFF, mask >> 8])     # mask follows the value, low byte first

    @staticmethod
    def colour(r: int, g: int, b: int) -> bytes:
        return bytes([CMD_PREFIX, TYPE_COLOUR, MODE_MANUAL, r, g, b])  # bytes() raises ValueError if any is outside 0-255

    @staticmethod
    def colour_segments(r: int, g: int, b: int, mask: int = ALL_SEGMENTS) -> bytes:
        if not 0 <= mask <= 0xFFFF:
            raise ValueError(f"mask must fit in 16 bits, got {mask}")
        return bytes([CMD_PREFIX, TYPE_COLOUR, MODE_SEGMENT, r, g, b,
                    0x00, 0x00,                    # unused here (colour temperature field in other modes)
                    mask & 0xFF, mask >> 8])       # low byte first (little-endian)

    @staticmethod
    def colour_rgbic(r: int, g: int, b: int, mask: int = ALL_SEGMENTS) -> bytes:
        if not 0 <= mask <= 0xFFFF:
            raise ValueError(f"mask must fit in 16 bits, got {mask}")
        return bytes([CMD_PREFIX, TYPE_COLOUR, MODE_RGBIC, 0x01, r, g, b,
                    0x00, 0x00, 0x00, 0x00, 0x00,
                    mask & 0xFF, mask >> 8])   # low byte first
