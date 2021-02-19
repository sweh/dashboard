from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float

Base = declarative_base()


class PV(Base):
    __tablename__ = 'pv'
    name_mapping = {
        'power_from_grid': 'Power from grid',
        'power_to_grid': 'Power to grid',
        'ac_power_solar': 'AC Power Solar',
        'ac_power_battery': 'AC Power Battery',
        'consumption': 'Consumption',
        'battery_charge': 'BatteryCharge',
        'battery_state': 'BatteryState',
        'battery_temp': 'BatteryTemp',
        'status_solar': 'Status Solar',
    }

    __fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    _timestamp = Column('timestamp', DateTime, primary_key=True)
    sums = Column(JSON)
    costs = Column(JSON)
    costs_per_hour = Column(JSON)
    power_from_grid = Column(Float)
    power_to_grid = Column(Float)
    ac_power_solar = Column(Float)
    ac_power_battery = Column(Float)
    consumption = Column(Float)
    battery_charge = Column(Integer)
    battery_state = Column(String)
    battery_temp = Column(Float)
    status_solar = Column(String)

    @property
    def timestamp(self):
        ts = self._timestamp.astimezone(timezone.utc)
        result = datetime.strftime(ts, self.__fmt)
        result = result.replace('000+0000', 'Z')
        return result

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = datetime.strptime(value, self.__fmt)
