import asyncio
import json

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


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
                log.error(f'Exception while fetching {self.type_} data: {e}')
            else:
                if result:
                    result['DeviceClass'] = self.type_
                    if result not in self.history:
                        self.history.append(result)
                        log.info(
                            f'{self.type_} fetched new data, sending to '
                            f'{len(self.websockets)} clients.'
                        )
                        for websocket in list(self.websockets):
                            await self.send(websocket, result)
                    else:
                        log.info(
                            f'{self.type_} fetched existing data, not sending '
                            f'to {len(self.websockets)} clients.'
                        )
            finally:
                await asyncio.sleep(self.sleep_time)
