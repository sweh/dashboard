from clients.baseclient import BaseClient
import os
from helios_com import COM
import time


class Client(BaseClient):

    sleep_time = 900  # seconds
    type_ = 'Helios'
    conn_active_filename = '/tmp/helios_client_active'

    def activate_conn(self):
        self.slept = 0
        while os.path.exists(self.conn_active_filename):
            if self.slept >= 5:
                os.remove(self.conn_active_filename)
                break
            self.slept += 1
            time.sleep(1)
        with open(self.conn_active_filename, 'w') as f:
            f.write('')

    async def set_status(self, data):
        value = data['stufe']
        self.activate_conn()
        try:
            com = COM('10.0.1.64')
            try:
                com.set_fan_stage(value)
            finally:
                com.exit()
        finally:
            os.remove(self.conn_active_filename)
        await self.run(once=True)

    def grab_helios_data(self):
        self.activate_conn()
        try:
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
        finally:
            os.remove(self.conn_active_filename)

    @property
    def data(self):
        result = self.grab_helios_data()
        if not result:
            return
        old_value = self.history.get_last_entry()
        if old_value:
            for key in (
                'stufe', 'aussenluft', 'zuluft',
                'fortluft', 'abluft', 'abluft_feuchte'
            ):
                if old_value[key] > result[key]:
                    result[key + '_tendency'] = 'down'
                elif old_value[key] < result[key]:
                    result[key + '_tendency'] = 'up'
        return result
