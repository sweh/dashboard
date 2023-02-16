import requests
import pytz
import datetime
from clients.baseclient import BaseClient


class Client(BaseClient):

    api_urls = (
        'https://api.forecast.solar/estimate/51.8887/12.6473/22/-110/3.9',
        'https://api.forecast.solar/estimate/51.8887/12.6473/22/-20/2.1',
        'https://api.forecast.solar/estimate/51.8887/12.6473/22/70/3.9',
    )
    external = True
    sleep_time = 3600
    keep_items = 1
    type_ = 'PVForecast'

    @property
    def data(self):
        forecast_raw = []
        forecast_raw_day = []
        for url in self.api_urls:
            r = requests.get(url, timeout=5).json()
            if r['result'] is None:
                raise ValueError(r['message'])
            forecast_raw.append(r['result']['watts'])
            forecast_raw_day.append(r['result']['watt_hours_day'])
        forecast = []
        today = datetime.date.today().isoformat()
        for ts in forecast_raw[0].keys():
            if not ts.startswith(today):
                continue
            watts = (
                forecast_raw[0][ts] + forecast_raw[1][ts] + forecast_raw[2][ts]
            )
            local = pytz.timezone("Europe/Berlin")
            naive = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            # 2023-02-16T09:16:24.882Z
            ts = utc_dt.isoformat()[:19] + '.000Z'
            forecast.append(dict(timestamp=ts, value=watts))
        forecast_day = 0
        for item in forecast_raw_day:
            forecast_day += item[today]
        return dict(
            forecast=forecast,
            forecast_day=forecast_day
        )
