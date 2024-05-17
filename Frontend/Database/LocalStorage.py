import asyncio
import time

import diskcache as dc


class LocalStorage:
    _instance = None
    _expiration_time = 600  # 24 hours * 60 minutes * 60 seconds

    def _init_storage(self):
        self._cache = dc.Cache(f'./Database/my_cache')
        self._lock = asyncio.Semaphore(1)  # Initialize semaphore for async lock

    @staticmethod
    def get_instance():
        if LocalStorage._instance is None:
            LocalStorage._instance = LocalStorage()
            LocalStorage._instance._init_storage()
        return LocalStorage._instance

    async def get_resource(self, key: str):
        async with self._lock:
            if key not in self._cache:
                print("Trying to get a non-existing resource")
                return None
            return self._cache[key]

    async def post_resource(self, key: str, value: dict):
        async with self._lock:
            # Set the item in the cache with an expiration time
            self._cache.set(key, value, expire=LocalStorage._expiration_time)
            return True

    async def delete_resource(self, key: str):
        async with self._lock:
            if key not in self._cache:
                print("Trying to delete a non-existing resource")
                return False
            del self._cache[key]
            return True

    async def put_resource(self, key: str, partial_value: dict):
        async with self._lock:
            if key not in self._cache:
                print("Key does not exist. Use post_resource to create a new resource.")
                return False
            current_value = self._cache[key]  # Get the current value
            # Update the current value with the partial_value
            updated_value = {**current_value, **partial_value}
            # Reset the expiration timer on update
            self._cache.set(key, updated_value, expire=LocalStorage._expiration_time)
            return True

    def close_cache(self):
        self._cache.close()  # Properly close the cache when done
