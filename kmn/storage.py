import asyncio
import json
import os


class JSONStorage:
    def __init__(self, file_name: str, *, loop):
        self.file_name = file_name
        self.loop = loop
        self._lock = asyncio.Lock()

        try:
            with open(self.file_name, 'r') as fp:
                self._data = json.load(fp)
        except FileNotFoundError:
            self._data = {}

    def _save(self):
        filename = self.file_name + '.save'
        with open(filename, 'w') as fp:
            json.dump(self._data, fp)

        os.rename(filename, self.file_name)
        os.remove(filename)

    async def delete(self, key):
        """Deletes some data."""
        del self._data[key]
        await self.save()

    async def save(self):
        """Saves the data."""
        async with self._lock:
            await self.loop.run_in_executor(None, self._save)

    async def put(self, key, value):
        """Puts data."""
        self._data[key] = value
        await self.save()

    def get(self, *args, **kwargs):
        return self._data.get(*args, **kwargs)
