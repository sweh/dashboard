from clients.baseclient import BaseClient
from PyViCare.PyViCareGazBoiler import GazBoiler
import gocept.cache.method
import asyncio


class Client(BaseClient):

    type_ = 'ViCare'

    def __init__(self, config):
        self.username = config.get("VICARE", "username")
        self.password = config.get("VICARE", "password")
        super(Client, self).__init__(config)

    @gocept.cache.method.Memoize(120)
    def boiler(self):
        return GazBoiler(self.username, self.password, "token.save")

    async def set_status(self, data):
        if 'hot_water' in data:
            self.boiler().setDomesticHotWaterTemperature(data['hot_water'])
        await asyncio.sleep(2)
        await self.run(once=True)

    @property
    def data(self):
        boiler = self.boiler()
        result = dict(
            hot_water_current=boiler.getDomesticHotWaterStorageTemperature(),
            hot_water_current_tendency='right',
            hot_water_config=boiler.getDomesticHotWaterConfiguredTemperature(),
            burner_active=boiler.getBurnerActive(),
            hot_water_charging=boiler.getDomesticHotWaterChargingActive(),
            circulation_active=boiler.getCirculationPumpActive(),
            hot_water_pump_active=boiler.getDomesticHotWaterPumpActive(),
        )
        if not result:
            return
        if self.history:
            old_value = self.history[-1]
            for key in ('hot_water_current', ):
                if old_value[key] > result[key]:
                    result[key + '_tendency'] = 'down'
                elif old_value[key] < result[key]:
                    result[key + '_tendency'] = 'up'
        return result
