from flask import Flask

app = Flask(__name__)
app.config.from_object('saltobserver.config')
try:
    app.config.from_envvar('SALTOBSERVER_SETTINGS')
except RuntimeError:
    print "No custom settings found! Point $SALTOBSERVER_SETTINGS to your configuration file."
    print "You might want to base them on the defaults:"
    print "  wget https://raw.githubusercontent.com/analogbyte/saltobserver/master/saltobserver/config.py"

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

if app.config['USE_LIVEUPDATES']:
    from saltobserver.redis_stream import RedisStream
    try:
        stream = RedisStream()
        stream.start()
    except NotImplementedError:
        app.config['USE_LIVEUPDATES'] = False # override configuration
        app.logger.error("Live updates not available, Redis version not sufficient (minimum is v2.8).")

import saltobserver.filters
import saltobserver.views
if app.config['USE_LIVEUPDATES']:
    import saltobserver.websockets
