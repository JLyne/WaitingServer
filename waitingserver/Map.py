import os

from quarry.types.nbt import TagRoot, NBTFile
from typing import List

from waitingserver.direction import Direction


class Map:

	def __init__(self, name: str, version: str, width: int, height: int, starting_id: int):
		self.name = name
		self.width = width
		self.height = height

		self.maps: List[MapPart] = list()

		map_id = starting_id

		for x in range(1, width + 1):
			for y in range(1, height + 1):
				filename = '{}{}{}{}{}.dat'.format(name,
												   '_' if self.width > 1 else '',
												   str(x) if self.width > 1 else '',
												   '_' if self.height > 1 else '',
												   str(y) if self.height > 1 else '')
				path = os.path.join(os.getcwd(), './maps', name, version, filename)

				self.maps.append(MapPart(map_id, NBTFile(TagRoot({})).load(path)))

				map_id += 1

	@staticmethod
	def get_spawn_pos(pos: List[float], direction: Direction, xoffset: int = 0, yoffset: int = 0):
		if direction == Direction.NORTH:
			return [pos[0] + (0.5 - xoffset), pos[1] + (0.5 - yoffset), pos[2] - 0.03125]
		elif direction == Direction.SOUTH:
			return [pos[0] + (0.5 + xoffset), pos[1] + (0.5 - yoffset), pos[2] + 1.03125]
		elif direction == Direction.WEST:
			return [pos[0] - 0.03125, pos[1] + (0.5 - yoffset), pos[2] + (0.5 - xoffset)]
		elif direction == Direction.EAST:
			return [pos[0] + 1.03125, pos[1] + (0.5 - yoffset), pos[2] + (0.5 + xoffset)]
		elif direction == Direction.BOTTOM:
			return [pos[0] + (0.5 + xoffset), pos[1] - 0.03125, pos[2] + (0.5 - yoffset)]
		elif direction == Direction.TOP:
			return [pos[0] + (0.5 + xoffset), pos[1] + 1.03125, pos[2] + (0.5 + yoffset)]


class MapPart:

	def __init__(self, map_id: int, data: NBTFile):
		self.map_id = map_id
		self.data = data.root_tag.body.to_obj().get('data', dict()).get('colors', list())


