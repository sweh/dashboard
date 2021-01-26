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


class MyDaemon(daemon3x):

    websockets = None

    def __init__(self, config):
        self.config = ConfigParser()
        self.config.read([config, 'config'])

        try:
            self.serials = self.config.get("SMA-EM", "serials").split(" ")
        except Exception:
            raise ValueError("Cannot find base config entry SMA-EM serials")

        self.pidfile = self.config.get("DAEMON", "pidfile")
        self.ipbind = self.config.get("DAEMON", "ipbind")
        self.mcast_grp = self.config.get("DAEMON", "mcastgrp")
        self.mcast_port = int(self.config.get("DAEMON", "mcastport"))
        try:
            self.statusdir = self.config.get("DAEMON", "statusdir")
        except Exception:
            self.statusdir = ""

        if os.path.isdir(self.statusdir):
            self.statusfile = os.path.join(self.statusdir, "em-status")
        else:
            self.statusfile = "em-status"

        self.websockets = []

        self.load_features()

        super(MyDaemon, self).__init__(self.pidfile)

    def load_features(self):
        self.featurelist = []
        features = self.config.get("SMA-EM", "features").split(" ")
        for feature in features:
            featureitem = {"name": feature}
            try:
                featureitem["feature"] = importlib.import_module(
                    "features." + feature
                )
            except (ImportError, FileNotFoundError, TypeError):
                print("feature " + feature + " not found")
                continue
            try:
                featureitem["config"] = dict(
                    self.config.items("FEATURE-" + feature)
                )
            except Exception:
                print("feature " + feature + " not configured")
                continue
            try:
                featureitem["feature"].config(featureitem["config"])
            except Exception:
                pass
            self.featurelist.append(featureitem)

    def register(self, websocket):
        self.websockets.append(websocket)

    def connect_to_socket(self):
        # prepare listen to socket-Multicast
        self.socketconnected = False
        while not self.socketconnected:
            # try:
            sock = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(5)
            sock.bind(("", self.mcast_port))
            try:
                mreq = struct.pack(
                    "4s4s",
                    socket.inet_aton(self.mcast_grp),
                    socket.inet_aton(self.ipbind)
                )
                sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_ADD_MEMBERSHIP,
                    mreq
                )
                with open(self.statusfile, "w") as f:
                    f.write("multicastgroup connected")
                self.socketconnected = True
            except BaseException:
                print(
                    "could not connect to mulicast group... rest a bit and "
                    "retry"
                )
                with open(self.statusfile, "w") as f:
                    f.write(
                        "could not connect to mulicast group... rest a bit "
                        "and retry"
                    )
                time.sleep(5)
        return sock

    async def run_features(self, emparts):
        # running all enabled features
        for feature in self.featurelist:
            result = feature["feature"].run(
                emparts, feature["config"]
            )
            if result:
                for websocket in self.websockets:
                    try:
                        await websocket.send(json.dumps(result))
                    except websockets.exceptions.ConnectionClosedOK:
                        self.websockets.remove(websocket)

    async def run(self):
        sock = self.connect_to_socket()

        while True:
            try:
                emparts = decode_speedwire(sock.recv(608))
                for serial in self.serials:
                    if serial == format(emparts["serial"]):
                        await self.run_features(emparts)
            except Exception:
                print("Daemon: Exception occured")
                print(traceback.format_exc())
                pass
            await asyncio.sleep(1)


# Daemon - Coding
if __name__ == "__main__":
    daemon = MyDaemon('/etc/smaemd/config')
    if len(sys.argv) == 2:
        if "start" == sys.argv[1]:
            daemon.start()
        elif "stop" == sys.argv[1]:
            for feature in daemon.featurelist:
                print(">>> stopping " + feature["name"])
                feature["feature"].stopping({}, feature["config"])
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
        print(daemon.pidfile)
        sys.exit(2)
