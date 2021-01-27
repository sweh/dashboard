import asyncio
import json

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class BaseClient:

    sleep_time = 30
    keep_items = 1
    history = None
    websockets = None
    type_ = None

    def __init__(self, config):
        self.config = config
        self.history = []
        self.websockets = {}

    async def register(self, websocket):
        self.websockets[websocket] = []
        if self.history:
            for item in self.history:
                await self.send(websocket, item)

    async def send(self, websocket, data):
        if data in self.websockets[websocket]:
            return
        await websocket.send(json.dumps(data))
        self.websockets[websocket].append(data)
        self.websockets[websocket] = (
            self.websockets[websocket][0-self.keep_items:]
        )

    def clean_websockets(self):
        for websocket in list(self.websockets):
            if websocket.state != 1:
                del self.websockets[websocket]

    async def run(self):
        while True:
            self.clean_websockets()
            try:
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
                self.history = self.history[0-self.keep_items:]
                await asyncio.sleep(self.sleep_time)
