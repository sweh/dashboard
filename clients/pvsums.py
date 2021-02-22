from model import PVSums
from history import sqlalchemy_encode
from sqlalchemy.orm import sessionmaker
from clients.baseclient import BaseClient


class Client(BaseClient):

    sleep_time = 5
    type_ = 'PVSums'
    keep_items = 365

    def __init__(self, *args, **kw):
        super(Client, self).__init__(*args, **kw)
        self.session = sessionmaker(bind=self.config.engine)()

    @property
    def data(self):
        item = (
            self.session.query(PVSums)
            .order_by(PVSums._timestamp.desc())
            .first()
        )
        item = sqlalchemy_encode(item)
        item['DeviceClass'] = self.type_
        self.history._data[-1] = item
        return item

    async def prepare_send(self, result):
        for websocket in list(self.websockets):
            await self.send(websocket, result)
