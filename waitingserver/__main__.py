import os
import sys
from argparse import ArgumentParser

from quarry.net.server import ServerFactory
from twisted.internet import reactor

from waitingserver.config import load_world_config
from waitingserver.log import logger
from waitingserver.prometheus import init_prometheus
from waitingserver.protocol import Protocol, build_versions

if getattr(sys, 'frozen', False):  # PyInstaller adds this attribute
    # Running in a bundle
    path = os.path.join(sys._MEIPASS, 'waitingserver')
else:
    # Running in normal Python environment
    path = os.path.dirname(__file__)

parser = ArgumentParser()
parser.add_argument("-a", "--host", default="127.0.0.1", help="bind address")
parser.add_argument("-p", "--port", default=25567, type=int, help="bind port")
parser.add_argument("-m", "--max", default=65535, type=int, help="player count")
parser.add_argument("-r", "--metrics", default=None, type=int, help="expose prometheus metrics on specified port")

args = parser.parse_args()

server_factory = ServerFactory()
server_factory.protocol = Protocol
server_factory.max_players = args.max
server_factory.motd = "Waiting Server"
server_factory.online_mode = False
server_factory.compression_threshold = 1500

metrics_port = args.metrics

load_world_config()
build_versions()

if metrics_port is not None:
    init_prometheus(metrics_port)

server_factory.listen(args.host, args.port)
logger.info('Server started')
logger.info("Listening on {}:{}".format(args.host, args.port))
reactor.run()
