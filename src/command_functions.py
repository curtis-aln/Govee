# Using the constants above we can make the following abstractions 
from constants import TYPE_POWER, TYPE_BRIGHT, TYPE_COLOUR, MODE_MANUAL, CMD_PREFIX, BRIGHT_MAX

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
    def colour(r: int, g: int, b: int) -> bytes:
        return bytes([CMD_PREFIX, TYPE_COLOUR, MODE_MANUAL, r, g, b])  # bytes() raises ValueError if any is outside 0-255
