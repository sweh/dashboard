import requests
import datetime
from clients.baseclient import BaseClient
from datetime import date, timedelta


class Client(BaseClient):

    corona_url = 'https://api.corona-zahlen.org/districts/15091'
    # https://api.corona-zahlen.org/districts/15091/history/incidence/5
    external = True
    keep_items = 15
    type_ = 'Corona'
    tage = {
        6: 'So', 0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa'
    }

    @property
    def data(self):
        result = requests.get(self.corona_url).json()
        dtstand = datetime.datetime.fromisoformat(
            result['meta']['lastUpdate'].replace('T', ' ').replace('Z', '')
        ).date()
        today = date.today()
        if dtstand == today:
            stand = 'heute'
        elif dtstand == (today - timedelta(days=1)):
            stand = 'gestern'
        else:
            stand = dtstand.strftime('%d.%m.%Y')
        data = result['data']['15091']
        gesamt = f"{data['cases']} (+{data['delta']['cases']})"
        inzidenz = round(data['weekIncidence'])
        inzidenzen = [
            (h.get('tag', ''), h['inzidenz'])
            for h in self.history._data[-6:-1]
        ]
        inzidenzen = list(set(inzidenzen))
        inzidenzen = inzidenzen[-5:]
        today = (self.tage[dtstand.weekday()], inzidenz)
        if today not in inzidenzen:
            inzidenzen.append(today)
        return dict(
            stand=stand,
            tag=self.tage[dtstand.weekday()],
            gesamt=gesamt,
            inzidenz=inzidenz,
            inzidenzen=inzidenzen
        )
