from clients.baseclient import BaseClient


class Client(BaseClient):

    type_ = 'WIFI'
    sleep_time = 3600*12

    @property
    def data(self):
        return {'password': self.config.get('WIFI', 'password')}
