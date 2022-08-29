"""
    Get inverter pv values via modbus

    2018-12-28 Tommi2Day
    2020-09-22 Tommi2Day fixes empty data exeptions
    2021-01-02 sellth added support for multiple inverters

    Configuration:
    pip3 install pymodbus

    [FEATURE-pvdata]

    # How frequently to send updates over (defaults to 20 sec)
    min_update=20
    #debug output
    debug=0

    #inverter connection
    inv_host = <inverter ip>
    inv_port = 502
    inv_modbus_id = 3
    inv_manufacturer = SMA
    #['address', 'type', 'format', 'description', 'unit', 'value']
    registers = [
        ['30057', 'U32', 'RAW', 'serial', ''],
        ['30201','U32','ENUM','Status',''],
        ['30051','U32','ENUM','DeviceClass',''],
        ['30053','U32','ENUM','DeviceID',''],
        ['40631', 'STR32', 'UTF8', 'Device Name', ''],
        ['30775', 'S32', 'FIX0', 'AC Power', 'W'],
        ['30813', 'S32', 'FIX0', 'AC apparent power', 'VA'],
        ['30977', 'S32', 'FIX3', 'AC current', 'A'],
        ['30783', 'S32', 'FIX2', 'AC voltage', 'V'],
        ['30803', 'U32', 'FIX2', 'grid frequency', 'Hz'],
        ['30773', 'S32', 'FIX0', 'DC power', 'W'],
        ['30771', 'S32', 'FIX2', 'DC input voltage', 'V'],
        ['30777', 'S32', 'FIX0', 'Power L1', 'W'],
        ['30779', 'S32', 'FIX0', 'Power L2', 'W'],
        ['30781', 'S32', 'FIX0', 'Power L3', 'W'],
        ['30953', 'S32', 'FIX1', u'device temperature', u'\xb0C'],
        ['30517', 'U64', 'FIX3', 'daily yield', 'kWh'],
        ['30513', 'U64', 'FIX3', 'total yield', 'kWh'],
        ['30521', 'U64', 'FIX0', 'operation time', 's'],
        ['30525', 'U64', 'FIX0', 'feed-in time', 's'],
        ['30975', 'S32', 'FIX2', 'intermediate voltage', 'V'],
        ['30225', 'S32', 'FIX0', 'Isolation resistance', u'\u03a9'],
        ['30581', 'U32', 'FIX0', u'energy from grid', 'Wh'],
        ['30583', 'U32', 'FIX0', u'energy to grid', 'Wh'],
        ['30865', 'S32', 'FIX0', 'Power from grid', 'W'],
        ['30867', 'S32', 'FIX0', 'Power to grid', 'W']
    ]
"""

import asyncio
import datetime
import time
import os
from features.smamodbus import get_device_class
from features.smamodbus import get_pv_data

pv_last_update = 0
pv_debug = 0
pv_data = []


def run(emparts, config):
    global pv_debug
    global pv_last_update
    global pv_data

    # Only update every X seconds
    if time.time() < pv_last_update + int(config.get('min_update', 20)):
        if (pv_debug > 1):
            print("pv: data skipping")
        return

    pv_last_update = time.time()
    registers = eval(config.get('registers'))

    pv_data = []
    for inv in eval(config.get('inverters')):
        host, port, modbusid, manufacturer = inv
        device_class = get_device_class(host, int(port), int(modbusid))
        if device_class == "Solar Inverter":
            relevant_registers = eval(config.get('registers'))
        elif device_class == "Battery Inverter":
            relevant_registers = eval(config.get('registers_batt'))
        else:
            if (pv_debug > 1):
                print("pv: unknown device class; skipping")
            pass

        mdata = get_pv_data(host, int(port), int(modbusid), relevant_registers)
        pv_data.append(mdata)

    # query
    if pv_data is None:
        if pv_debug > 0:
            print("PV: no data")
        return

    timestamp = datetime.datetime.utcnow().isoformat(
        timespec='milliseconds'
    ) + 'Z'
    result = []
    for i in pv_data:
        if i is None:
            continue
        i['timestamp'] = timestamp
        if pv_debug > 0:
            print("PV:" + format(i))
        result.append(i)
    return result


def stopping(emparts, config):
    pass


def on_publish(client, userdata, result):
    pass


def config(config):
    global pv_debug
    pv_debug = int(config.get('debug', 0))
    print('pvdata: feature enabled')
