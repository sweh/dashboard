import requests
import lnetatmo
from clients.baseclient import BaseClient


class Client(BaseClient):

    type_ = 'Weather'
    external = False
    sleep_time = 900

    user = None
    password = None
    client_id = None
    client_secret = None

    def __init__(self, config):
        self.user = config.get("WEATHER", 'netatmo_user')
        self.password = config.get("WEATHER", 'netatmo_password')
        self.client_id = config.get("WEATHER", 'netatmo_client_id')
        self.client_secret = config.get("WEATHER", 'netatmo_client_secret')
        super(Client, self).__init__(config)

    def authenticate(self):
        authorization = lnetatmo.ClientAuth(
            self.client_id,
            self.client_secret,
            self.user,
            self.password,
            scope="read_station"
        )
        return lnetatmo.WeatherStationData(authorization)

    def get_outside_temperature(self, weatherData):
        result = dict()

        station = weatherData.stationByName('Am Wachtelberg 14 (Wohnzimmer)')
        for module in station['modules']:
            if module['type'] == 'NAModule1':
                result['out_temp'] = module['dashboard_data']['Temperature']

        return result

    def save_weather_to_influx(self, weatherData):
        client = self.get_influx_client(db='netatmo')
        if not client:
            return

        for station in weatherData.stations:
            station_data = []
            module_data = []
            station = weatherData.stationById(station)
            station_name = station['station_name']
            altitude = station['place']['altitude']
            country= station['place']['country']
            timezone = station['place']['timezone']
            longitude = station['place']['location'][0]
            latitude = station['place']['location'][1]
            for module, moduleData in weatherData.lastData(station=station_name, exclude=3600).items():
                for measurement in ['altitude', 'country', 'longitude', 'latitude', 'timezone']:
                    value = eval(measurement)
                    if type(value) == int:
                        value = float(value)
                    station_data.append({
                        "measurement": measurement,
                        "tags": {
                            "station": station_name,
                            "module": module
                        },
                        "time": moduleData['When'],
                        "fields": {
                            "value": value
                        }
                    })

                for sensor, value in moduleData.items():
                    if sensor.lower() != 'when':
                        if type(value) == int:
                            value = float(value)
                        module_data.append({
                            "measurement": sensor.lower(),
                            "tags": {
                                "station": station_name,
                                "module": module
                            },
                            "time": moduleData['When'],
                            "fields": {
                                "value": value
                            }
                        })

            client.write_points(station_data, time_precision='s')
            client.write_points(module_data, time_precision='s')

    @property
    def data(self):
        weatherData = self.authenticate()
        self.save_weather_to_influx(weatherData)
        result = self.get_outside_temperature(weatherData)
        api_key = self.config.get("WEATHER", 'openweather_api_key')
        if api_key:
            url = (
                f'https://api.openweathermap.org/data/2.5/onecall?'
                'units=metric&lang=de&'
                'lat=51.888689135586574&lon=12.647285179149327&'
                f'appid={api_key}'
            )
            data = requests.get(url, timeout=5).json()
            result.update(data)
        return result
