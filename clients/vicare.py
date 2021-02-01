from clients.baseclient import BaseClient
from PyViCare.PyViCareGazBoiler import GazBoiler
import gocept.cache.method
import asyncio


class Client(BaseClient):

    type_ = 'ViCare'
    sleep_time = 120
    td = 5  # Temperaturdifferenz, da der Sensor zu tief im Boiler hängt

    def __init__(self, config):
        self.username = config.get("VICARE", "username")
        self.password = config.get("VICARE", "password")
        super(Client, self).__init__(config)

    @gocept.cache.method.Memoize(120)
    def boiler(self):
        return GazBoiler(self.username, self.password, "token.save")

    async def set_status(self, data):
        if 'hot_water' in data:
            value = int(data['hot_water']) - self.td
            self.boiler().setDomesticHotWaterTemperature(value)
        await asyncio.sleep(2)
        await self.run(once=True)

    @property
    def data(self):
        boiler = self.boiler()
        result = dict(
            hot_water_current=(
                round(boiler.getDomesticHotWaterStorageTemperature()) + self.td
            ),
            hot_water_current_tendency='right',
            hot_water_config=(
                round(boiler.getDomesticHotWaterConfiguredTemperature()) +
                self.td
            ),
            burner_active=boiler.getBurnerActive(),
            hot_water_charging=boiler.getDomesticHotWaterChargingActive(),
            circulation_active=boiler.getCirculationPumpActive(),
            hot_water_pump_active=boiler.getDomesticHotWaterPumpActive(),
        )
        if not result:
            return
        for k, v in result.items():
            if v == 'error':
                return
        if self.history:
            old_value = self.history[-1]
            for key in ('hot_water_current', ):
                if old_value[key] > result[key]:
                    result[key + '_tendency'] = 'down'
                elif old_value[key] < result[key]:
                    result[key + '_tendency'] = 'up'
        return result
