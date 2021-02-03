import libtado.api
import gocept.cache.method
from clients.baseclient import BaseClient
import asyncio


class Client(BaseClient):

    type_ = 'Tado'
    sleep_time = 60
    external = True

    def __init__(self, config):
        self.username = config.get("TADO", "username")
        self.password = config.get("TADO", "password")
        self.secret = config.get("TADO", "secret")
        super(Client, self).__init__(config)

    @gocept.cache.method.Memoize(120)
    def api(self):
        return libtado.api.Tado(self.username, self.password, self.secret)

    async def set_status(self, data):
        if 'dest_temp' in data:
            self.api().set_temperature(
                int(data['zone']),
                float(data['dest_temp'])
            )
            await asyncio.sleep(4)
            await self.run(once=True)

    @property
    def data(self):
        result = {}
        for zone in self.api().get_zones():
            item = dict(name=zone['name'])
            state = self.api().get_state(zone['id'])
            item['curr_temp'] = (
                state['sensorDataPoints']['insideTemperature']['celsius']
            )
            item['curr_humi'] = (
                state['sensorDataPoints']['humidity']['percentage']
            )
            item['dest_temp'] = state['setting']['temperature']['celsius']
            item['heating_power'] = (
                state['activityDataPoints']['heatingPower']['percentage']
            )
            result[zone['id']] = item
        return result
