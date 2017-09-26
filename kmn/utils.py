import time


class timed:
    def __enter__(self):
        self.before = time.monotonic()
        return self

    def __exit__(self, *args):
        self.after = time.monotonic()
        self.interval = (self.after - self.before) * 1000
