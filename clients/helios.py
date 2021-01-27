from clients.baseclient import BaseClient
from helios_com import COM


class Client(BaseClient):

    type_ = 'Helios'

    def set_stufe(self, value):
        com = COM('10.0.1.64')
        try:
            com.set_fan_stage(value)
        finally:
            com.exit()

    def grab_helios_data(self):
        com = COM('10.0.1.64')
        try:
            fanLevel = com.read_fan_stage()
            outTemp, suppTemp, exhaustTemp, extractTemp = com.read_temp()
            exhaustHumid = com.read_humidity()
        except Exception:
            return
        finally:
            com.exit()
        return dict(
            stufe=fanLevel,
            stufe_tendency='right',
            aussenluft=outTemp,
            aussenluft_tendency='right',
            zuluft=suppTemp,
            zuluft_tendency='right',
            fortluft=extractTemp,
            fortluft_tendency='right',
            abluft=exhaustTemp,
            abluft_tendency='right',
            abluft_feuchte=exhaustHumid,
            abluft_feuchte_tendency='right',
        )

    @property
    def data(self):
        result = self.grab_helios_data()
        if not result:
            return
        if self.history:
            old_value = self.history[-1]
            for key in (
                'stufe', 'percent', 'aussenluft', 'zuluft',
                'fortluft', 'abluft', 'abluft_feuchte'
            ):
                if old_value[key] > result[key]:
                    result[key + '_tendency'] = 'down'
                elif old_value[key] < result[key]:
                    result[key + '_tendency'] = 'up'
        return result
