from flask import Flask
from flask_sockets import Sockets
app = Flask(__name__)
app.config.from_object('saltobserver.config')

sockets = Sockets(app)

from saltobserver.redis_stream import RedisStream
stream = RedisStream()
stream.start()

import saltobserver.filters
import saltobserver.views
