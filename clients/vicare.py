from clients.baseclient import BaseClient
from PyViCare.PyViCare import PyViCare
import gocept.cache.method
import asyncio


class Client(BaseClient):

    # LIMIT
    # 120 calls for a time window of 10 minutes
    # 1450 calls for a time window of 24 hours

    type_ = 'ViCare'
    # sleep_time = 300  # 17h * 12 runs * 6 requests + 68 inits = 1292 requests
    sleep_time = 3600
    external = True

    def __init__(self, config):
        self.username = config.get("VICARE", "username")
        self.password = config.get("VICARE", "password")
        self.client_key = config.get("VICARE", "client_key")
        super(Client, self).__init__(config)

    @gocept.cache.method.Memoize(900)
    def boiler(self):
        try:
            vicare = PyViCare()
            vicare.initWithCredentials(
                self.username, self.password, self.client_key, "token.save"
            )
            return vicare.devices[0].asAutoDetectDevice()
        except KeyError:
            raise RuntimeError('Limit exceeded')

    async def set_status(self, data):
        if 'hot_water' in data:
            value = int(data['hot_water'])
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
        solar_collector_temp = boiler.getSolarCollectorTemperature()
        solar_pump_active = boiler.getSolarPumpActive()
        # circulation_active = boiler.getCirculationPumpActive()
        # hot_water_pump_active = boiler.getDomesticHotWaterPumpActive()

        result = dict(
            hot_water_current=water_temp,
            hot_water_current_tendency='right',
            hot_water_config=water_temp_config,
            burner_active=burner_active,
            hot_water_charging=water_charging,
            solar_collector_temp=solar_collector_temp,
            solar_pump_active=solar_pump_active,
        )
        if not result:
            return
        for k, v in result.items():
            if v == 'error':
                return
        old_value = self.history.get_last_entry()
        if old_value:
            for key in ('hot_water_current', ):
                if old_value[key] > result[key]:
                    result[key + '_tendency'] = 'down'
                elif old_value[key] < result[key]:
                    result[key + '_tendency'] = 'up'
        return result
