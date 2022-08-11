from gardena.smart_system import SmartSystem
from clients.baseclient import BaseClient
import pprint


class Client(BaseClient):

    type_ = 'Gardena'
    external = True
    _data = None

    def __init__(self, config):
        super(Client, self).__init__(config)
        if not self.enabled:
            return
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
        try:
            smart_system.authenticate()
        except Exception:
            pass
        else:
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
        location = self.smart_system.locations[self.loc_id]
        water_control = location.find_device_by_type("WATER_CONTROL")[0]
        if 'on' in data:
            if data['on']:
                water_control.start_seconds_to_override(3600)
            else:
                water_control.stop_until_next_task()
        await self.run(once=True)
