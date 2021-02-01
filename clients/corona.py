import requests
from clients.baseclient import BaseClient


class Client(BaseClient):

    corona_url = (
        'https://www.landkreis-wittenberg.de/de/informationen-zum-coronavirus'
        '-im-landkreis-wittenberg/informationen-zum-coronavirus.html'
    )
    type_ = 'Corona'

    @property
    def data(self):
        result = requests.get(self.corona_url).text
        stand = result.split('(Stand ')[1][:21]
        gesamt = (
            result
            .split('Im Landkreis Wittenberg wurden ')[1]
            .split(' Infektionen')[0]
        )
        aktuell = (
            result
            .split('Aktuell infiziert sind ')[1].split(' ')[0]
        )
        gestorben = (
            result.split('Patienten. ')[1].split(' ')[0]
        )
        inzidenz = (
            result.split('wöchentliche Inzidenz von ')[1].split(' ')[0]
        )
        return dict(
            stand=stand,
            gesamt=gesamt,
            aktuell=aktuell,
            gestorben=gestorben,
            inzidenz=inzidenz
        )
