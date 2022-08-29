import json
import requests
from datetime import datetime, timedelta
from speedwiredecoder import decode_speedwire
from clients.baseclient import BaseClient


EVCHARGERKEYMAP = {
    'Measurement.Metering.GridMs.TotWIn.ChaSta': 'AC Power Wallbox',
    'Measurement.Operation.Health': 'WallboxHealth',
    'Measurement.Operation.EVeh.ChaStt': 'WallboxState',
}


class Client(BaseClient):

    sleep_time = 5
    type_ = 'PV'
    keep_items = 1000
    kw_price = 0.2769
    max_battery = 9600
    hueclient = None
    windrad_running = False

    def __init__(self, smadaemon, hueclient):
        self.smadaemon = smadaemon
        self.ev_charger_ip = hueclient.config.get("PV", 'ev_charger_ip')
        self.ev_charger_user = hueclient.config.get("PV", 'ev_charger_user')
        self.ev_charger_password = hueclient.config.get(
            "PV", 'ev_charger_password'
        )
        if hueclient.enabled:
            self.hueclient = hueclient
        super(Client, self).__init__(smadaemon.config)
        self.sock = smadaemon.connect_to_socket()

    def save_result_to_file(self, data):
        data = dict(
            panelpower=data['AC Power Solar'] or 0,
            batterypower=0-data['AC Power Battery'] or 0,
            power_from_grid=data['Power from grid'] or 0,
            power_to_grid=data['Power to grid'] or 0
        )
        data['consumption'] = (
                data['panelpower'] + data['batterypower'] +
                data['power_from_grid'] - data['power_to_grid']
        )
        if data['consumption'] < 0:
            data['consumption'] = 0 - data['consumption']
        data_file = self.config.get('FEATURE-pvdata', 'output_file')
        if data_file:
            with open(data_file, 'w') as f:
                f.write(json.dumps(data))

    def calculate_sums(self, result):
        fmt = "%Y-%m-%dT%H:%M:%S.%f%z"

        seconds = 1
        sums = dict()
        last_item = self.history.get_last_entry()
        if last_item:
            current = datetime.strptime(result['timestamp'], fmt)
            last = datetime.strptime(last_item['timestamp'], fmt)
            if current.day != last.day:
                seconds = 1
            else:
                seconds = current - last
                seconds = float(f'{seconds.seconds}.{seconds.microseconds}')
                sums = last_item['sums'].copy()
        if seconds == 0:
            seconds = 1
        for key in (
            'Consumption',
            'AC Power Solar',
            'Power to grid',
            'Power from grid'
        ):
            sums.setdefault(key, 0)
            if not last_item:
                r = result[key]
            else:
                r = ((result[key] + last_item[key]) / 2)
            sums[key] += r / 3600 * seconds
        sums.setdefault('AC Power Battery', 0)
        sums.setdefault('Power from battery', 0)

        if not last_item:
            battery_power = 0 - result['AC Power Battery']
        else:
            battery_power = 0 - ((
                result['AC Power Battery'] + last_item['AC Power Battery']
            ) / 2)
        if battery_power > 0:
            sums['AC Power Battery'] += (
                battery_power / 3600 * seconds
            )
        else:
            sums['Power from battery'] -= (
                battery_power / 3600 * seconds
            )
        result['sums'] = sums

    def calculate_costs(self, result):
        costs = dict()
        costs.setdefault('Power to grid', 0)
        costs['Power to grid'] = (
            result['sums']['Power to grid'] / 1000 * 0.0877
        )
        costs.setdefault('Power from grid', 0)
        costs['Power from grid'] = (
            result['sums']['Power from grid'] / 1000 * self.kw_price
        )
        costs.setdefault('Power saving', 0)
        costs['Power saving'] = (
            result['sums']['Consumption'] - result['sums']['Power from grid']
        ) / 1000 * self.kw_price
        result['costs'] = costs

    def calculate_costs_per_hour(self, result):
        costs_per_hour = dict()
        costs_per_hour.setdefault('Power to grid', 0)
        costs_per_hour['Power to grid'] = (
            result['Power to grid'] / 1000 * 0.0877
        )
        costs_per_hour.setdefault('Power from grid', 0)
        costs_per_hour['Power from grid'] = (
            result['Power from grid'] / 1000 * self.kw_price
        )
        costs_per_hour.setdefault('Power saving', 0)
        costs_per_hour['Power saving'] = (
            result['Consumption'] - result['Power from grid']
        ) / 1000 * self.kw_price
        result['costs_per_hour'] = costs_per_hour

    def get_ev_charger_data(self):
        if not self.ev_charger_ip:
            return {}
        try:
            resp = requests.post(
                f'http://{self.ev_charger_ip}/api/v1/token',
                data=dict(
                    grant_type='password',
                    username=self.ev_charger_user,
                    password=self.ev_charger_password,
                ),
                timeout=5
            )
            token = resp.json()['access_token']

            resp = requests.post(
                f'http://{self.ev_charger_ip}/api/v1/measurements/live/',
                json=[dict(componentId='IGULD:SELF')],
                headers=dict(Authorization=f'Bearer {token}'),
                timeout=5
            )

            result = {}
            for item in resp.json():
                key = EVCHARGERKEYMAP.get(item['channelId'])
                if key is None:
                    continue
                value = item['values'][0]['value']

                if key == 'WallboxState':
                    value = {
                        200111: 'nicht verbunden',
                        200112: 'verbunden',
                        200113: 'lädt'
                    }.get(value)
                if key == 'WallboxHealth':
                    value = 'Ok' if value == 307 else 'NA'

                result[key] = value
            return result
        except Exception:
            return {}

    @property
    def data(self):
        result = {}
        emparts = decode_speedwire(self.sock.recv(608))
        for serial in self.smadaemon.serials:
            if "serial" in emparts and serial == format(emparts["serial"]):
                for items in self.run_features(emparts):
                    for item in items:
                        if item['DeviceClass'] == 'Solar Inverter':
                            item['AC Power Solar'] = item['AC Power'] or 0
                            item['Status Solar'] = item['Status']
                        if item['DeviceClass'] == 'Battery Inverter':
                            item['AC Power Battery'] = item['AC Power'] or 0
                        result.update(item)
                result.update(self.get_ev_charger_data())
        result['Power to grid'] = result.get('Power to grid', 0) or 0
        result['AC Power Solar'] = result.get('AC Power Solar', 0) or 0
        result['AC Power Wallbox'] = int(
            result.get('AC Power Wallbox', 0) or 0
        )
        result['AC Power Battery'] = result.get('AC Power Battery', 0) or 0
        result['Power from grid'] = result.get('Power from grid', 0) or 0
        result['Consumption'] = (
            result['AC Power Solar'] +
            result['AC Power Battery'] -
            result['AC Power Wallbox'] +
            result['Power from grid'] -
            result['Power to grid']
        )
        if (result['Consumption'] == 0) or 'BatteryCharge' not in result:
            return
        result['BatteryChargeWatt'] = (
            self.max_battery * (result['BatteryCharge'] / 100)
        )
        if result['AC Power Battery'] == 0:
            amount_to_charge = self.max_battery
            hours = 24
            minutes = 0
        elif result['AC Power Battery'] < 0:
            # charge
            amount_to_charge = self.max_battery - result['BatteryChargeWatt']
            time = amount_to_charge / (0 - result['AC Power Battery'])
            hours = int(time)
            minutes = int(60 * (time - hours))
        else:
            # discharge
            amount_to_discharge = result['BatteryChargeWatt']
            time = amount_to_discharge / result['AC Power Battery']
            hours = int(time)
            minutes = int(60 * (time - hours))
        if hours > 23:
            result['BatteryChargeTime'] = '∞'
        else:
            result['BatteryChargeTime'] = (
                datetime.now() + timedelta(hours=hours, minutes=minutes)
            ).strftime('%H:%M')
        if result:
            self.save_result_to_file(result)
        self.calculate_sums(result)
        self.calculate_costs(result)
        self.calculate_costs_per_hour(result)
        self.check_windrad(result)
        return result

    def check_windrad(self, result):
        if self.hueclient is None:
            return
        if result['BatteryCharge'] == 100:
            if not self.windrad_running:
                self.hueclient.api.turn_on([9])
                self.windrad_running = True
        elif self.windrad_running:
            self.hueclient.api.turn_off([9])
            self.windrad_running = False

    def run_features(self, emparts):
        # running all enabled features
        for feature in self.smadaemon.featurelist:
            result = feature["feature"].run(
                emparts, feature["config"]
            )
            if result:
                yield result
