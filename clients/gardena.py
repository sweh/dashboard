from gardena.smart_system import SmartSystem
from clients.baseclient import BaseClient
import pprint


class Client(BaseClient):

    type_ = 'Gardena'
    external = True
    _data = None

    def __init__(self, config):
        self._data = {
            'Hochbeet': {},
            'Water Control': {},
        }

        def update_callback(device):
            if device.name == 'Hochbeet':
                self._data['Hochbeet'].update(
                    dict(
                        Batterie=device.battery_level,
                        BatterieStatus=device.battery_state,
                        LinkLevel=device.rf_link_level,
                        LinkState=device.rf_link_state,
                        Lufttemperatur=device.ambient_temperature,
                        Helligkeit=device.light_intensity,
                        Bodenfeuchte=device.soil_humidity,
                        Bodentemperatur=device.soil_temperature,
                    )
                )
            elif device.name == 'Water Control':
                self._data['Water Control'].update(
                    dict(
                        Batterie=device.battery_level,
                        BatterieStatus=device.battery_state,
                        LinkLevel=device.rf_link_level,
                        LinkState=device.rf_link_state,
                        Status=device.valve_activity
                    )
                )

        self.smart_system = smart_system = SmartSystem(
            email=config.get("GARDENA", "username"),
            password=config.get("GARDENA", "password"),
            client_id=config.get("GARDENA", "client_id")
        )
        smart_system.authenticate()
        smart_system.update_locations()
        for location in smart_system.locations.values():
            self.loc_id = location.id
            smart_system.update_devices(location)
            pprint.pprint(location)
            for device in location.devices.values():
                pprint.pprint(device)
                device.add_callback(update_callback)
        smart_system.start_ws(smart_system.locations[self.loc_id])
        super(Client, self).__init__(config)

    @property
    def data(self):
        return self._data

    async def set_status(self, data):
        if 'on' in data:
            if data['on']:
                self.smart_system.locations[
                    self.loc_id
                ].find_device_by_type("WATER_CONTROL")[0].unpause()
            else:
                self.smart_system.locations[
                    self.loc_id
                ].find_device_by_type("WATER_CONTROL")[0].pause()
        await self.run(once=True)
