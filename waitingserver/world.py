import glob
import os
import re
import math

from quarry.types.buffer import Buffer
from typing import List

from quarry.types.chat import Message

from waitingserver.direction import Direction


class World:

	def __init__(self, name: str, folder: str, version: str, config: dict):
		self.name = name

		environment = config.get('environment', dict())

		self.time = int(environment.get('time', 0))
		self.dimension = "minecraft:{}".format(environment.get('dimension', 'overworld'))
		self.weather = environment.get('weather', 'clear')
		self.music = environment.get('music', 'minecraft:music.end')
		self.cycle = environment.get('cycle', False)
		self.contributors = config.get('contributors', list())

		self.packets: List[WorldPacket] = []
		self.portals: List[WorldPortal] = []
		self.maps: List[WorldMap] = []
		self.holograms: List[WorldStatusHologram] = []
		self.bounds = None
		self.spawn = {"x": 0, "y": 0, "z": 0, "yaw": 0, "yaw_256": 0, "pitch": 0}

		path = os.path.join(os.getcwd(), './packets', folder, version, '*.bin')

		for filename in sorted(glob.glob(path)):
			file = open(filename, 'rb')
			packet_type = re.match(r'(\d+)(?:_dn)?_([a-z_]+)(_[\w-]*)?.bin', os.path.basename(filename))

			self.packets.append(WorldPacket(packet_type.group(1), packet_type.group(2), Buffer(file.read()).read()))
			file.close()

		parts = [0, 0, 0, 0, 0]

		for i, part in enumerate(config.get('spawn').split(',')):
			parts[i] = part

			self.spawn = {
				"x": float(parts[0]),
				"y": float(parts[1]),
				"z": float(parts[2]),
				"yaw": float(parts[3]),
				"yaw_256": int((float(parts[3]) / 360) * 256),
				"pitch": int(float(parts[4])),
			}

		for portal in config.get('portals', list()):
			pos1 = [0, 0, 0]
			pos2 = [0, 0, 0]

			for i, part in enumerate(portal.get('pos1', '').split(',')):
				pos1[i] = math.floor(float(part))

			for i, part in enumerate(portal.get('pos2', '').split(',')):
				pos2[i] = math.floor(float(part))

			self.portals.append(WorldPortal(pos1, pos2, portal.get('server', None)))

		for map in config.get('maps', list()):
			pos = [0, 0, 0]

			for i, part in enumerate(map.get('pos', '').split(',')):
				pos[i] = float(part)

			self.maps.append(WorldMap(map.get('name'), pos, Direction[map.get('direction', 'NORTH').upper()]))

		for hologram in config.get('status-holograms', list()):
			pos = [0.0, 0.0, 0.0]

			for i, part in enumerate(hologram.get('pos', '').split(',')):
				pos[i] = float(part)

			self.holograms.append(WorldStatusHologram(hologram.get('server'), pos))

		if 'bounds' in config:
			bounds = config.get('bounds')
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
			pos1x = min(portal.pos1[0], portal.pos2[0])
			pos1y = min(portal.pos1[1], portal.pos2[1])
			pos1z = min(portal.pos1[2], portal.pos2[2])

			pos2x = max(portal.pos1[0], portal.pos2[0])
			pos2y = max(portal.pos1[1], portal.pos2[1])
			pos2z = max(portal.pos1[2], portal.pos2[2])

			if pos1x <= x <= pos2x and pos1y <= y <= pos2y and pos1z <= z <= pos2z:
				return portal.destination

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

	def credit_component(self):
		if len(self.contributors) > 0:
			return Message({
				"text": "\"" + self.name + "\"\n",
				"italic": True,
				"color": "green",
				"extra": [
					{
						"text": "Created by ",
						"italic": False
					},
					{
						"text": ", ".join(self.contributors[:-1]),
						"italic": False,
						"color": "yellow"
					},
					{
						"text": self.contributors[-1] if len(self.contributors) == 1 else " and " + self.contributors[
							-1],
						"italic": False,
						"color": "yellow"
					}
				]})
		else:
			return Message({
				"text": "\"" + self.name + "\"\n",
				"italic": True,
				"color": "green",
			})


class WorldMap:

	def __init__(self, map_name: str, pos: List[float], direction: Direction):
		self.map_name = map_name
		self.pos = pos
		self.direction = direction


class WorldPortal:

	def __init__(self, pos1: List[int], pos2: List[int], destination: str):
		self.pos1 = pos1
		self.pos2 = pos2
		self.destination = destination


class WorldStatusHologram:

	def __init__(self, server: str, pos: List[float]):
		self.server = server
		self.pos = pos


class WorldPacket:

	def __init__(self, id: int, type: str, data: Buffer):
		self.id = id
		self.type = type
		self.data = data
