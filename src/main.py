from async_worker import AsyncWorker
from govee_strip import GoveeStrip
from gui import App


def main():
    worker = AsyncWorker()
    strip = GoveeStrip()
    app = App(worker, strip)
    app.mainloop()  # blocks until the window closes; on_close handles all cleanup


if __name__ == "__main__":
    main()