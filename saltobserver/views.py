from saltobserver import app, sockets, stream
import gevent
from geventwebsocket.websocket import WebSocketError

from flask import Response
from flask import render_template, redirect, url_for, request

import json
import time

from redis import Redis
redis = Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASS'])

@app.route('/_get_function_data/<minion>/<jid>')
def get_function_data(minion, jid):
    """AJAX access for loading function/job details."""
    data = redis.get('{0}:{1}'.format(minion, jid))
    return Response(response=data, status=200, mimetype="application/json")

@app.route('/jobs/<jid>')
def jobs(jid):
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

@app.route('/')
def functions():
    return redirect(url_for('function', function=request.args.get('function', app.config['DEFAULT_FUNCTION'])))
