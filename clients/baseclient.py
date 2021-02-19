import asyncio
from datetime import datetime
from history import History
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class BaseClient:

    sleep_time = 60
    keep_items = 1
    history = None
    websockets = None
    external = False
    enabled = False
    external_operation_time = ('05:30', '22:30')
    type_ = None

    def __init__(self, config):
        self.config = config
        self.enabled = bool(int(config.get(self.type_.upper(), 'enabled')))
        self.history = History(self.type_, config.engine, max_items=self.keep_items)
        self.websockets = {}

    async def register(self, websocket):
        self.websockets[websocket] = []
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

    def assert_operation_time(self):
        if not self.external:
            return
        min_, max_ = self.external_operation_time
        min_hour, min_minute = min_.split(':')
        max_hour, max_minute = max_.split(':')
        now = datetime.now()
        if now < datetime(
            now.year, now.month, now.day, int(min_hour), int(min_minute)
        ):
            raise RuntimeError('Operation time not reached')
        if now > datetime(
            now.year, now.month, now.day, int(max_hour), int(max_minute)
        ):
            raise RuntimeError('Operation time not reached')

    async def run(self, once=False):
        while True:
            self.clean_websockets()
            try:
                self.assert_operation_time()
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
                if once:
                    return
                await asyncio.sleep(self.sleep_time)
