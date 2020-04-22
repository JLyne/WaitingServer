import glob
import json
import os
import re
import math

from quarry.types.buffer import Buffer


class World:

    def __init__(self, name: str, environment: dict, folder: str, spawn: str, portals: list):
        self.name = name
        self.time = environment.get('time', 0)
        self.dimension = environment.get('dimension', 'Overworld')
        self.weather = environment.get('weather', 'clear')
        self.cycle = environment.get('cycle', False)

        self.packets = list()
        self.portals = list()
        self.spawn = { "x": 0, "y": 0, "z": 0, "yaw": 0, "yaw_256": 0, "pitch": 0}

        path = os.path.join(os.getcwd(), 'packets', folder, '*.bin')

        for filename in sorted(glob.glob(path)):
            file = open(filename, 'rb')
            packet_type = re.match(r'(\d+)_dn_(\w+)\.bin', os.path.basename(filename))

            self.packets.append({
                "id": packet_type.group(1),
                "type": packet_type.group(2),
                "packet": Buffer(file.read()).read()
            })
            file.close()

        parts = [0, 0, 0, 0, 0]

        for i, part in enumerate(spawn.split(',')):
            parts[i] = part

            self.spawn = {
                "x": float(parts[0]),
                "y": float(parts[1]),
                "z": float(parts[2]),
                "yaw": float(parts[3]),
                "yaw_256": int((float(parts[3]) / 360) * 256),
                "pitch": int(float(parts[4])),
            }

        for portal in portals:
            pos1 = [0, 0, 0]
            pos2 = [0, 0, 0]

            for i, part in enumerate(portal.get('pos1', '').split(',')):
                pos1[i] = math.floor(float(part))

            for i, part in enumerate(portal.get('pos2', '').split(',')):
                pos2[i] = math.floor(float(part))

            self.portals.append({
                "pos1": pos1,
                "pos2": pos2,
                "server": portal.get('server', None)
            })