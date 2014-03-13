from flask import Flask, Response
from flask import render_template, redirect, url_for, request, abort

import gevent
from gevent import monkey; monkey.patch_all()

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

import time
from redis import Redis

app = Flask(__name__)
redis = Redis()

class RedisStream(BaseNamespace, BroadcastMixin):
    def redis_emitter(self, channel):
        pubsub = Redis().pubsub()
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message['type'] == 'message':
                self.broadcast_event(channel, message['data'])

    def on_subscribe(self, channel):
        self.spawn(self.redis_emitter, channel=channel)

@app.route('/_get_function_data/<minion>/<jid>')
def get_function_data(minion, jid):
    data = redis.get('{0}:{1}'.format(minion, jid))
    return Response(response=data, status=200, mimetype="application/json")

@app.route('/stats')
def stats():
    highstates = list()
    slss = list()
    pings = list()
    upgrades = list()
    for minion in redis.sort('minions', alpha=True):
        highstates.append((minion, len(redis.lrange('{0}:state.highstate'.format(minion), 0, -1))))
        slss.append((minion, len(redis.lrange('{0}:state.sls'.format(minion), 0, -1))))
        pings.append((minion, len(redis.lrange('{0}:test.ping'.format(minion), 0, -1))))
        upgrades.append((minion, len(redis.lrange('{0}:pkg.upgrade'.format(minion), 0, -1))))
    return render_template('stats.html', highstates=highstates, slss=slss, pings=pings, upgrades=upgrades)

@app.route('/jobs/<jid>')
def jobs(jid):
    if request.args.get('q', None):
        return redirect(url_for('jobs', jid=request.args.get('q')))
    ret = list()
    for minion in redis.keys('*:%s' % jid):
        ret.append(minion.split(':')[0])
    try:
        timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
        return render_template('jobs.html', minions=ret, time=time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp))
    except Exception:
        abort(404)

@app.route('/jobs')
def jobsearch():
    if request.args.get('job', None):
        return redirect(url_for('jobs', jid=request.args.get('job')))
    return render_template('jobform.html')

@app.route('/history/<minion>/<function>')
def history(minion, function):
    ret = list()
    try:
        for jid in redis.lrange('{0}:{1}'.format(minion, function), 0, -1):
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            ret.append((jid, time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
    except Exception:
        pass
    return render_template('history.html', jids=ret)

@app.route('/history')
def historysearch():
    if request.args.get('minion', None) and request.args.get('function', None):
        return redirect(url_for('history', minion=request.args.get('minion'), function=request.args.get('function')))
    return render_template('historyform.html')

@app.route('/functions/<function>')
def function(function):
    if request.args.get('q', None):
        return redirect(url_for('functions', function=request.args.get('q')))
    ret = list()
    for minion in redis.sort('minions', alpha=True):
        try:
            jid = redis.lindex('{0}:{1}'.format(minion, function), 0)
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            ret.append((minion, jid, time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
        except Exception:
            continue
    return render_template('functions.html', functions=ret)

@app.route('/functions')
def functionsearch():
    # get param or
    if request.args.get('function', None):
        return redirect(url_for('functions', function=request.args.get('function')))
    return render_template('functionform.html')

@app.route('/')
def functions():
    # get param or default, but always redirect to function view
    return redirect(url_for('function', function=request.args.get('function', 'state.highstate')))

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    socketio_manage(request.environ, {'/subscription': RedisStream}, request)
    return Response()

if __name__ == '__main__':
    print 'Listening on http://0.0.0.0:8000'
    app.debug = True
    SocketIOServer(('0.0.0.0', 8000), app, resource="socket.io", policy_server=False).serve_forever()
