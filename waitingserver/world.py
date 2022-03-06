import glob
import os
import re
import math

from quarry.types.buffer import Buffer


class World:

    def __init__(self, name: str, folder: str, version: str, env: dict, bounds: dict, spawn: str, portals: list):
        self.name = name
        self.time = env.get('time', 0)
        self.dimension = env.get('dimension', 'Overworld')
        self.weather = env.get('weather', 'clear')
        self.music = env.get('music', 'minecraft:music.end')
        self.cycle = env.get('cycle', False)

        self.packets = list()
        self.portals = list()
        self.bounds = None
        self.spawn = {"x": 0, "y": 0, "z": 0, "yaw": 0, "yaw_256": 0, "pitch": 0}

        path = os.path.join(os.getcwd(), './packets', folder, version, '*.bin')

        for filename in sorted(glob.glob(path)):
            file = open(filename, 'rb')
            packet_type = re.match(r'(\d+)(?:_dn)?_([a-z_]+)(_[\w-]*)?.bin', os.path.basename(filename))

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

        if bounds is not None:
            pos1 = [0, 0, 0]
            pos2 = [0, 0, 0]

            for i, part in enumerate(bounds.get('pos1', '').split(',')):
                pos1[i] = math.floor(float(part))

            for i, part in enumerate(bounds.get('pos2', '').split(',')):
                pos2[i] = math.floor(float(part))

            self.bounds = {
                "pos1": pos1,
                "pos2": pos2,
            }

    def get_portal_at(self, x, y, z):
        x = math.floor(x)
        y = math.floor(y)
        z = math.floor(z)

        for portal in self.portals:
            pos1x = min(portal['pos1'][0], portal['pos2'][0])
            pos1y = min(portal['pos1'][1], portal['pos2'][1])
            pos1z = min(portal['pos1'][2], portal['pos2'][2])

            pos2x = max(portal['pos1'][0], portal['pos2'][0])
            pos2y = max(portal['pos1'][1], portal['pos2'][1])
            pos2z = max(portal['pos1'][2], portal['pos2'][2])

            if pos1x <= x <= pos2x and pos1y <= y <= pos2y and pos1z <= z <= pos2z:
                return portal['server']

        return None

    def is_within_bounds(self, x, y, z):
        x = math.floor(x)
        y = math.floor(y)
        z = math.floor(z)

        if self.bounds is None:
            return True

        pos1x = min(self.bounds['pos1'][0], self.bounds['pos2'][0])
        pos1y = min(self.bounds['pos1'][1], self.bounds['pos2'][1])
        pos1z = min(self.bounds['pos1'][2], self.bounds['pos2'][2])

        pos2x = max(self.bounds['pos1'][0], self.bounds['pos2'][0])
        pos2y = max(self.bounds['pos1'][1], self.bounds['pos2'][1])
        pos2z = max(self.bounds['pos1'][2], self.bounds['pos2'][2])

        return pos1x <= x <= pos2x and pos1y <= y <= pos2y and pos1z <= z <= pos2z
