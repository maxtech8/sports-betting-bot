import asyncio
import diskcache as dc

from Logger.CustomLogger import CustomLogger


class LocalStorage:
    _instance = None
    _expiration_time = 604800  # 1 Week

    def _init_storage(self):
        self._cache = dc.Cache(f'/Database/my_cache')
        self._logger = CustomLogger.get_instance()
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
                self._logger.debug(f"Trying to get a non-existing resource. key: {key}")
                return None
            return self._cache[key]

    async def post_resource(self, key: str, value: dict):
        async with self._lock:
            self._cache.set(key, value, expire=LocalStorage._expiration_time)
            return True

    async def delete_resource(self, key: str):
        async with self._lock:
            if key not in self._cache:
                self._logger.debug(f"Trying to delete a non-existing resource. key: {key}")
                return False
            del self._cache[key]
            return True

    async def put_resource(self, key: str, partial_value: dict):
        try:
            async with self._lock:
                if key not in self._cache:
                    self._logger.debug(f"Key does not exist. Use post_resource to create a new resource. key: {key}")
                    return False
                current_value = self._cache[key]  # Get the current value
                # Update the current value with the partial_value
                updated_value = {**current_value, **partial_value}
                # Reset the expiration timer on update
                self._cache.set(key, updated_value, expire=LocalStorage._expiration_time)
                return True
        except Exception as ex:
            print(f"put_resource error: {ex}")
        

    def close_cache(self):
        self._cache.close()  # Properly close the cache when done
