import asyncio

from govee_strip import GoveeStrip


async def main():
   govee = GoveeStrip()
   await govee.connect()

# entry point into the program
if __name__ == "__main__":
    asyncio.run(main())