from saltobserver import app, stream
from flask.ext.uwsgi_websocket import WebSocket

sockets = WebSocket(app)

@sockets.route('/subscribe')
def subscribe(ws):
    """WebSocket endpoint, used for liveupdates"""
    while ws is not None:
        # gevent.sleep(0.1)
        try:
            message = ws.receive()  # expect function name to subscribe to
            if message:
                stream.register(ws, message)
        except WebSocketError:
            ws = None
