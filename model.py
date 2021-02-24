from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import synonym
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON, Float


class BaseModel:

    name_mapping = {}

    def prepare(self, session):
        pass


Base = declarative_base(cls=BaseModel)


class PVSums(Base):
    __tablename__ = 'pvsums'
    name_mapping = {
        'power_from_grid': 'Power from grid',
        'power_to_grid': 'Power to grid',
        'ac_power_solar': 'AC Power Solar',
        'ac_power_battery': 'AC Power Battery',
        'power_from_battery': 'Power from battery',
        'consumption': 'Consumption',
    }

    day = Column(Date, primary_key=True)
    _timestamp = synonym('day')
    consumption = Column(Float)
    ac_power_solar = Column(Float)
    power_to_grid = Column(Float)
    ac_power_battery = Column(Float)
    power_from_battery = Column(Float)
    power_from_grid = Column(Float)


class PVCosts(Base):
    __tablename__ = 'pvcosts'
    name_mapping = {
        'power_from_grid': 'Power from grid',
        'power_to_grid': 'Power to grid',
        'power_saving': 'Power saving',
    }

    day = Column(Date, primary_key=True)
    power_to_grid = Column(Float)
    power_from_grid = Column(Float)
    power_saving = Column(Float)


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

    def _calculate_sub(self, session, db_class):
        sub = (
            session.query(db_class)
            .filter(db_class.day == self._timestamp.date())
            .one_or_none()
        )
        if sub is None:
            sub = db_class()
            sub.day = self._timestamp.date()
        for k, v in sub.name_mapping.items():
            setattr(
                sub,
                k,
                getattr(self, sub.__tablename__.replace('pv', ''))[v]
            )
        return sub

    def prepare(self, session):
        session.add(self._calculate_sub(session, PVCosts))
        session.add(self._calculate_sub(session, PVSums))
