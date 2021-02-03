from clients.baseclient import BaseClient
from PyViCare.PyViCareGazBoiler import GazBoiler
import gocept.cache.method
import asyncio


class Client(BaseClient):

    # LIMIT
    # 120 calls for a time window of 10 minutes
    # 1450 calls for a time window of 24 hours

    type_ = 'ViCare'
    sleep_time = 180  # 17h * 20 runs * 4 requests + 68 inits = 1428 requests
    external = True
    td = 7  # Temperaturdifferenz, da der Sensor zu tief im Boiler hängt

    def __init__(self, config):
        self.username = config.get("VICARE", "username")
        self.password = config.get("VICARE", "password")
        super(Client, self).__init__(config)

    @gocept.cache.method.Memoize(900)
    def boiler(self):
        try:
            return GazBoiler(
                self.username,
                self.password,
                token_file="token.save"
            )
        except KeyError:
            raise RuntimeError('Limit exceeded')

    async def set_status(self, data):
        if 'hot_water' in data:
            value = int(data['hot_water']) - self.td
            self.boiler().setDomesticHotWaterTemperature(value)
        await asyncio.sleep(2)
        await self.run(once=True)

    @property
    def data(self):
        boiler = self.boiler()

        # Single requests to the ViCareApi
        water_temp = boiler.getDomesticHotWaterStorageTemperature()
        water_temp_config = boiler.getDomesticHotWaterConfiguredTemperature()
        water_charging = boiler.getDomesticHotWaterChargingActive()
        burner_active = boiler.getBurnerActive()
        # circulation_active = boiler.getCirculationPumpActive()
        # hot_water_pump_active = boiler.getDomesticHotWaterPumpActive()

        result = dict(
            hot_water_current=round(water_temp) + self.td,
            hot_water_current_tendency='right',
            hot_water_config=round(water_temp_config) + self.td,
            burner_active=burner_active,
            hot_water_charging=water_charging,
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
