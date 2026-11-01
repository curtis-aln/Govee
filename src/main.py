import time

from async_worker import AsyncWorker
from govee_strip import GoveeStrip
from command_functions import CommandFunctions


def main():
    worker = AsyncWorker()
    strip = GoveeStrip()

    try:
        future = worker.submit(strip.connect()) # connect to the strip before starting the GUI
        future.result(timeout=10) # wait for the connection to complete, or raise an exception if it fails
        time.sleep(2)

        worker.submit(strip.send(CommandFunctions.off())).result() # turn off the strip before starting the GUI
        time.sleep(1)
        worker.submit(strip.send(CommandFunctions.on())).result() # turn on the strip before starting the GUI


    finally:
        worker.submit(strip.close()).result() # disconnect from the strip when the program exits
        worker.stop() # stop the asyncio loop and thread when the program exits


# entry point into the program
if __name__ == "__main__":
    main()