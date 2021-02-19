from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON, Float


class BaseModel:

    name_mapping = {}

    def prepare(self, session):
        pass


Base = declarative_base(cls=BaseModel)


class PVCosts(Base):
    __tablename__ = 'pvcosts'
    name_mapping = {
        'power_from_grid': 'Power from grid',
        'power_to_grid': 'Power to grid',
        'ac_power_solar': 'AC Power Solar',
        'ac_power_battery': 'AC Power Battery',
        'consumption': 'Consumption',
    }

    day = Column(Date, primary_key=True)
    consumption = Column(Float)
    ac_power_solar = Column(Float)
    power_to_grid = Column(Float)
    ac_power_battery = Column(Float)
    power_from_grid = Column(Float)


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
    _timestamp = Column('timestamp', DateTime(timezone=True), primary_key=True)
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

    def prepare(self, session):
        costs = (
            session.query(PVCosts)
            .filter(PVCosts.day == self._timestamp.date())
            .one_or_none()
        )
        if costs is None:
            costs = PVCosts()
            costs.day = self._timestamp.date()
        for k, v in costs.name_mapping.items():
            setattr(costs, k, getattr(self, k))
        session.add(costs)
