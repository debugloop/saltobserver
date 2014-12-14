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

app = Flask(__name__, static_folder='dependencies')
app.config['DEBUG'] = True

app.config['REDIS_HOST'] = 'localhost'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 0
app.config['REDIS_PASS'] = None

redis = Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASS'])
redis.config_set('notify-keyspace-events', 'Kls')

class RedisStream(BaseNamespace, BroadcastMixin):
    def redis_emitter(self, channel, subscription):
        pubsub = Redis().pubsub()
        pubsub.subscribe(subscription)
        for message in pubsub.listen():
            if message['type'] == 'message':
                minion_id = message['channel'].split(':')[1]
                function = message['channel'].split(':')[2]
                jid = redis.lindex('{0}:{1}'.format(minion_id, function), 0)
                timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
                self.emit(channel, dict(minion_id=minion_id, jid=jid, time=time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))

    def on_subscribe_function(self, function):
        redis_channels = ["__keyspace@0__:{0}:{1}".format(minion, function) for minion in redis.smembers('minions')]
        self.spawn(self.redis_emitter, channel='subscribe_function', subscription=redis_channels)

    def on_subscribe_history(self, history):
        self.spawn(self.redis_emitter, channel='subscribe_history', subscription="__keyspace@0__:{0}".format(history))

@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    else:
        return plural

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
        at_time = time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)
    except Exception:
        at_time = None
    return render_template('jobs.html', minions=ret, time=at_time)

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
    functions = list()
    times_list = list()
    for minion in redis.sort('minions', alpha=True):
        try:
            jid = redis.lindex('{0}:{1}'.format(minion, function), 0)
            times_run = redis.llen('{0}:{1}'.format(minion, function))
            if times_run > 0:
                times_list.append(times_run)
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            functions.append((minion, jid, time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
        except Exception:
            continue
    return render_template('functions.html', functions=functions, average_run=float(sum(times_list))/len(times_list) if len(times_list) > 0 else 0)

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
    SocketIOServer(('0.0.0.0', 8000), app, resource="socket.io", policy_server=False).serve_forever()
