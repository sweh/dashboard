#!/usr/bin/env python3
# coding=utf-8
from configparser import ConfigParser
from daemon3x import daemon3x
from speedwiredecoder import decode_speedwire
import asyncio
import importlib
import json
import socket
import struct
import sys
import time
import os
import traceback
import websockets.exceptions

parser = ConfigParser()
parser.read(["/etc/smaemd/config", "config"])
try:
    smaemserials = parser.get("SMA-EM", "serials")
except Exception:
    print("Cannot find base config entry SMA-EM serials")
    sys.exit(1)

serials = smaemserials.split(" ")
# smavalues=parser.get('SMA-EM', 'values')
# values=smavalues.split(' ')
pidfile = parser.get("DAEMON", "pidfile")
ipbind = parser.get("DAEMON", "ipbind")
MCAST_GRP = parser.get("DAEMON", "mcastgrp")
MCAST_PORT = int(parser.get("DAEMON", "mcastport"))
features = parser.get("SMA-EM", "features")
features = features.split(" ")
statusdir = ""
try:
    statusdir = parser.get("DAEMON", "statusdir")
except Exception:
    statusdir = "/run/shm/"

if os.path.isdir(statusdir):
    statusfile = statusdir + "em-status"
else:
    statusfile = "em-status"


# Check features and load
featurelist = {}
featurecounter = 0
for feature in features:
    # print ('import ' + feature + '.py')
    featureitem = {}
    featureitem = {"name": feature}
    try:
        featureitem["feature"] = importlib.import_module("features." + feature)
    except (ImportError, FileNotFoundError, TypeError):
        print("feature " + feature + " not found")
        sys.exit()
    try:
        featureitem["config"] = dict(parser.items("FEATURE-" + feature))
        # print (featureitem['config'])
    except Exception:
        print("feature " + feature + " not configured")
        sys.exit()
    try:
        # run config action, if any
        featureitem["feature"].config(featureitem["config"])
    except Exception:
        pass
    featurelist[featurecounter] = featureitem
    featurecounter += 1

# set defaults
if MCAST_GRP == "":
    MCAST_GRP = "239.12.255.254"
if MCAST_PORT == 0:
    MCAST_PORT = 9522


class MyDaemon(daemon3x):

    websockets = None

    def __init__(self, config):
        self.config = ConfigParser()
        self.config.read([config, 'config'])
        try:
            self.smaemserials = self.config.get("SMA-EM", "serials")
        except Exception:
            raise ValueError("Cannot find base config entry SMA-EM serials")
        self.websockets = []
        super(MyDaemon, self).__init__(self.config.get("DAEMON", "pidfile"))

    def register(self, websocket):
        self.websockets.append(websocket)

    async def run(self):
        # prepare listen to socket-Multicast
        socketconnected = False
        while not socketconnected:
            # try:
            sock = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", MCAST_PORT))
            try:
                mreq = struct.pack(
                    "4s4s",
                    socket.inet_aton(MCAST_GRP),
                    socket.inet_aton(ipbind)
                )
                sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_ADD_MEMBERSHIP,
                    mreq
                )
                file = open(statusfile, "w")
                file.write("multicastgroup connected")
                file.close()
                socketconnected = True
            except BaseException:
                print(
                    "could not connect to mulicast group... rest a bit and "
                    "retry"
                )
                file = open(statusfile, "w")
                file.write(
                    "could not connect to mulicast group... rest a bit and "
                    "retry"
                )
                file.close()
                time.sleep(5)
        emparts = {}

        while True:
            # getting sma values
            try:
                # emparts=smaem.readem(sock)
                emparts = decode_speedwire(sock.recv(608))
                for serial in serials:
                    # process only known sma serials
                    if serial == format(emparts["serial"]):
                        # running all enabled features
                        for featurenr in featurelist:
                            result = featurelist[featurenr]["feature"].run(
                                emparts, featurelist[featurenr]["config"]
                            )
                            if result:
                                for websocket in self.websockets:
                                    try:
                                        await websocket.send(
                                            json.dumps(result)
                                        )
                                    except (
                                        websockets.exceptions.
                                        ConnectionClosedOK
                                    ):
                                        self.websockets.remove(websocket)

            except Exception:
                print("Daemon: Exception occured")
                print(traceback.format_exc())
                pass
            await asyncio.sleep(1)


# Daemon - Coding
if __name__ == "__main__":
    daemon = MyDaemon(pidfile)
    if len(sys.argv) == 2:
        if "start" == sys.argv[1]:
            daemon.start()
        elif "stop" == sys.argv[1]:
            for featurenr in featurelist:
                print(">>> stopping " + featurelist[featurenr]["name"])
                featurelist[featurenr]["feature"].stopping(
                    {}, featurelist[featurenr]["config"]
                )
            daemon.stop()
        elif "restart" == sys.argv[1]:
            daemon.restart()
        elif "run" == sys.argv[1]:
            daemon.run()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart|run" % sys.argv[0])
        print(pidfile)
        sys.exit(2)
