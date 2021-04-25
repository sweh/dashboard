import requests
import datetime
from clients.baseclient import BaseClient
from datetime import date, timedelta


class Client(BaseClient):

    corona_url = 'https://api.corona-zahlen.org/districts/15091'
    external = True
    type_ = 'Corona'

    @property
    def data(self):
        result = requests.get(self.corona_url).json()
        stand = datetime.datetime.fromisoformat(
            result['meta']['lastUpdate'].replace('T', ' ').replace('Z', '')
        ).date()
        today = date.today()
        if stand == today:
            stand = 'heute'
        elif stand == (today - timedelta(days=1)):
            stand = 'gestern'
        else:
            stand = stand.strftime('%d.%m.%Y')
        data = result['data']['15091']
        gesamt = f"{data['cases']} (+{data['delta']['cases']})"
        inzidenz = round(data['weekIncidence'])
        return dict(
            stand=stand,
            gesamt=gesamt,
            inzidenz=inzidenz,
        )
