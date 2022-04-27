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
    # sleep_time = 3600
    # sleep_time = 10
    sleep_time = 60
    external = False

    def __init__(self, config):
        self.username = config.get("VICARE", "username")
        self.password = config.get("VICARE", "password")
        self.client_key = config.get("VICARE", "client_key")
        super(Client, self).__init__(config)

    @gocept.cache.method.Memoize(86400)
    def boiler(self):
        vicare = PyViCare()
        vicare.initWithCredentials(
            self.username, self.password, self.client_key, "token.save"
        )
        return vicare.devices[0].asAutoDetectDevice()

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
        water_temp_config = boiler.getDomesticHotWaterDesiredTemperature()
        outside_temp = boiler.getOutsideTemperature()

        solar_collector_temp = boiler.getSolarCollectorTemperature()
        solar_pump_active = boiler.getSolarPumpActive()

        burner_active = boiler.burners[0].getActive()
        water_charging_active = boiler.getDomesticHotWaterChargingActive()
        hot_water_pump_active = boiler.getDomesticHotWaterPumpActive()

        hk0 = boiler.getCircuit(1)
        supply_temp_hk1 = hk0.getSupplyTemperature()
        target_supply_temp_hk1 = hk0.getTargetSupplyTemperature()
        circulation_active = hk0.getCirculationPumpActive()

        # hk1 = boiler.getCircuit(1)
        # supply_temp_hk2 = hk1.getSupplyTemperature()
        # target_supply_temp_hk2 = (
        #     hk1.getTargetSupplyTemperature() or supply_temp_hk2
        # )
        supply_temp_hk2 = 0
        target_supply_temp_hk2 = 0

        gas_consumption_hot_water_today = (
            boiler.getGasConsumptionDomesticHotWaterToday()
        )
        gas_consumption_heating_today = boiler.getGasConsumptionHeatingToday()
        solar_power_production_today = boiler.getSolarPowerProductionToday()

        result = dict(
            outside_temp=outside_temp,
            hot_water_current=water_temp,
            hot_water_current_tendency='right',
            hot_water_config=water_temp_config,
            burner_active=burner_active,
            hot_water_charging=water_charging_active,
            solar_collector_temp=solar_collector_temp,
            solar_pump_active=solar_pump_active,
            circulation_active=circulation_active,
            hot_water_pump_active=hot_water_pump_active,
            supply_temp_hk1=supply_temp_hk1,
            target_supply_temp_hk1=target_supply_temp_hk1,
            supply_temp_hk2=supply_temp_hk2,
            target_supply_temp_hk2=target_supply_temp_hk2,
            gas_consumption_hot_water_today=gas_consumption_hot_water_today,
            gas_consumption_heating_today=gas_consumption_heating_today,
            solar_power_production_today=solar_power_production_today,

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
