from hue_api import HueApi
from clients.baseclient import BaseClient
import os


class Client(BaseClient):

    type_ = 'Hue'
    ip = '10.0.1.108'
    cache_file = None

    def __init__(self, config):
        if not int(config.get("HUE", "enabled")):
            return
        self.cache_file = config.get("HUE", "cache_file")
        self.ip = config.get("HUE", "ip")
        super(Client, self).__init__(config)
        self.api = HueApi()
        if not os.path.exists(self.cache_file):
            self.api.create_new_user(self.ip)
            self.api.save_api_key(cache_file=self.cache_file)
        self.api.load_existing(cache_file=self.cache_file)

    async def set_status(self, data):
        if 'on' in data:
            if data['on']:
                self.api.turn_on([int(data['id'])])
            else:
                self.api.turn_off([int(data['id'])])
        elif 'bri' in data:
            self.api.set_brightness(data['bri'], [int(data['id'])])
        await self.run(once=True)

    @property
    def data(self):
        result = {}
        for light in self.api.fetch_lights():
            if not light.state.reachable:
                continue
            if light.name in ('Papa', 'Aussen'):
                continue
            result[light.id] = light.state.to_payload()
            result[light.id]['name'] = light.name
        return result
