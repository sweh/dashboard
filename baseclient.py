import asyncio
import json


class BaseClient:

    sleep_time = 30
    keep_history = 3600  # 1 hour
    history = None
    websockets = None
    type_ = None

    def __init__(self, config):
        self.config = config
        self.history = []
        self.websockets = {}
        self.keep_items = int(self.keep_history / self.sleep_time)

    async def register(self, websocket):
        self.websockets[websocket] = []
        if self.history:
            for item in self.history:
                await self.send(websocket, item)

    async def send(self, websocket, data):
        if websocket.state == 1:
            if data in self.websockets[websocket]:
                return
            await websocket.send(json.dumps(data))
            self.websockets[websocket].append(data)
        else:
            del self.websockets[websocket]

    async def run(self):
        while True:
            try:
                self.history = self.history[0-self.keep_items:]
                result = self.data
            except Exception as e:
                print(f'Exception while fetching {self._type} data: {e}')
            else:
                if result:
                    result['DeviceClass'] = self.type_
                    if result not in self.history:
                        self.history.append(result)
                    for websocket in list(self.websockets):
                        await self.send(websocket, result)
            finally:
                await asyncio.sleep(self.sleep_time)
