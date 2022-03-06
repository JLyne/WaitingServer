import logging
import os

import glob

from yaml import SafeLoader

from waitingserver.world import World
from waitingserver.log import file_handler, console_handler
import yaml

logger = logging.getLogger('config')
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

worlds = {}
default_world = {}


def load_world_config():
    global default_world
    global worlds

    with open(r'./config.yml') as file:
        config = yaml.load(file, Loader=SafeLoader)
        default = config.get('default-world', None)

        for w in config.get('worlds', list()):
            name = w.get('name', 'Untitled')
            contributors = w.get('contributors', list())
            environment = w.get('environment', dict())
            portals = w.get('portals', list())
            folder = w.get('folder')
            bounds = w.get('bounds', None)
            spawn = w.get('spawn', None)

            if folder is None:
                logger.error('World %s has no folder defined. Skipped.', name)
                continue

            folder_path = os.path.join(os.getcwd(), './packets', folder)

            if os.path.exists(folder_path) is False:
                logger.error('Folder for world %s does not exist. Skipped.', name)
                continue

            for subFolder in glob.glob(os.path.join(folder_path, '*/')):
                version = os.path.basename(os.path.normpath(subFolder))

                if worlds.get(version) is None:
                    worlds[version] = []

                world = World(name, folder, version, contributors, environment, bounds, spawn, portals)
                logger.info('Loaded {} for version {}'.format(world.name, version))

                if default == world.name:
                    default_world[version] = world

                worlds[version].append(world)

        for version in worlds:
            if len(worlds[version]) == 0:
                logger.error('No worlds defined for {}'.format(str(version)))
                exit(1)

            if default_world.get(version) is None:
                default_world[version] = worlds[version][0]


def get_worlds():
    return worlds


def get_default_world(version):
    return default_world.get(version, None)
