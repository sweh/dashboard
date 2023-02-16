import requests
import datetime
from clients.baseclient import BaseClient


class Client(BaseClient):

    api_urls = (
        'https://api.forecast.solar/estimate/51.8887/12.6473/22/-110/3.9',
        'https://api.forecast.solar/estimate/51.8887/12.6473/22/-20/2.1',
        'https://api.forecast.solar/estimate/51.8887/12.6473/22/70/3.9',
    )
    external = True
    sleep_time = 900
    keep_items = 0
    type_ = 'PVForecast'

    @property
    def data(self):
        forecast_raw = []
        for url in self.api_urls:
            try:
                forecast_raw.append(
                    requests.get(url, timeout=5).json()['result']['watts']
                )
            except Exception:
                return
        forecast = []
        today = datetime.date.today().isoformat()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:')
        start = False
        for ts in forecast_raw[0].keys():
            if not start and not ts.startswith(now):
                continue
            start = True
            if not ts.startswith(today):
                continue
            watts = (
                forecast_raw[0][ts] + forecast_raw[1][ts] + forecast_raw[2][ts]
            )
            forecast.append(dict(timestamp=ts, value=watts))
        return dict(
            forecast=forecast
        )
