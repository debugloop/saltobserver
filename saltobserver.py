from flask import Flask, Response
from flask import render_template, redirect, url_for, request, abort

import gevent
from geventwebsocket.websocket import WebSocketError
from flask_sockets import Sockets

import json
import time
from redis import Redis

app = Flask(__name__, static_folder='static')
app.config['DEBUG'] = True

app.config['USE_CDN'] = True
app.config['FUNCTION_QUICKLIST'] = ['state.highstate', 'state.sls', 'pkg.upgrade', 'test.ping']

app.config['REDIS_HOST'] = 'localhost'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 0
app.config['REDIS_PASS'] = None

sockets = Sockets(app)

redis = Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASS'])
redis.config_set('notify-keyspace-events', 'Kls')

class RedisStream(object):
    def __init__(self):
        self.clients = list()
        self.pubsub = Redis().pubsub()
        self.pubsub.psubscribe(["__keyspace@0__:{0}:*.*".format(minion) for minion in redis.smembers('minions')])

    def _generator(self):
        for message in self.pubsub.listen():
            if message['type'] == 'pmessage':
                minion_id = message['channel'].split(':')[1]
                function = message['channel'].split(':')[2]
                jid = redis.lindex('{0}:{1}'.format(minion_id, function), 0)
                timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
                yield dict(minion_id=minion_id, function=function, jid=jid, time=time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp))

    def register(self, client, function):
        self.clients.append((client, function))

    def send_or_discard_connection(self, client_tupl, data):
        client, function = client_tupl
        try:
            client.send(json.dumps(data))
        except Exception:
            self.clients.remove(client_tupl)

    def run(self):
        for data in self._generator():
            for client, function in self.clients:
                if data['function'] == function:
                    gevent.spawn(self.send_or_discard_connection, (client, function), data)

    def start(self):
        gevent.spawn(self.run)

stream = RedisStream()
stream.start()

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
    # TODO: this following line is just for the navigation-bar highlight. make
    # it less ugly?
    function = json.loads(redis.get('{0}:{1}'.format(ret[0], jid)))['fun']
    try:
        timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
        at_time = time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)
    except Exception:
        at_time = None
    return render_template('jobs.html', minions=ret, time=at_time, function=function)

@app.route('/jobs')
def jobsearch():
    if request.args.get('jobid', None):
        return redirect(url_for('jobs', jid=request.args.get('jobid')))
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
    if request.args.get('minionid', None) and request.args.get('function', None):
        return redirect(url_for('history', minion=request.args.get('minionid'), function=request.args.get('function')))
    return render_template('historyform.html')

@app.route('/functions/<function>')
def function(function):
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
    if request.args.get('function', None):
        return redirect(url_for('functions', function=request.args.get('function')))
    return render_template('functionform.html')

@sockets.route('/subscribe_alt')
def outgoing(ws):
    stream.register(ws, "test.ping")
    while ws is not None:
        gevent.sleep()

@sockets.route('/subscribe')
def subscribe(ws):
    while ws is not None:
        gevent.sleep(0.1)
        try:
            message = ws.receive()
        except WebSocketError:
            ws = None
        if message:
            stream.register(ws, message)

@app.route('/')
def functions():
    return redirect(url_for('function', function=request.args.get('function', 'state.highstate')))
