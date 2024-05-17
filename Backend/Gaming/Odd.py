import time


class Odd:
    def __init__(self, odd_id, odd_name, rate, update_time=None):
        self.odd_id = odd_id  # Unique id to each odd
        self.odd_name = odd_name
        self.rate = rate  # side multiplier
        if update_time is None:
            self.update_time = time.time()
        else:
            self.update_time = update_time
        self._last_refresh_time = time.time()

    def get_last_refresh_time(self):
        return self._last_refresh_time

    def set_last_refresh_time(self, time):
        self._last_refresh_time = time

    def to_dict(self):
        return {
            "odd_id": self.odd_id,
            "odd_name": self.odd_name,
            "rate": self.rate,
            "update_time": self.update_time
        }
