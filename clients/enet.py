from clients.baseclient import BaseClient
from aioenet import EnetClient


class Client(BaseClient):

    type_ = 'eNet'
    url = 'http://10.0.1.12'
    username = None
    password = None

    def __init__(self, config):
        self.username = config.get("ENET", "username")
        self.password = config.get("ENET", "password")

    @property
    def data(self):
        return {}

    async def setup(self):
        self.devices = {}

        client = EnetClient(self.url, self.username, self.password)
        await client.simple_login()

        for device in await client.get_devices():
            location = device.location.split(':')[-1]
            if not device.channels:
                continue
            channel = device.channels[0]
            type_ = channel.name
            current_value = await channel.get_value()
            if location not in self.devices:
                self.devices[location] = []
            self.devices[location].append(
                dict(type=type_, value=current_value, channel=channel)
            )

    async def set_status(self, data):
        action = data['action']

        await self.setup()

        if action == 'open':
            for location, devices in self.devices.items():
                for device in devices:
                    await device['channel'].set_value(0)
