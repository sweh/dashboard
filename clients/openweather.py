import requests
from clients.baseclient import BaseClient


class Client(BaseClient):

    type_ = 'Weather'
    external = False
    sleep_time = 900

    user = None
    password = None
    client_id = None
    client_secret = None

    def authenticate(self):
        import lnetatmo
        authorization = lnetatmo.ClientAuth()
        return lnetatmo.WeatherStationData(authorization)

    def get_update_with_netatmo_data(self, weatherData):
        result = dict()

        station = weatherData.stationByName('Am Wachtelberg 14 (Wohnzimmer)')
        for module in station['modules']:
            if module['type'] == 'NAModule1':
                result['out_temp'] = module['dashboard_data']['Temperature']
            if module['type'] == 'NAModule3':
                result['rain'] = module['dashboard_data']['sum_rain_24']
            if module['type'] == 'NAModule2':
                result['wind'] = module['dashboard_data']['WindStrength']

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
            weatherData.default_station_data = weatherData.stationByName(station_name)
            weatherData_ = weatherData.lastData(exclude=3600)
            if weatherData_:
                for module, moduleData in weatherData_.items():
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
        try:
            weatherData = self.authenticate()
            self.save_weather_to_influx(weatherData)
            result = self.get_update_with_netatmo_data(weatherData)
        except Exception:
            result = {'rain': 0, 'wind': 0}
        api_key = self.config.get("WEATHER", 'openweather_api_key')
        if api_key:
            url = (
                f'https://api.openweathermap.org/data/3.0/onecall?'
                'units=metric&lang=de&'
                'lat=51.888689135586574&lon=12.647285179149327&'
                f'appid={api_key}'
            )
            data = requests.get(url, timeout=5).json()
            if 'out_temp' not in result:
                result['out_temp'] = data['current']['temp']
            result.update(data)
        return result
