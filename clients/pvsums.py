import logging
from model import PVSums
from history import sqlalchemy_encode
from clients.baseclient import BaseClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Client(BaseClient):

    sleep_time = 5
    type_ = 'PVSums'
    keep_items = 365

    @property
    def data(self):
        log.info(f'{self.type_} fetching new data.')
        session = self.history.session
        item = (
            session.query(PVSums)
            .order_by(PVSums._timestamp.desc())
            .first()
        )
        log.info(f'{self.type_} fetched new data.')
        item = sqlalchemy_encode(item)
        item['DeviceClass'] = self.type_
        log.info(f'{self.type_} prepared new data...')
        if self.history._data[-1]['day'] == item['day']:
            log.info(f'{self.type_} updated for current day.')
            self.history._data[-1] = item
        else:
            log.info(f'{self.type_} appended for new day.')
            self.history._data.append(item)
        return item

    async def prepare_send(self, result):
        log.info(
            f'{self.type_} fetched new data, sending to '
            f'{len(self.websockets)} clients.'
        )
        for websocket in list(self.websockets):
            await self.send(websocket, result)
