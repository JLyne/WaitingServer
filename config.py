import logging
import os

import glob

from world import World

import yaml

logger = logging.getLogger('config')
worlds = {
    '1.15': {},
    '1.16': {},
    '1.16.2': {},
    '1.17': {}
}

default_world = {
    '1.15': None,
    '1.16': None,
    '1.16.2': None,
    '1.17': None
}


def load_world_config():
    global default_world
    global worlds

    with open(r'config.yml') as file:
        config = yaml.load(file)
        default = config.get('default-world', None)
        default_exists = {
            '1.15': False,
            '1.16': False,
            '1.16.2': False,
            '1.17': False
        }

        for w in config.get('worlds', list()):
            name = w.get('name', 'Untitled')
            environment = w.get('environment', dict())
            portals = w.get('portals', list())
            folder = w.get('folder')
            bounds = w.get('bounds', None)
            spawn = w.get('spawn', None)

            if folder is None:
                logger.error('World %s has no folder defined. Skipped.', name)
                continue

            folder_path = os.path.join(os.getcwd(), 'packets', folder)

            if os.path.exists(folder_path) is False:
                logger.error('Folder for world %s does not exist. Skipped.', name)
                continue

            for subFolder in glob.glob(os.path.join(folder_path, '*/')):
                version = os.path.basename(os.path.normpath(subFolder))

                if worlds.get(version) is not None:
                    world = World(name, folder, version, environment, bounds, spawn, portals)
                    logger.info('Loaded {} for version {}', world.name, version)

                    if default == world.name:
                        default_exists[version] = True

                    worlds[version][world.name] = world

        for version in worlds:
            if len(worlds[version]) == 0:
                logger.error('No worlds defined for {}'.format(str(version)))
                exit(1)

            if default_exists[version]:
                default_world[version] = worlds[version][default]
            else:
                default_world[version] = next(iter(worlds[version].values()))


def get_worlds():
    return worlds


def get_default_world(version):
    return default_world.get(version, None)
