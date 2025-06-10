import time
import threading

class Timer:
    def __init__(self):
        self.timeout = False

    def time_track(self, limit):
        start = time.time()
        def is_timeout():
            while True:
                elapsed = time.time() - start
                if elapsed > limit:
                    self.timeout = True
                    break
                time.sleep(1)
        threading.Thread(target=is_timeout, daemon=True).start()
        
class TimeControl:
    def __init__(self):
        pass

    def add_timer(self, limit):
        timer = Timer()
        timer.time_track(limit)
        return timer
