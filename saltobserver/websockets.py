from saltobserver import app, stream
from flask_sockets import Sockets

import gevent
from geventwebsocket.websocket import WebSocketError

sockets = Sockets(app)

@sockets.route('/subscribe')
def subscribe(ws):
    """WebSocket endpoint, used for liveupdates"""
    while ws is not None:
        gevent.sleep(0.1)
        try:
            message = ws.receive() # expect function name to subscribe to
            if message:
                stream.register(ws, message)
        except WebSocketError:
            ws = None
