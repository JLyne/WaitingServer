import logging
import os

from world import World

import yaml

logger = logging.getLogger('config')
worlds = dict()
default_world = None

def load_world_config():
    global default_world
    global worlds

    with open(r'config.yml') as file:
        config = yaml.load(file)
        default = config.get('default-world', None)
        default_exists = False

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

            world = World(name, folder, environment, bounds, spawn, portals)
            logger.info('Loaded {}', world.name)

            if default == world.name:
                default_exists = True

            worlds[world.name] = world

        if len(worlds) == 0:
            logging.getLogger('main').error("No worlds defined.")
            exit(1)

        if default_exists:
            default_world = worlds[default]
        else:
            default_world = next(iter(worlds.values()))

def get_worlds():
    return worlds

def get_default_world():
    return default_world