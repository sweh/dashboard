import requests
import datetime
from clients.baseclient import BaseClient


class Client(BaseClient):

    corona_url = 'https://api.corona-zahlen.org/districts/15091'
    external = True
    keep_items = 15
    type_ = 'Corona'
    tage = {
        0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'
    }

    @property
    def data(self):
        result = requests.get(self.corona_url).json()
        dtstand = datetime.datetime.fromisoformat(
            result['meta']['lastUpdate'].replace('T', ' ').replace('Z', '')
        ).date()
        data = result['data']['15091']
        inzidenz = round(data['weekIncidence'])
        inzidenzen = []
        for h in self.history._data:
            value = (h.get('tag', ''), h['inzidenz'])
            if value not in inzidenzen:
                inzidenzen.append(value)
        today = (self.tage[dtstand.weekday()], inzidenz)
        if today != inzidenzen[-1]:
            inzidenzen.append(today)
        inzidenzen = inzidenzen[-5:]
        return dict(
            stand=dtstand.isoformat(),
            tag=self.tage[dtstand.weekday()],
            inzidenz=inzidenz,
            inzidenzen=inzidenzen
        )
