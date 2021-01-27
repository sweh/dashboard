import requests
import lnetatmo
from baseclient import BaseClient


class NetatmoClient:

    user = None
    password = None
    client_id = None
    client_secret = None

    def __init__(self, config):
        self.user = config.get("WEATHER", 'netatmo_user')
        self.password = config.get("WEATHER", 'netatmo_password')
        self.client_id = config.get("WEATHER", 'netatmo_client_id')
        self.client_secret = config.get("WEATHER", 'netatmo_client_secret')

    def authenticate(self):
        authorization = lnetatmo.ClientAuth(
            self.client_id,
            self.client_secret,
            self.user,
            self.password,
            scope="read_station"
        )
        return lnetatmo.WeatherStationData(authorization)

    @property
    def weatherData(self):
        result = dict()
        weatherData = self.authenticate()

        station = weatherData.stationByName('Am Wachtelberg 14 (Wohnzimmer)')
        for module in station['modules']:
            if module['type'] == 'NAModule1':
                result['out_temp_battery'] = module['battery_percent']
                result['out_temp'] = module['dashboard_data']['Temperature']
                result['out_temp_min'] = module['dashboard_data']['min_temp']
                result['out_temp_max'] = module['dashboard_data']['max_temp']
                result['out_humi'] = module['dashboard_data']['Humidity']
                temp_trend = module['dashboard_data']['temp_trend']
                temp_trend = (
                    'right' if temp_trend == 'stable' else temp_trend
                )
                result['out_temp_trend'] = temp_trend
            elif module['type'] == 'NAModule3':
                result['rain_battery'] = module['battery_percent']
                result['rain'] = module['dashboard_data']['Rain']
                result['rain_1'] = module['dashboard_data']['sum_rain_1']
                result['rain_24'] = module['dashboard_data']['sum_rain_24']
            elif module['type'] == 'NAModule2':
                result['wind_battery'] = module['battery_percent']
                result['wind_str'] = module['dashboard_data']['WindStrength']
                result['wind_angle'] = module['dashboard_data']['WindAngle']
            elif module['type'] == 'NAModule4':
                result['temp_in_battery'] = module['battery_percent']
                result['in_temp'] = module['dashboard_data']['Temperature']
                result['in_humi'] = module['dashboard_data']['Humidity']
                result['in_co2'] = module['dashboard_data']['CO2']
        return result


class Client(BaseClient):

    open_weather_url = (
        'http://api.openweathermap.org/data/2.5/weather'
        '?q=Lutherstadt%20Wittenberg'
        '&units=metric'
        '&lang=de'
        '&appid='
    )
    type_ = 'Weather'

    @property
    def data(self):
        api_key = self.config.get("WEATHER", 'openweather_api_key')
        netatmo = NetatmoClient(self.config)
        result = requests.get(self.open_weather_url + api_key).json()
        result.update(netatmo.weatherData)
        return result
