import gocept.cache.method
from model import PVSums
from history import sqlalchemy_encode
from sqlalchemy.orm import sessionmaker
from clients.baseclient import BaseClient


class Client(BaseClient):

    sleep_time = 5
    type_ = 'PVSums'
    keep_items = 365

    @property
    def data(self):
        session = self.history.session
        item = (
            session.query(PVSums)
            .order_by(PVSums._timestamp.desc())
            .first()
        )
        item = sqlalchemy_encode(item)
        item['DeviceClass'] = self.type_
        if self.history._data[-1]['day'] == item['day']:
            self.history._data[-1] = item
        else:
            self.history._data.append(item)
        return item

    async def prepare_send(self, result):
        for websocket in list(self.websockets):
            await self.send(websocket, result)
