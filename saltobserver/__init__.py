from flask import Flask
from flask_sockets import Sockets
app = Flask(__name__)
app.config.from_object('saltobserver.config')

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(app.config['LOG_FILE'])
file_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
    ))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

sockets = Sockets(app)

from saltobserver.redis_stream import RedisStream
stream = RedisStream()
stream.start()

import saltobserver.filters
import saltobserver.views
