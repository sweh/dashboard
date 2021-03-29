import requests
from clients.baseclient import BaseClient
from datetime import date, timedelta


class Client(BaseClient):

    corona_url = (
        'https://www.landkreis-wittenberg.de/de/informationen-zum-coronavirus'
        '-im-landkreis-wittenberg/informationen-zum-coronavirus.html'
    )
    external = True
    type_ = 'Corona'

    @property
    def data(self):
        result = requests.get(self.corona_url).text
        stand = result.split('(Stand ')[1][:10]
        today = date.today()
        if stand == today.strftime('%d.%m.%Y'):
            stand = 'heute'
        if stand == (today - timedelta(days=1)).strftime('%d.%m.%Y'):
            stand = 'gestern'
        gesamt = (
            result
            .split('Im Landkreis Wittenberg wurden ')[1]
            .split(' Infektionen')[0]
        )
        aktuell = (
            result
            .split('Aktuell sind ')[1].split(' ')[0]
        )
        gestorben = (
            result.split('infiziert. ')[1].split(' ')[0]
        )
        inzidenz = (
            result
            .split('Inzidenz von ')[1]
            .split(') ')[0]
            .replace('<strong>', '')
            .replace('</strong>', '')
        )
        inzidenz_plus = inzidenz.split(' (')[1]
        inzidenz = inzidenz.split(' (')[0]
        return dict(
            stand=stand,
            gesamt=gesamt,
            aktuell=aktuell,
            gestorben=gestorben,
            inzidenz=inzidenz,
            inzidenz_plus=inzidenz_plus
        )
